import importlib
from copy import deepcopy

import pytest
import warnings
from starlette.exceptions import StarletteDeprecationWarning
warnings.filterwarnings("ignore", category=StarletteDeprecationWarning)
from fastapi.testclient import TestClient

# Import the app module so we can reset its `activities`
app_module = importlib.import_module("src.app")
from src.app import app as fastapi_app  # the FastAPI instance


@pytest.fixture(autouse=True)
def deepcopy_activities():
    """Deepcopy fixture to reset `activities` in src.app after each test."""
    original = deepcopy(app_module.activities)
    try:
        yield
    finally:
        app_module.activities = original


@pytest.fixture
def client():
    return TestClient(fastapi_app)


def test_get_activities(client):
    # Arrange (none)

    # Act
    resp = client.get("/activities")

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert data == app_module.activities


def test_signup_success(client):
    # Arrange
    activity = "Chess Club"
    email = "new_student@mergington.edu"
    assert email not in app_module.activities[activity]["participants"]

    # Act
    resp = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert resp.status_code == 200
    assert resp.json() == {"message": f"Signed up {email} for {activity}"}
    assert email in app_module.activities[activity]["participants"]


def test_duplicate_signup_returns_400(client):
    # Arrange
    activity = "Chess Club"
    email = "duplicate@mergington.edu"
    resp1 = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert resp1.status_code == 200

    # Act
    resp2 = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert resp2.status_code == 400
    assert "already signed up" in resp2.json().get("detail", "").lower()


def test_remove_participant_success(client):
    # Arrange
    activity = "Chess Club"
    email = "michael@mergington.edu"
    assert email in app_module.activities[activity]["participants"]

    # Act
    resp = client.delete(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert resp.status_code == 200
    assert resp.json() == {"message": f"Removed {email} from {activity}"}
    assert email not in app_module.activities[activity]["participants"]


def test_signup_activity_not_found_returns_404(client):
    # Act
    resp = client.post("/activities/Nonexistent/signup", params={"email": "a@b.com"})

    # Assert
    assert resp.status_code == 404
    assert "not found" in resp.json().get("detail", "").lower()


def test_remove_activity_not_found_returns_404(client):
    # Act
    resp = client.delete("/activities/Nonexistent/signup", params={"email": "a@b.com"})

    # Assert
    assert resp.status_code == 404
    assert "not found" in resp.json().get("detail", "").lower()


def test_remove_participant_not_found_returns_404(client):
    # Arrange
    activity = "Chess Club"
    email = "not_in_list@mergington.edu"
    assert email not in app_module.activities[activity]["participants"]

    # Act
    resp = client.delete(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert resp.status_code == 404
    assert "participant not found" in resp.json().get("detail", "").lower()
