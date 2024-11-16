from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from ..database import engine, get_db
import psycopg2
from .. import models, schemas, utils, oauth2
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from . import auth
from sqlalchemy.sql import func

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
    
    new_subscription = models.Subscription(service_id = service.service_id, user_id = current_user.user_id)
    db.add(new_subscription)
    db.commit()
    return{"message":"successfully added subscription"}

#GET MY SUBSCRIPTIONS
@router.get("/my_subscriptions", response_model=List[schemas.Subscription])
def get_my_subscriptions(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    subscriptions = db.query(models.Subscription).filter(models.Subscription.user_id == current_user.user_id).all()
    
    if not subscriptions:
        raise HTTPException(status_code=404, detail="You don't have any subscriptions")
    
    return subscriptions

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