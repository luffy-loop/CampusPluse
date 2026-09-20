from datetime import datetime

import pytest

from app import app
import routes.tracking as tracking_module


@pytest.fixture
def client(monkeypatch):
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"
    monkeypatch.setattr(tracking_module, "DISABLE_DB", True)
    tracking_module.mock_complaints.clear()
    tracking_module.mock_complaint_counter = 1

    with app.test_client() as client:
        yield client


def login_student(client, roll_no="TEST001"):
    with client.session_transaction() as session:
        session["student_roll_no"] = roll_no


def add_complaint(complaint_id, roll_no="TEST001"):
    now = datetime.now()
    tracking_module.mock_complaints[complaint_id] = {
        "id": complaint_id,
        "uni_roll_no": roll_no,
        "description": "Broken light",
        "category": "Infrastructure",
        "department": "Facilities",
        "location": "Library",
        "severity": 4,
        "priority": "High",
        "issue_group": "Lighting",
        "recommended_action": "Inspect the light.",
        "status": "Pending",
        "created_at": now,
        "updated_at": now
    }


def test_track_page_requires_login(client):
    response = client.get("/track")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/student/login")


def test_track_page_loads_for_logged_in_student(client):
    login_student(client)

    response = client.get("/track")

    assert response.status_code == 200


def test_student_sees_only_own_complaints(client):
    login_student(client, "TEST001")
    add_complaint(1, "TEST001")
    add_complaint(2, "TEST002")

    response = client.get("/api/complaints")
    data = response.get_json()

    assert response.status_code == 200
    assert data["count"] == 1
    assert data["complaints"][0]["id"] == 1


def test_student_complaint_detail_is_scoped_to_session(client):
    login_student(client, "TEST001")
    add_complaint(1, "TEST002")

    response = client.get("/api/complaints/1")

    assert response.status_code == 404
    assert response.get_json()["error"] == "Complaint not found."


def test_student_can_view_own_complaint_detail(client):
    login_student(client, "TEST001")
    add_complaint(1, "TEST001")

    response = client.get("/api/complaints/1")
    data = response.get_json()

    assert response.status_code == 200
    assert data["complaint"]["id"] == 1
    assert data["complaint"]["status"] == "Pending"


def test_student_cannot_view_missing_complaint(client):
    login_student(client, "TEST001")

    response = client.get("/api/complaints/999")

    assert response.status_code == 404
    assert response.get_json()["error"] == "Complaint not found."
