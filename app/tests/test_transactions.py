import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app import models
from app.oauth2 import create_access_token
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import random
import string

client = TestClient(app)

def random_email():
    return f"user_{''.join(random.choices(string.ascii_lowercase, k=5))}@example.com"

@pytest.fixture
def setup_data():
    db = next(get_db())

    user = models.User(
        email=random_email(),
        name="Test User",
        password="hashedpassword"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    business = models.Business(
        email=f"business_{random_email()}",
        name="Test Business",
        password="hashedpassword",
        phone="1234567890",
        description="A test business",
        country="Testland",
        city="Test City",
        address="123 Test St.",
        bank_account="12345678",
        bank_account_name="Test Account",
        bank_name="Test Bank",
    )
    db.add(business)
    db.commit()
    db.refresh(business)

    # Create a test service
    service = models.Service(
        name="Test Service",
        description="A service for testing",
        price=100.0,
        duration=30,
        business_id=business.business_id,
        status="active"
    )
    db.add(service)
    db.commit()
    db.refresh(service)

    card = models.Card(
        user_id=user.user_id,
        card_number="4111 1111 1111 1111",
        card_expiry="12/30",
        card_brand="Visa"
    )
    db.add(card)
    db.commit()
    db.refresh(card)

    subscription_date = datetime.utcnow()
    expiry_date = subscription_date + timedelta(days=30)
    subscription = models.Subscription(
        service_id=service.service_id,
        user_id=user.user_id,
        subscription_date=subscription_date,
        expiry_date=expiry_date,
        status="active",
        days_till_next_payment=5
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    return {
        "user_id": user.user_id,
        "business_id": business.business_id,
        "service_id": service.service_id,
        "subscription_id": subscription.subscription_id,
    }

def test_transaction_processing_pending(setup_data):
    db = next(get_db())
    subscription_id = setup_data["subscription_id"]

    subscription = db.query(models.Subscription).filter(models.Subscription.subscription_id == subscription_id).first()

    from app.routers.transaction import process_transactions
    process_transactions(db)

    transaction = db.query(models.Transaction).filter(
        models.Transaction.subscription_id == subscription.subscription_id,
        models.Transaction.status == "Pending"
    ).first()
    assert transaction is not None, "Expected a pending transaction to be created"
    assert transaction.amount == subscription.service.price
    assert transaction.card_brand == "Visa"

def test_transaction_processing_complete(setup_data):
    db = next(get_db())
    subscription_id = setup_data["subscription_id"]

    subscription = db.query(models.Subscription).filter(models.Subscription.subscription_id == subscription_id).first()
    subscription.days_till_next_payment = 0
    db.commit()

    user_card = db.query(models.Card).filter(models.Card.user_id == subscription.user_id).first()

    transaction = models.Transaction(
        amount=subscription.service.price,
        status="Pending",
        subscription_id=subscription.subscription_id,
        card_brand=user_card.card_brand
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    from app.routers.transaction import process_transactions
    process_transactions(db)

    completed_transaction = db.query(models.Transaction).filter(
        models.Transaction.subscription_id == subscription.subscription_id,
        models.Transaction.status == "Complete"
    ).first()

    assert completed_transaction is not None, "Expected a transaction to be marked as complete"
    assert completed_transaction.created_at.date() == datetime.utcnow().date()
