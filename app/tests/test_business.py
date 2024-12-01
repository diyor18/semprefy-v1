import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.oauth2 import create_access_token
from app.database import get_db
from app import models
from sqlalchemy.orm import Session
import random
import string

client = TestClient(app)


@pytest.fixture
def db():
    db = next(get_db())
    db.query(models.Business).delete()
    db.commit()
    yield db


def random_email():
    return f"business_{''.join(random.choices(string.ascii_lowercase, k=5))}@example.com"


# Test: Create a business successfully
def test_create_business_success(db):
    response = client.post(
        "/businesses/create",
        params={
            "email": random_email(),
            "name": "New Business",
            "password": "password123",
            "phone": "0987654321",
            "description": "A new test business",
            "country": "Newland",
            "city": "New City",
            "address": "456 New St.",
            "bank_account": "87654321",
            "bank_account_name": "New Account",
            "bank_name": "New Bank",
        }
    )
    assert response.status_code == 200
    assert "email" in response.json()



def test_create_business_missing_fields(db):
    response = client.post(
        "/businesses/create",
        json={
            "email": random_email(),
            "name": "Incomplete Business",
            "password": "password123",
        },
    )
    assert response.status_code == 422



def test_get_current_business_success(db):
    business = models.Business(
        email=random_email(),
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

    token = create_access_token(data={"id": business.business_id, "role": "business"})
    response = client.get(
        "/businesses/current",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == business.email


def test_update_current_business_success(db):
    business = models.Business(
        email=random_email(),
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

    token = create_access_token(data={"id": business.business_id, "role": "business"})
    response = client.patch(
        "/businesses/current/update",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "name": "Updated Business",
            "phone": "1111111111",
            "city": "Updated City",
        },
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Business"
    assert response.json()["phone"] == "1111111111"


def test_get_business_by_id(db):
    business = models.Business(
        email=random_email(),
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

    response = client.get(f"/businesses/id/{business.business_id}")
    assert response.status_code == 200
    assert response.json()["email"] == business.email


def test_get_business_metrics(db):
    business = models.Business(
        email=random_email(),
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

    token = create_access_token(data={"id": business.business_id, "role": "business"})
    response = client.get(
        "/businesses/current/metrics",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert "MRR" in response.json()


def test_get_current_business_services(db):
    business = models.Business(
        email=random_email(),
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

    token = create_access_token(data={"id": business.business_id, "role": "business"})
    response = client.get(
        "/businesses/current/services",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_current_business_payouts(db):
    business = models.Business(
        email=random_email(),
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

    token = create_access_token(data={"id": business.business_id, "role": "business"})
    response = client.get(
        "/businesses/current/payouts",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_users_with_subscriptions(db):
    business = models.Business(
        email=random_email(),
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

    token = create_access_token(data={"id": business.business_id, "role": "business"})
    response = client.get(
        "/businesses/current/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
