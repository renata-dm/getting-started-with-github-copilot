from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_module, "activities", deepcopy(app_module.activities))
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_get_activities_returns_activity_data(client):
    # Arrange
    activity_name = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert activity_name in response.json()
    assert response.json()[activity_name]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_adds_participant(client):
    # Arrange
    activity_name = "Soccer Team"
    email = "student@example.com"
    activity_path = quote(activity_name, safe="")

    # Act
    response = client.post(
        f"/activities/{activity_path}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    activities_response = client.get("/activities")
    assert email in activities_response.json()[activity_name]["participants"]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity_name = "Soccer Team"
    email = "student@example.com"
    activity_path = quote(activity_name, safe="")
    app_module.activities[activity_name]["participants"].append(email)

    # Act
    response = client.post(
        f"/activities/{activity_path}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    activities_response = client.get("/activities")
    assert activities_response.json()[activity_name]["participants"].count(email) == 1


def test_signup_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Activity"
    activity_path = quote(activity_name, safe="")

    # Act
    response = client.post(
        f"/activities/{activity_path}/signup",
        params={"email": "student@example.com"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    # Arrange
    activity_name = "Soccer Team"
    email = "student@example.com"
    activity_path = quote(activity_name, safe="")
    email_path = quote(email, safe="")
    app_module.activities[activity_name]["participants"].append(email)

    # Act
    response = client.delete(f"/activities/{activity_path}/participants/{email_path}")

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    activities_response = client.get("/activities")
    assert email not in activities_response.json()[activity_name]["participants"]


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    activity_path = quote("Unknown Activity", safe="")
    email_path = quote("student@example.com", safe="")

    # Act
    response = client.delete(f"/activities/{activity_path}/participants/{email_path}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_rejects_unregistered_participant(client):
    # Arrange
    activity_name = "Soccer Team"
    activity_path = quote(activity_name, safe="")
    email_path = quote("student@example.com", safe="")

    # Act
    response = client.delete(f"/activities/{activity_path}/participants/{email_path}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_root_redirects_to_frontend(client):
    # Arrange
    expected_path = "/static/index.html"

    # Act
    response = client.get("/")

    # Assert
    assert response.status_code == 200
    assert response.url.path == expected_path
    assert response.history[0].status_code == 307