import pytest

pytestmark = pytest.mark.slow
from fastapi.testclient import TestClient

from nexa.api.main import app

EMPLOYEE = {"email": "layla@falcon.example", "password": "dev-password-123"}
DIRECTOR = {"email": "huda@falcon.example", "password": "dev-password-123"}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _token(client, credentials: dict) -> str:
    response = client.post("/auth/login", json=credentials)
    assert response.status_code == 200
    return response.json()["access_token"]


def test_health_is_public(client) -> None:
    assert client.get("/health").status_code == 200


def test_search_without_token_is_rejected(client) -> None:
    assert client.get("/search", params={"q": "annual leave"}).status_code == 401


def test_search_with_malformed_token_is_rejected(client) -> None:
    response = client.get(
        "/search",
        params={"q": "annual leave"},
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert response.status_code == 401


def test_login_with_wrong_password_is_rejected(client) -> None:
    response = client.post(
        "/auth/login",
        json={"email": "layla@falcon.example", "password": "wrong"},
    )
    assert response.status_code == 401


def test_login_with_unknown_email_gives_same_error(client) -> None:
    response = client.post(
        "/auth/login",
        json={"email": "ghost@falcon.example", "password": "dev-password-123"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "invalid email or password"


def test_search_with_valid_token_succeeds(client) -> None:
    token = _token(client, EMPLOYEE)
    response = client.get(
        "/search",
        params={"q": "ÙƒÙ… ÙŠÙˆÙ… Ø¥Ø¬Ø§Ø²Ø© Ø³Ù†ÙˆÙŠØ©ØŸ"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()[0]["doc_id"].startswith("annual_leave_en")


def test_me_returns_identity_from_token_not_request(client) -> None:
    token = _token(client, EMPLOYEE)
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["role"] == "employee"


def test_director_and_employee_get_different_roles(client) -> None:
    employee = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {_token(client, EMPLOYEE)}"},
    ).json()
    director = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {_token(client, DIRECTOR)}"},
    ).json()

    assert employee["role"] == "employee"
    assert director["role"] == "director"