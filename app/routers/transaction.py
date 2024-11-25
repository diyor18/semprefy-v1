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
    prefix = "/transactions",
    tags=["Transactions"]
)

#
#GET MY SUBSCRIPTIONS
@router.get("/my_transactions", response_model=List[schemas.Transaction])
def get_my_transactions(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    
    process_transactions(db)
    transactions = (
        db.query(models.Transaction)
        .join(models.Subscription, models.Transaction.subscription_id == models.Subscription.subscription_id)
        .filter(models.Subscription.user_id == current_user.user_id)
        .all()
    )

    if not transactions:
        raise HTTPException(status_code=404, detail="No transactions found")
    
    return transactions if transactions else []





def process_transactions(db: Session):
    subscriptions = db.query(models.Subscription).all()

    for subscription in subscriptions:
        user_card = db.query(models.Card).filter(models.Card.user_id == subscription.user_id).first()
        # Check if `days_till_next_payment` is 5
        if subscription.days_till_next_payment == 5:
            # Check if a pending transaction already exists for this subscription
            existing_transaction = (
                db.query(models.Transaction)
                .filter(
                    models.Transaction.subscription_id == subscription.subscription_id,
                    models.Transaction.status == "pending"
                )
                .first()
            )
            if not existing_transaction:
                # Create a new pending transaction
                new_transaction = models.Transaction(
                    amount=subscription.service.price,
                    status="pending",
                    subscription_id=subscription.subscription_id,
                    card_brand=user_card.card_brand 
                )
                db.add(new_transaction)
        
        # Check if `days_till_next_payment` is 0
        elif subscription.days_till_next_payment == 0:
            # Update the status of any pending transaction to "complete"
            transaction = (
                db.query(models.Transaction)
                .filter(
                    models.Transaction.subscription_id == subscription.subscription_id,
                    models.Transaction.status == "Pending"
                )
                .first()
            )
            if transaction:
                transaction.status = "Complete"
                transaction.created_at = datetime.utcnow()

    db.commit()