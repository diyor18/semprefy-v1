from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter, UploadFile, File, Query
from ..database import engine, get_db
import psycopg2
from .. import models, schemas, utils, oauth2
from sqlalchemy.orm import Session, joinedload, aliased
from pydantic import BaseModel
from typing import List, Optional
from ..config import settings
from sqlalchemy.sql import func, extract
from datetime import date, datetime, timedelta
from sqlalchemy import desc



router = APIRouter(
    prefix = "/businesses",
    tags=["Businesses"]
)

#CREATE A BUSINESS
@router.post("/create", response_model=schemas.BusinessOut)
def create_business(business: schemas.BusinessCreate = Depends(), file: UploadFile = File(None), db: Session = Depends(get_db)):
    #HASHING THE PASSWORD
    hashed_password = utils.hash(business.password)
    business.password = hashed_password
    
    # Upload the image to S3 and get the URL
    profile_image = utils.upload_image_to_s3(file) if file else None
    
    new_business = models.Business(**business.dict(), profile_image = profile_image)
    db.add(new_business)
    db.commit()
    db.refresh(new_business)
    
    return new_business

#GET CURRENT BUSINESS
@router.get("/current", response_model=schemas.BusinessOut)
def get_current_business(db: Session = Depends(get_db), current_business: int = Depends(oauth2.get_current_business)):
    business = db.query(models.Business).filter(models.Business.business_id == current_business.business_id).first()
    
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Business with id: {current_business.business_id} does not exist")
    
    return business

#GET BUSINESS BY ID
@router.get("/id/{id}", response_model=schemas.BusinessOut)
def get_business(id: int, db: Session = Depends(get_db)):
    business = db.query(models.Business).filter(models.Business.business_id == id).first()
    
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Business with id: {id} does not exist")
    
    return business


@router.get("/current/metrics")
def get_business_metrics(
    db: Session = Depends(get_db), 
    current_business: int = Depends(oauth2.get_current_business)
):
    business_id = current_business.business_id

    # 1. MRR (Monthly Recurring Revenue)
    mrr = (
        db.query(func.sum(models.Service.price))
        .join(models.Subscription, models.Service.service_id == models.Subscription.service_id)
        .filter(
            models.Service.business_id == business_id,
            models.Subscription.status == "active"  # Filter for active subscriptions
        )
        .scalar() or 0
    )

    # 2. Active Users
    active_users = (
        db.query(func.count(models.Subscription.user_id.distinct()))
        .join(models.Service, models.Service.service_id == models.Subscription.service_id)
        .filter(
            models.Service.business_id == business_id,
            models.Subscription.status == "active"
        )
        .scalar() or 0
    )

    # 3. New Users (this calendar month)
    current_date = date.today()
    new_users = (
        db.query(func.count(models.Subscription.user_id.distinct()))
        .join(models.Service, models.Service.service_id == models.Subscription.service_id)
        .filter(
            models.Service.business_id == business_id,
            models.Subscription.status == "active",
            extract("year", models.Subscription.subscription_date) == current_date.year,
            extract("month", models.Subscription.subscription_date) == current_date.month
        )
        .scalar() or 0
    )

    # 4. Service Count
    service_count = (
        db.query(func.count(models.Service.service_id))
        .filter(models.Service.business_id == business_id)
        .scalar() or 0
    )

    # Response
    return {
        "MRR": mrr,
        "active_users": active_users,
        "new_users": new_users,
        "service_count": service_count
    }
    
    
@router.get("/current/services")
def get_current_business_services(
    db: Session = Depends(get_db),
    current_business: int = Depends(oauth2.get_current_business),
):
    # Query the services for the current business
    services = db.query(models.Service).filter(
        models.Service.business_id == current_business.business_id
    ).all()

    if not services:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No services found for the current business."
        )

    service_data = []
    for service in services:
        # Calculate MRR for the service
        mrr = (
            db.query(func.sum(models.Service.price))
            .join(models.Subscription, models.Service.service_id == models.Subscription.service_id)
            .filter(
                models.Service.service_id == service.service_id,
                models.Subscription.status == "active"
            )
            .scalar() or 0
        )

        # Calculate active users for the service
        active_users = (
            db.query(func.count(models.Subscription.user_id.distinct()))
            .filter(
                models.Subscription.service_id == service.service_id,
                models.Subscription.status == "active"
            )
            .scalar() or 0
        )

        # Attach metrics to the service dictionary
        service_dict = schemas.ServiceOut.from_orm(service).dict()
        service_dict.update({"mrr": mrr, "active_users": active_users})

        service_data.append(service_dict)

    return service_data


