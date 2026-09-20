from datetime import datetime

import pytest

from app import app
import routes.admin as admin_module


@pytest.fixture
def client(monkeypatch):
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"
    monkeypatch.setattr(admin_module, "DISABLE_DB", True)
    admin_module.mock_complaints.clear()
    admin_module.mock_complaint_counter = 1

    with app.test_client() as client:
        yield client


def login_admin(client, monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "secret")
    response = client.post(
        "/admin/login",
        data={"username": "admin", "password": "secret"}
    )
    assert response.status_code == 302


def test_admin_login_page(client):
    response = client.get("/admin/login")

    assert response.status_code == 200


def test_admin_rejects_invalid_credentials(client, monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "secret")

    response = client.post(
        "/admin/login",
        data={"username": "admin", "password": "wrong"}
    )

    assert response.status_code == 401


def test_admin_requires_credentials_to_be_configured(client, monkeypatch):
    monkeypatch.delenv("ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)

    response = client.post(
        "/admin/login",
        data={"username": "admin", "password": "secret"}
    )

    assert response.status_code == 401


def test_admin_dashboard_requires_authentication(client):
    response = client.get("/api/admin/dashboard")

    assert response.status_code == 401
    assert response.get_json()["success"] is False


def test_admin_can_view_dashboard(client, monkeypatch):
    login_admin(client, monkeypatch)
    admin_module.mock_complaints[1] = {
        "id": 1,
        "uni_roll_no": "TEST001",
        "description": "Broken light",
        "category": "Infrastructure",
        "department": "Facilities",
        "location": "Library",
        "severity": 4,
        "priority": "High",
        "status": "Pending",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "evidence_path": None
    }

    response = client.get("/api/admin/dashboard")
    data = response.get_json()

    assert response.status_code == 200
    assert data["stats"]["total"] == 1
    assert data["stats"]["pending"] == 1
    assert data["stats"]["high_priority"] == 1
    assert data["complaints"][0]["id"] == 1


def test_admin_rejects_invalid_status(client, monkeypatch):
    login_admin(client, monkeypatch)

    response = client.put(
        "/api/admin/complaints/1/status",
        json={"status": "Deleted"}
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Invalid status."


def test_admin_updates_complaint_status(client, monkeypatch):
    login_admin(client, monkeypatch)
    admin_module.mock_complaints[1] = {
        "id": 1,
        "uni_roll_no": "TEST001",
        "description": "Broken light",
        "category": "Infrastructure",
        "department": "Facilities",
        "location": "Library",
        "severity": 4,
        "priority": "High",
        "status": "Pending",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "evidence_path": None
    }

    response = client.put(
        "/api/admin/complaints/1/status",
        json={"status": "Resolved"}
    )

    assert response.status_code == 200
    assert admin_module.mock_complaints[1]["status"] == "Resolved"


def test_admin_status_update_returns_not_found(client, monkeypatch):
    login_admin(client, monkeypatch)

    response = client.put(
        "/api/admin/complaints/999/status",
        json={"status": "Resolved"}
    )

    assert response.status_code == 404
    assert response.get_json()["error"] == "Complaint not found."
