from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def activities(monkeypatch):
    isolated_activities = deepcopy(app_module.activities)
    monkeypatch.setattr(app_module, "activities", isolated_activities)
    return isolated_activities


@pytest.fixture
def client(activities):
    with TestClient(app_module.app, follow_redirects=False) as test_client:
        yield test_client


def test_root_redirects_to_static_index(client):
    response = client.get("/")

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_seeded_activities(client, activities):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == activities


def test_signup_adds_participant(client, activities):
    email = "new-student@mergington.edu"
    response = client.post("/activities/Art%20Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Art Club"}
    assert email in activities["Art Club"]["participants"]


def test_signup_rejects_duplicate_participant(client, activities):
    email = activities["Chess Club"]["participants"][0]
    participant_count = len(activities["Chess Club"]["participants"])
    response = client.post("/activities/Chess%20Club/signup", params={"email": email})

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert len(activities["Chess Club"]["participants"]) == participant_count


def test_signup_returns_404_for_unknown_activity(client):
    response = client.post("/activities/Unknown%20Activity/signup", params={"email": "student@mergington.edu"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client, activities):
    email = activities["Art Club"]["participants"]
    email.append("student@mergington.edu")
    response = client.delete("/activities/Art%20Club/signup", params={"email": "student@mergington.edu"})

    assert response.status_code == 200
    assert response.json() == {"message": "Removed student@mergington.edu from Art Club"}
    assert "student@mergington.edu" not in activities["Art Club"]["participants"]


def test_unregister_returns_404_for_unregistered_participant(client):
    response = client.delete(
        "/activities/Art%20Club/signup",
        params={"email": "missing@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_returns_404_for_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown%20Activity/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_clears_all_existing_duplicate_registrations(client, activities):
    email = "duplicate@mergington.edu"
    activities["Art Club"]["participants"].extend([email, email])

    response = client.delete("/activities/Art%20Club/signup", params={"email": email})

    assert response.status_code == 200
    assert email not in activities["Art Club"]["participants"]
