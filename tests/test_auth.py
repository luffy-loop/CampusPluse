import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def test_student_login_page(client):
    response = client.get("/student/login")
    assert response.status_code == 200


def test_student_login_requires_roll_no(client):
    response = client.post("/student/login", data={})
    assert response.status_code == 400


def test_student_login_accepts_valid_roll_no(client):
    response = client.post(
        "/student/login",
        data={"roll_no": "23A91A0001"}
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/student")