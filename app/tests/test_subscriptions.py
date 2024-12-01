import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app import models
from app.oauth2 import create_access_token
import random
import string

client = TestClient(app)

# Helper functions
def random_email():
    """Generate a random email for testing."""
    return f"user_{''.join(random.choices(string.ascii_lowercase, k=5))}@example.com"

def random_business_email():
    """Generate a random business email for testing."""
    return f"business_{''.join(random.choices(string.ascii_lowercase, k=5))}@example.com"

@pytest.fixture
def setup_data():
    """Fixture to set up test data for user, business, service, and card."""
    db = next(get_db())
    
    # Create a test user
    user_email = random_email()
    user = models.User(
        email=user_email,
        name="Test User",
        password="hashedpassword"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create a test business
    business_email = random_business_email()
    business = models.Business(
        email=business_email,
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

    # Create a card for the user
    card = models.Card(
        user_id=user.user_id,
        card_number="4111 1111 1111 1111",
        card_expiry="12/30",
        card_brand="Visa"
    )
    db.add(card)
    db.commit()
    db.refresh(card)

    return {
        "user_id": user.user_id,
        "business_id": business.business_id,
        "service_id": service.service_id,
    }

def test_create_subscription(setup_data):
    """Test creating a subscription."""
    user_id = setup_data["user_id"]
    service_id = setup_data["service_id"]

    user_token = create_access_token(data={"id": user_id, "role": "user"})

    response = client.post(
        f"/subscriptions/create/{service_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 201, f"Unexpected status code: {response.status_code}. Response: {response.text}"
    assert "subscription_id" in response.json()

def test_create_subscription_duplicate(setup_data):
    """Test creating a duplicate subscription."""
    user_id = setup_data["user_id"]
    service_id = setup_data["service_id"]

    user_token = create_access_token(data={"id": user_id, "role": "user"})

    # Create the first subscription
    response = client.post(
        f"/subscriptions/create/{service_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 201, f"Unexpected status code: {response.status_code}. Response: {response.text}"

    # Attempt to create the same subscription again
    response = client.post(
        f"/subscriptions/create/{service_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 400, f"Unexpected status code: {response.status_code}. Response: {response.text}"
    assert response.json()["detail"] == "Subscription already exists"

def test_get_my_subscriptions(setup_data):
    """Test retrieving user's subscriptions."""
    user_id = setup_data["user_id"]
    service_id = setup_data["service_id"]

    user_token = create_access_token(data={"id": user_id, "role": "user"})

    # Create a subscription
    response = client.post(
        f"/subscriptions/create/{service_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 201, f"Unexpected status code: {response.status_code}. Response: {response.text}"

    # Retrieve subscriptions
    response = client.get(
        "/subscriptions/my_subscriptions",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200, f"Unexpected status code: {response.status_code}. Response: {response.text}"
    subscriptions = response.json()
    assert len(subscriptions) > 0

def test_get_my_subscriptions_amount(setup_data):
    """Test retrieving the total subscription amount for a user."""
    user_id = setup_data["user_id"]
    service_id = setup_data["service_id"]

    user_token = create_access_token(data={"id": user_id, "role": "user"})

    # Create a subscription
    response = client.post(
        f"/subscriptions/create/{service_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 201, f"Unexpected status code: {response.status_code}. Response: {response.text}"

    # Get total subscription amount
    response = client.get(
        "/subscriptions/my_subscriptions_amount",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200, f"Unexpected status code: {response.status_code}. Response: {response.text}"
    total_amount = response.json()["monthly_payable"]
    assert total_amount == 100.0, f"Expected 100.0, got {total_amount}"
