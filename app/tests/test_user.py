import pytest
import random
import string
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.oauth2 import create_access_token
from app.database import get_db
from app.models import User

@pytest.fixture(scope="module")
def client():

    with TestClient(app) as c:
        yield c

def generate_random_email():
    prefix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}@example.com"


def get_user_id_by_email(email: str, db: Session):
    user = db.query(User).filter(User.email == email).first()
    return user.user_id if user else None


RANDOM_EMAIL = generate_random_email()

def test_create_user_success(client):
    global RANDOM_EMAIL
    RANDOM_EMAIL = generate_random_email()  
    response = client.post(
        "/users/create",
        params={
            "name": "Test User",
            "email": RANDOM_EMAIL,
            "password": "password123",
            "card_number": "4111 1111 1111 1111",
            "card_expiry": "12/25",
            "card_cvc": "123"
        }
    )
    assert response.status_code == 200, response.text
    data = response.json()

    
    assert data["email"] == RANDOM_EMAIL
    assert data["name"] == "Test User"

def test_get_current_user_success(client):

    db = next(get_db())
    user_id = get_user_id_by_email(RANDOM_EMAIL, db)
    assert user_id is not None, "User ID must exist after user creation"

    token = create_access_token(data={"id": user_id, "role": "user"})
    
    
    response = client.get(
        "/users/current",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200, response.text
    assert response.json()["user_id"] == user_id

def test_get_current_user_no_token(client):
    response = client.get("/users/current") 
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

def test_update_user_success(client):
    db = next(get_db())
    user_id = get_user_id_by_email(RANDOM_EMAIL, db)
    assert user_id is not None, "User ID must exist after user creation"

    token = create_access_token(data={"id": user_id, "role": "user"})
    response = client.patch(
        "/users/update",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "name": "Updated User",
            "email": RANDOM_EMAIL,
            "card_number": "4111 1111 1111 1111",
            "card_expiry": "12/30",
            "card_cvc": "456"
        }
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "Updated User"
    assert data["email"] == RANDOM_EMAIL

def test_update_user_no_auth(client):
    response = client.patch(
        "/users/update",
        params={
            "name": "Updated User",
            "email": "updateduser@example.com",
            "card_number": "4111 1111 1111 1111",
            "card_expiry": "12/30",
            "card_cvc": "456"
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
