import uuid
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from sqlalchemy import select
from sqlalchemy.orm import Session

from nexa.audit.log import EventType, Outcome, record
from nexa.auth.dependencies import UserContext
from nexa.auth.permissions import Permission, has_permission
from nexa.db.connection import engine
from nexa.db.models import ApprovalRequest
from nexa.tools.base import ToolError
from nexa.tools.executor import registry

APPROVAL_TTL_HOURS = 48


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    EXECUTED = "executed"
    EXECUTION_FAILED = "execution_failed"


def create_request(
    tool_name: str,
    arguments: dict,
    target_type: str,
    target_id: str,
    expected_state: dict,
    proposed_state: dict,
    justification: str,
    user: UserContext,
) -> str:
    """Persist a pending approval. Nothing is mutated."""
    request_id = f"apr-{uuid.uuid4().hex[:16]}"
    now = datetime.now(UTC)

    with Session(engine) as session:
        session.add(
            ApprovalRequest(
                id=request_id,
                status=ApprovalStatus.PENDING.value,
                requester_id=user.user_id,
                tool_name=tool_name,
                tool_arguments=arguments,
                target_type=target_type,
                target_id=target_id,
                expected_current_state=expected_state,
                proposed_state=proposed_state,
                justification=justification,
                expires_at=now + timedelta(hours=APPROVAL_TTL_HOURS),
            )
        )

        record(
            session,
            event_type=EventType.ACTION_REQUESTED,
            actor_id=user.user_id,
            actor_role=user.role.value,
            target_type=target_type,
            target_id=target_id,
            before_state=expected_state,
            after_state=proposed_state,
            tool_name=tool_name,
            tool_arguments=arguments,
            approval_request_id=request_id,
            outcome=Outcome.SUCCESS,
        )

        session.commit()

    return request_id


def decide(
    request_id: str,
    approve: bool,
    approver: UserContext,
    reason: str | None = None,
) -> dict:
    """Approve or reject. On approval, execute inside the same transaction."""
    if not has_permission(approver.role, Permission.APPROVALS_DECIDE):
        return {"ok": False, "error_code": "PERMISSION_DENIED"}

    with Session(engine) as session:
        request = session.scalar(
            select(ApprovalRequest)
            .where(ApprovalRequest.id == request_id)
            .with_for_update()
        )

        if request is None:
            return {"ok": False, "error_code": "REQUEST_NOT_FOUND"}

        if request.status != ApprovalStatus.PENDING.value:
            return {"ok": False, "error_code": "ALREADY_DECIDED",
                    "status": request.status}

        if datetime.now(UTC) >= request.expires_at.replace(tzinfo=UTC):
            request.status = ApprovalStatus.EXPIRED.value
            session.commit()
            return {"ok": False, "error_code": "APPROVAL_EXPIRED"}

        if request.requester_id == approver.user_id:
            return {"ok": False, "error_code": "SELF_APPROVAL_FORBIDDEN"}

        request.approver_id = approver.user_id
        request.decided_at = datetime.now(UTC)
        request.decision_reason = reason

        if not approve:
            request.status = ApprovalStatus.REJECTED.value
            record(
                session,
                event_type=EventType.ACTION_REJECTED,
                actor_id=approver.user_id,
                actor_role=approver.role.value,
                on_behalf_of_id=request.requester_id,
                target_type=request.target_type,
                target_id=request.target_id,
                tool_name=request.tool_name,
                approval_request_id=request_id,
                outcome=Outcome.DENIED,
            )
            session.commit()
            return {"ok": True, "status": "rejected"}

        tool = registry.get(request.tool_name)
        if tool is None:
            request.status = ApprovalStatus.EXECUTION_FAILED.value
            session.commit()
            return {"ok": False, "error_code": "UNKNOWN_TOOL"}

        requester_ctx = UserContext(
            user_id=request.requester_id,
            role=approver.role,
            full_name="",
        )

        result = tool.handler(
            tool.input_schema(**request.tool_arguments), requester_ctx
        )

        executed = result.data.get("executed") is True

        request.status = (
            ApprovalStatus.EXECUTED.value if executed
            else ApprovalStatus.EXECUTION_FAILED.value
        )
        request.executed_at = datetime.now(UTC)

        record(
            session,
            event_type=(
                EventType.ACTION_EXECUTED if executed else EventType.ACTION_FAILED
            ),
            actor_id=approver.user_id,
            actor_role=approver.role.value,
            on_behalf_of_id=request.requester_id,
            target_type=request.target_type,
            target_id=request.target_id,
            before_state=request.expected_current_state,
            after_state=result.data if executed else None,
            tool_name=request.tool_name,
            tool_arguments=request.tool_arguments,
            approval_request_id=request_id,
            outcome=Outcome.SUCCESS if executed else Outcome.FAILED,
            error_code=None if executed else result.data.get("error_code"),
        )

        session.commit()

        return {"ok": executed, "status": request.status, "result": result.data}