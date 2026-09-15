from io import BytesIO

import pytest

from app import app
import routes.complaints as complaints_module


@pytest.fixture
def client(monkeypatch):
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"
    monkeypatch.setattr(complaints_module, "DISABLE_DB", True)
    complaints_module.mock_complaints.clear()
    complaints_module.mock_complaint_counter = 1
    monkeypatch.setattr(
        complaints_module,
        "analyze_complaint",
        lambda description: {
            "category": "Infrastructure",
            "department": "Facilities",
            "location": "Library",
            "severity": 4,
            "priority": "High",
            "issue": description[:100],
            "recommended_action": "Inspect the reported issue."
        }
    )

    with app.test_client() as client:
        with client.session_transaction() as session:
            session["student_roll_no"] = "TEST001"
        yield client


def test_complaint_requires_student_session(client):
    with client.session_transaction() as session:
        session.clear()

    response = client.post(
        "/api/complaints",
        data={"description": "Broken light"}
    )

    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_complaint_requires_description(client):
    response = client.post("/api/complaints", data={})

    assert response.status_code == 400
    assert response.get_json()["error"] == "Complaint description is required."


def test_complaint_rejects_long_description(client):
    response = client.post(
        "/api/complaints",
        data={"description": "x" * 5001}
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Complaint description is too long."


def test_complaint_rejects_invalid_evidence_type(client):
    response = client.post(
        "/api/complaints",
        data={
            "description": "Broken light",
            "evidence": (BytesIO(b"bad file"), "malware.exe")
        },
        content_type="multipart/form-data"
    )

    assert response.status_code == 400
    assert "Invalid file type" in response.get_json()["error"]


def test_complaint_submits_in_mock_mode(client):
    response = client.post(
        "/api/complaints",
        data={"description": "Broken light"}
    )

    data = response.get_json()
    assert response.status_code == 200
    assert data["success"] is True
    assert data["id"] == 1
    assert data["mode"] == "mock"
    assert complaints_module.mock_complaints[1]["uni_roll_no"] == "TEST001"


def test_complaint_preserves_anonymous_flag(client):
    response = client.post(
        "/api/complaints",
        data={
            "description": "Broken light",
            "is_anonymous": "true"
        }
    )

    assert response.status_code == 200
    assert complaints_module.mock_complaints[1]["is_anonymous"] is True


def test_complaint_accepts_allowed_evidence(client, tmp_path, monkeypatch):
    monkeypatch.setattr(complaints_module, "UPLOAD_FOLDER", tmp_path)

    response = client.post(
        "/api/complaints",
        data={
            "description": "Broken light",
            "evidence": (BytesIO(b"fake png data"), "photo.PNG")
        },
        content_type="multipart/form-data"
    )

    data = response.get_json()
    assert response.status_code == 200
    assert data["evidence_uploaded"] is True
    assert len(list(tmp_path.iterdir())) == 1
