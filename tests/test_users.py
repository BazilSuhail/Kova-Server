import pytest
from app import create_app

@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_create_task(client):
    # First, signup to get token
    signup = client.post("/api/auth/signup", json={
        "name": "Test User",
        "email": "tasktest@example.com",
        "password": "test123"
    })
    token = signup.json["access_token"]
    
    response = client.post("/api/tasks", json={
        "title": "Test Task",
        "description": "Test description",
        "category": "Test",
        "dueDate": "2025-07-25T18:00:00Z",
        "createdFrom": "manual"
    }, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201
    assert "taskId" in response.json