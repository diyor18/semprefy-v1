from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from ..database import engine, get_db
import psycopg2
from .. import models, schemas, utils, oauth2
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from . import auth
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from pytz import UTC


router = APIRouter(
    prefix = "/subscriptions",
    tags=["Subscriptions"]
)

#CREATE SUBSCRIPTION
@router.post("/create/{service_id}", status_code=status.HTTP_201_CREATED)
def create_subscription(service_id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    service = db.query(models.Service).filter(models.Service.service_id == service_id).first()
    
    if not current_user:
        raise HTTPException(status_code=404, detail="User not authorized")
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    existing_subscription = db.query(models.Subscription).filter(models.Subscription.user_id == current_user.user_id, models.Subscription.service_id == service.service_id).first()

    if existing_subscription:
        raise HTTPException(status_code=400, detail="Subscription already exists")
    
    # Retrieve user's card details (assuming the user's card is stored in a 'User' or 'Card' model)
    user_card = db.query(models.Card).filter(models.Card.user_id == current_user.user_id).first()
    
    if not user_card:
        raise HTTPException(status_code=400, detail="User does not have a card associated")
    
    # Calculate expiry date
    subscription_date = datetime.utcnow()
    expiry_date = subscription_date + relativedelta(months=service.duration)
    
    # Calculate `days_till_next_payment`
    next_payment_date = subscription_date + timedelta(days=30)  # Payments occur every 30 days
    days_till_next_payment = (next_payment_date - subscription_date).days
    
    # Create a new subscription
    new_subscription = models.Subscription(
        service_id=service.service_id,
        user_id=current_user.user_id,
        subscription_date=subscription_date,
        expiry_date=expiry_date,
        status="active",
        days_till_next_payment=days_till_next_payment
    )
    db.add(new_subscription)
    db.commit()
    db.refresh(new_subscription)  # Refresh to get the full object including autogenerated fields
    
    first_transaction = models.Transaction(
        amount=service.price,
        status="Complete",  # Initial transaction is marked as complete
        subscription_id=new_subscription.subscription_id,
        created_at=subscription_date,  # Use the subscription creation date
        card_brand=user_card.card_brand  # Assign the user's card brand
    )
    db.add(first_transaction)
    db.commit()

    return {"message": "Successfully added subscription", "subscription_id": new_subscription.subscription_id}

#GET MY SUBSCRIPTIONS
@router.get("/my_subscriptions", response_model=List[schemas.Subscription])
def get_my_subscriptions(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    subscriptions = db.query(models.Subscription).filter(models.Subscription.user_id == current_user.user_id).all()
    
    if not subscriptions:
        raise HTTPException(status_code=404, detail="You don't have any subscriptions")
    
    for subscription in subscriptions:
        update_days_till_next_payment(subscription)
        db.commit()  # Save updated days_till_next_payment
    
    return subscriptions if subscriptions else []

@router.get("/my_subscriptions_amount", response_model=dict)
def get_my_subscriptions_amount(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    
    total_amount = (
        db.query(func.sum(models.Service.price))
        .join(models.Subscription, models.Service.service_id == models.Subscription.service_id)
        .filter(models.Subscription.user_id == current_user.user_id)
        .filter(models.Subscription.status == 'active')  # Adjust this condition as needed
        .scalar()
    )

    if total_amount is None:
        total_amount = 0  # Default to 0 if no subscriptions are found

    return {"monthly_payable": total_amount}




def update_days_till_next_payment(subscription: models.Subscription):
    # Ensure both dates are offset-aware
    today = datetime.utcnow().replace(tzinfo=UTC)
    subscription_date = subscription.subscription_date

    if subscription_date.tzinfo is None:
        subscription_date = subscription_date.replace(tzinfo=UTC)

    next_payment_date = subscription_date + timedelta(days=30)

    # If the next payment date has passed, calculate the next cycle
    while next_payment_date < today:
        next_payment_date += timedelta(days=30)
    
    subscription.days_till_next_payment = (next_payment_date - today).days
    
    
    
@router.delete("/cleanup", status_code=status.HTTP_204_NO_CONTENT)
def delete_expired_subscriptions(
    db: Session = Depends(get_db),
):
    # Get the current date
    current_date = datetime.utcnow().date()

    # Query for expired subscriptions belonging to the current business
    expired_subscriptions_query = (
        db.query(models.Subscription)
        .join(models.Service, models.Subscription.service_id == models.Service.service_id)
        .filter(
            models.Subscription.expiry_date < current_date
        )
    )

    expired_subscriptions = expired_subscriptions_query.all()

    if not expired_subscriptions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No expired subscriptions found for deletion"
        )

    # Delete all expired subscriptions
    expired_subscriptions_query.delete(synchronize_session=False)
    db.commit()

    return {"message": f"{len(expired_subscriptions)} expired subscriptions have been deleted"}