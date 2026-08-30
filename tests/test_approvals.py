import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from nexa.approvals.service import ApprovalStatus, create_request, decide
from nexa.auth.dependencies import UserContext
from nexa.auth.permissions import Role
from nexa.db.connection import engine
from nexa.db.models import AuditEvent, Project

OMAR = UserContext("u-omar", Role.MANAGER, "Omar")
FAHAD = UserContext("u-fahad", Role.MANAGER, "Fahad")
HUDA = UserContext("u-huda", Role.DIRECTOR, "Huda")
LAYLA = UserContext("u-layla", Role.EMPLOYEE, "Layla")


def _status(code: str) -> str:
    with Session(engine) as session:
        return session.scalar(select(Project.status).where(Project.code == code))


def _set_status(code: str, status: str) -> None:
    with Session(engine) as session:
        project = session.scalar(select(Project).where(Project.code == code))
        project.status = status
        session.commit()


def _request(code: str, new_status: str, user: UserContext, current: str) -> str:
    return create_request(
        "update_project_status",
        {
            "code": code,
            "new_status": new_status,
            "reason": "test justification for the change",
            "expected_current_status": current,
        },
        "project",
        code,
        {"status": current},
        {"status": new_status},
        "test justification",
        user,
    )


@pytest.fixture
def active_project() -> str:
    _set_status("PRJ-001", "active")
    yield "PRJ-001"
    _set_status("PRJ-001", "active")


def test_request_does_not_mutate_anything(active_project: str) -> None:
    _request(active_project, "on_hold", OMAR, "active")
    assert _status(active_project) == "active"


def test_approval_executes_the_change(active_project: str) -> None:
    request_id = _request(active_project, "on_hold", OMAR, "active")
    result = decide(request_id, True, HUDA)

    assert result["ok"] is True
    assert _status(active_project) == "on_hold"


def test_rejection_changes_nothing(active_project: str) -> None:
    request_id = _request(active_project, "on_hold", OMAR, "active")
    decide(request_id, False, HUDA, reason="not now")

    assert _status(active_project) == "active"


def test_requester_cannot_approve_own_request(active_project: str) -> None:
    request_id = _request(active_project, "on_hold", HUDA, "active")
    result = decide(request_id, True, HUDA)

    assert result["error_code"] == "SELF_APPROVAL_FORBIDDEN"
    assert _status(active_project) == "active"


def test_manager_cannot_approve(active_project: str) -> None:
    request_id = _request(active_project, "on_hold", OMAR, "active")
    result = decide(request_id, True, FAHAD)

    assert result["error_code"] == "PERMISSION_DENIED"
    assert _status(active_project) == "active"


def test_employee_cannot_approve(active_project: str) -> None:
    request_id = _request(active_project, "on_hold", OMAR, "active")
    result = decide(request_id, True, LAYLA)

    assert result["error_code"] == "PERMISSION_DENIED"


def test_approval_executes_only_once(active_project: str) -> None:
    request_id = _request(active_project, "on_hold", OMAR, "active")

    first = decide(request_id, True, HUDA)
    second = decide(request_id, True, HUDA)

    assert first["ok"] is True
    assert second["error_code"] == "ALREADY_DECIDED"


def test_stale_state_blocks_execution(active_project: str) -> None:
    request_id = _request(active_project, "on_hold", OMAR, "active")
    _set_status(active_project, "completed")

    result = decide(request_id, True, HUDA)

    assert result["ok"] is False
    assert result["result"]["error_code"] == "STATE_CHANGED_SINCE_REQUEST"


def test_invalid_transition_is_blocked(active_project: str) -> None:
    _set_status(active_project, "completed")
    request_id = _request(active_project, "planning", OMAR, "completed")

    result = decide(request_id, True, HUDA)

    assert result["ok"] is False
    assert result["result"]["error_code"] == "INVALID_TRANSITION"


def test_unknown_request_is_rejected() -> None:
    result = decide(f"apr-{uuid.uuid4().hex[:16]}", True, HUDA)
    assert result["error_code"] == "REQUEST_NOT_FOUND"


def test_execution_writes_an_audit_trail(active_project: str) -> None:
    request_id = _request(active_project, "on_hold", OMAR, "active")
    decide(request_id, True, HUDA)

    with Session(engine) as session:
        events = session.scalars(
            select(AuditEvent).where(AuditEvent.approval_request_id == request_id)
        ).all()

    types = {e.event_type for e in events}
    assert "action_requested" in types
    assert "action_executed" in types

    executed = next(e for e in events if e.event_type == "action_executed")
    assert executed.actor_id == "u-huda"
    assert executed.on_behalf_of_id == "u-omar"