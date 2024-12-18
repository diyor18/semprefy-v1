from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter, UploadFile, File, Query
from ..database import engine, get_db
import psycopg2
from .. import models, schemas, utils, oauth2
from sqlalchemy.orm import Session, joinedload, aliased
from pydantic import BaseModel, EmailStr
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
def create_business(
    business: schemas.BusinessCreate = Depends(), 
    file: UploadFile = File(None), 
    db: Session = Depends(get_db)
):
    
    
    existing_business = db.query(models.Business).filter(models.Business.email == business.email).first()
    if existing_business:
        raise HTTPException(
            status_code=400, 
            detail="A business with this email already exists."
        )
    # Validate required fields
    if business.country == "null":
        business.country = None
        
    if business.city == "null":
        business.city = None
        
    missing_fields = []
    if not business.email:
        missing_fields.append("email")
    if not business.name:
        missing_fields.append("name")
    if not business.password:
        missing_fields.append("password")
    if not business.phone:
        missing_fields.append("phone")
    if not business.description:
        missing_fields.append("description")
    if not business.country:
        missing_fields.append("country")
    if not business.city:
        missing_fields.append("city")
    if not business.address:
        missing_fields.append("address")
    if not business.bank_account:
        missing_fields.append("bank_account")
    if not business.bank_account_name:
        missing_fields.append("bank_account_name")
    if not business.bank_name:
        missing_fields.append("bank_name")
    
    if missing_fields:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Incorrect Data: Missing {', '.join(missing_fields)}"
        )
    
    # Validate email format
    if not isinstance(business.email, str) or "@" not in business.email:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Incorrect Data: Invalid email format"
        )
    
    # Validate file type (if file is uploaded)
    if file and file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Incorrect Data: Wrong type of image. Only jpg and png are allowed."
        )
    
    # Hash the password
    hashed_password = utils.hash(business.password)
    business.password = hashed_password
    
    # Upload the image to S3 and get the URL
    profile_image = utils.upload_image_to_s3(file) if file else None
    
    # Create a new business record with the image URL
    new_business = models.Business(**business.dict(), profile_image=profile_image)
    db.add(new_business)
    db.commit()
    db.refresh(new_business)
    
    return new_business

@router.patch("/current/update", response_model=schemas.BusinessBase)
def update_current_business(
    email: Optional[EmailStr] = None,
    name: Optional[str] = None,
    phone: Optional[str] = None,
    description: Optional[str] = None,
    country: Optional[str] = None,
    city: Optional[str] = None,
    address: Optional[str] = None,
    bank_account: Optional[str] = None,
    bank_account_name: Optional[str] = None,
    bank_name: Optional[str] = None,
    profile_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_business: models.Business = Depends(oauth2.get_current_business),
):
    # Fetch the current business from the database
    business = db.query(models.Business).filter(models.Business.business_id == current_business.business_id).first()
    
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Business with ID {current_business.business_id} does not exist"
        )

    # Update fields if provided
    if email:
        business.email = email
    if name:
        business.name = name
    if phone:
        business.phone = phone
    if description:
        business.description = description
    if country:
        business.country = country
    if city:
        business.city = city
    if address:
        business.address = address
    if bank_account:
        business.bank_account = bank_account
    if bank_account_name:
        business.bank_account_name = bank_account_name
    if bank_name:
        business.bank_name = bank_name

    # Handle profile image upload
    if profile_image:
        try:
            business.profile_image = utils.upload_image_to_s3(profile_image)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Failed to upload profile image: {str(e)}"
            )

    # Commit updates to the database
    db.commit()
    db.refresh(business)

    return business


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
        return []

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

    return service_data if service_data else []


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

        # Calculate the total amount of transactions linked to the current business's services on this day
        total_transaction_amount = (
            db.query(func.sum(models.Transaction.amount))
            .join(models.Subscription, models.Subscription.subscription_id == models.Transaction.subscription_id)
            .join(models.Service, models.Service.service_id == models.Subscription.service_id)
            .filter(
                models.Service.business_id == business_id,
                func.date(models.Transaction.created_at) == single_date
            )
            .scalar() or 0.0
        )

        # Append the day's data to the response
        graph_data.append({
            "day": day_int,  # Use the integer day
            "new_users": new_users_count,
            "total_transaction_amount": total_transaction_amount
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
            models.Service.name.label("service_name")
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
            "status": payout.status
        }
        for payout in payouts
    ]

    return formatted_payouts if formatted_payouts else []




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
    
    return subscriptions if subscriptions else []