@router.get("/current/graph-data")
def get_current_business_graph_data(
    db: Session = Depends(get_db), 
    current_business: int = Depends(oauth2.get_current_business)
):
    business_id = current_business.business_id

    # Get the first and last days of the current month
    today = date.today()
    start_of_month = today.replace(day=1)

    # Prepare the response structure
    graph_data = []
    
    # Iterate over each day in the current month up to today
    for single_date in (start_of_month + timedelta(days=i) for i in range((today - start_of_month).days + 1)):
        day_int = int(single_date.strftime("%d"))  # Extract the day and convert it to an integer
        
        # Count new users who created subscriptions with services owned by the current business on this day
        new_users_count = (
            db.query(func.count(models.Subscription.user_id.distinct()))
            .join(models.Service, models.Service.service_id == models.Subscription.service_id)
            .filter(
                models.Service.business_id == business_id,
                func.date(models.Subscription.subscription_date) == single_date
            )
            .scalar() or 0
        )

        # Count transactions linked to the current business's services on this day
        transactions_count = (
            db.query(func.count(models.Transaction.transaction_id))
            .join(models.Subscription, models.Subscription.subscription_id == models.Transaction.subscription_id)
            .join(models.Service, models.Service.service_id == models.Subscription.service_id)
            .filter(
                models.Service.business_id == business_id,
                func.date(models.Transaction.created_at) == single_date
            )
            .scalar() or 0
        )

        # Append the day's data to the response
        graph_data.append({
            "day": day_int,  # Use the integer day
            "new_users": new_users_count,
            "transactions": transactions_count
        })

    return {"graph_data": graph_data}




@router.get("/current/payouts")
def get_current_business_payouts(
    db: Session = Depends(get_db),
    current_business: int = Depends(oauth2.get_current_business)
):
    business_id = current_business.business_id

    # Query transactions for the current business, ordered by created_at descending
    payouts = (
        db.query(
            models.Transaction.transaction_id,
            models.Transaction.amount,
            models.Transaction.created_at,
            models.Transaction.status,
            models.Subscription.user_id,
            models.Service.name.label("service_name"),
            models.Service.service_image.label("service_image")
        )
        .join(models.Subscription, models.Transaction.subscription_id == models.Subscription.subscription_id)
        .join(models.Service, models.Service.service_id == models.Subscription.service_id)
        .filter(models.Service.business_id == business_id)
        .order_by(desc(models.Transaction.created_at))  # Sort by created_at descending
        .all()
    )

    # Format the result
    formatted_payouts = [
        {
            "transaction_id": payout.transaction_id,
            "user_id": payout.user_id,
            "amount": payout.amount,
            "service": payout.service_name,
            "created_date": payout.created_at.strftime("%d/%m/%Y"),
            "status": payout.status,
            "service_image": payout.service_image 
        }
        for payout in payouts
    ]

    return formatted_payouts




@router.get("/current/users", response_model=List[schemas.UserSubscriptionOut])
def get_users_with_subscriptions(
    current_business: models.Business = Depends(oauth2.get_current_business),
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description="Search by user name")
):
    # Base query to fetch subscriptions
    query = (
        db.query(
            models.Subscription.subscription_id,
            models.User.name.label("user_name"),
            models.User.email,
            models.User.profile_image,
            models.Service.name.label("service_name"),
            models.Subscription.subscription_date,
            models.Subscription.expiry_date,
            models.Service.price
        )
        .join(models.Service, models.Subscription.service_id == models.Service.service_id)
        .join(models.User, models.Subscription.user_id == models.User.user_id)
        .filter(models.Service.business_id == current_business.business_id)
    )
    
    # Apply search filter if 'search' parameter is provided
    if search:
        query = query.filter(models.User.name.ilike(f"%{search}%"))
    
    # Execute query and fetch results
    subscriptions = query.all()
    
    return subscriptions