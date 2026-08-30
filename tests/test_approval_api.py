import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from nexa.api.main import app
from nexa.db.connection import engine
from nexa.db.models import Project

pytestmark = pytest.mark.slow

OMAR = {"email": "omar@falcon.example", "password": "dev-password-123"}
HUDA = {"email": "huda@falcon.example", "password": "dev-password-123"}
LAYLA = {"email": "layla@falcon.example", "password": "dev-password-123"}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _auth(client, credentials: dict) -> dict:
    token = client.post("/auth/login", json=credentials).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _reset(code: str, status: str) -> None:
    with Session(engine) as session:
        project = session.scalar(select(Project).where(Project.code == code))
        project.status = status
        session.commit()


def _status(client, headers: dict, code: str) -> str:
    return client.get(f"/approvals/{code}", headers=headers).status_code


def test_full_approval_journey(client) -> None:
    _reset("PRJ-001", "active")

    omar = _auth(client, OMAR)
    huda = _auth(client, HUDA)

    # 1. manager requests a change
    response = client.post(
        "/projects/request-status-change",
        json={
            "code": "PRJ-001",
            "new_status": "on_hold",
            "reason": "vendor contract delayed by three weeks",
        },
        headers=omar,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["submitted"] is True
    assert body["executed"] is False

    request_id = body["approval_request_id"]

    # 2. nothing changed yet
    with Session(engine) as session:
        assert session.scalar(
            select(Project.status).where(Project.code == "PRJ-001")
        ) == "active"

    # 3. the request appears for the approver
    pending = client.get("/approvals/pending", headers=huda).json()
    assert any(r["id"] == request_id for r in pending)

    # 4. director approves
    decision = client.post(
        f"/approvals/{request_id}/decide",
        json={"approve": True},
        headers=huda,
    )
    assert decision.status_code == 200
    assert decision.json()["ok"] is True

    # 5. now it changed
    with Session(engine) as session:
        assert session.scalar(
            select(Project.status).where(Project.code == "PRJ-001")
        ) == "on_hold"

    _reset("PRJ-001", "active")


def test_employee_cannot_request_change(client) -> None:
    response = client.post(
        "/projects/request-status-change",
        json={
            "code": "PRJ-001",
            "new_status": "on_hold",
            "reason": "trying without permission at all",
        },
        headers=_auth(client, LAYLA),
    )
    assert response.status_code == 403


def test_manager_cannot_see_pending_queue(client) -> None:
    response = client.get("/approvals/pending", headers=_auth(client, OMAR))
    assert response.status_code == 403


def test_requester_can_track_own_request(client) -> None:
    _reset("PRJ-005", "planning")
    omar = _auth(client, OMAR)

    request_id = client.post(
        "/projects/request-status-change",
        json={
            "code": "PRJ-005",
            "new_status": "active",
            "reason": "kickoff approved by steering committee",
        },
        headers=omar,
    ).json()["approval_request_id"]

    detail = client.get(f"/approvals/{request_id}", headers=omar)
    assert detail.status_code == 200
    assert detail.json()["status"] == "pending"


def test_rejection_leaves_project_untouched(client) -> None:
    _reset("PRJ-007", "active")
    omar = _auth(client, OMAR)
    huda = _auth(client, HUDA)

    request_id = client.post(
        "/projects/request-status-change",
        json={
            "code": "PRJ-007",
            "new_status": "cancelled",
            "reason": "considering cancellation of this initiative",
        },
        headers=omar,
    ).json()["approval_request_id"]

    client.post(
        f"/approvals/{request_id}/decide",
        json={"approve": False, "reason": "not yet, revisit in Q4"},
        headers=huda,
    )

    with Session(engine) as session:
        assert session.scalar(
            select(Project.status).where(Project.code == "PRJ-007")
        ) == "active"