import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.oauth2 import create_access_token
from app.database import get_db
from app import models

client = TestClient(app)

@pytest.fixture(scope="module")
def fetch_ids():
    db = next(get_db())
    existing_user = db.query(models.User).first()
    existing_business = db.query(models.Business).first()
    
    user_id = existing_user.user_id if existing_user else None
    business_id = existing_business.business_id if existing_business else None
    
    return user_id, business_id

@pytest.fixture(scope="module")
def tokens(fetch_ids):
    user_id, business_id = fetch_ids
    if not user_id or not business_id:
        pytest.fail("No user or business exists in the database.")
    
    user_token = create_access_token({"id": user_id, "role": "user"})
    business_token = create_access_token({"id": business_id, "role": "business"})
    
    return user_token, business_token

# Global variable for service ID
SERVICE_ID = None

def get_existing_service_id(business_token):
    response = client.get(
        "/services/my_services",
        headers={"Authorization": f"Bearer {business_token}"}
    )
    assert response.status_code == 200, response.text
    services = response.json()
    return services[0]["service_id"] if services else None

def test_create_service_success(tokens):
    global SERVICE_ID
    _, business_token = tokens

    service_data = {
        "name": "Test Service",
        "description": "A service for testing",
        "price": 100.0,
        "duration": 30
    }
    response = client.post(
        "/services/create",
        headers={"Authorization": f"Bearer {business_token}"},
        json=service_data
    )
    assert response.status_code == 200, response.text
    data = response.json()

    SERVICE_ID = data["service_id"]

    assert data["name"] == service_data["name"]
    assert data["price"] == service_data["price"]
    assert data["status"] == "active"

def test_get_all_services(tokens):
    user_token, _ = tokens
    response = client.get(
        "/services/all",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200, response.text
    assert isinstance(response.json(), list)

def test_get_my_services(tokens):
    global SERVICE_ID
    _, business_token = tokens
    SERVICE_ID = get_existing_service_id(business_token)

    response = client.get(
        "/services/my_services",
        headers={"Authorization": f"Bearer {business_token}"}
    )
    assert response.status_code == 200, response.text
    assert any(service["service_id"] == SERVICE_ID for service in response.json())

def test_get_service_by_id(tokens):
    global SERVICE_ID
    _, business_token = tokens
    SERVICE_ID = get_existing_service_id(business_token)

    response = client.get(f"/services/{SERVICE_ID}")
    assert response.status_code == 200, response.text
    assert response.json()["service_id"] == SERVICE_ID

def test_update_service(tokens):
    global SERVICE_ID
    _, business_token = tokens
    SERVICE_ID = get_existing_service_id(business_token)

    response = client.put(
        f"/services/update/{SERVICE_ID}",
        headers={"Authorization": f"Bearer {business_token}"},
        params={
            "price": 150.0,
            "name": "Updated Service",
            "description": "Updated description",
            "duration": 60,
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["price"] == 150.0
    assert data["name"] == "Updated Service"
    assert data["description"] == "Updated description"
    assert data["duration"] == 60

def test_toggle_service_status(tokens):
    global SERVICE_ID
    _, business_token = tokens
    SERVICE_ID = get_existing_service_id(business_token)

    response = client.put(
        f"/services/toggle-status/{SERVICE_ID}",
        headers={"Authorization": f"Bearer {business_token}"}
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] in ["active", "not active"]

def test_delete_service(tokens):
    global SERVICE_ID
    _, business_token = tokens
    SERVICE_ID = get_existing_service_id(business_token)

    response = client.delete(
        f"/services/delete/{SERVICE_ID}",
        headers={"Authorization": f"Bearer {business_token}"}
    )
    assert response.status_code == 204, response.text

def test_get_current_business_services(tokens):
    _, business_token = tokens
    response = client.get(
        "/services/my_services",
        headers={"Authorization": f"Bearer {business_token}"}
    )
    assert response.status_code == 200, response.text
    assert isinstance(response.json(), list)
