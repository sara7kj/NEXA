import uuid
from enum import StrEnum
from typing import Any

from sqlalchemy.orm import Session

from nexa.db.models import AuditEvent


class EventType(StrEnum):
    ACTION_REQUESTED = "action_requested"
    ACTION_APPROVED = "action_approved"
    ACTION_REJECTED = "action_rejected"
    ACTION_EXECUTED = "action_executed"
    ACTION_FAILED = "action_failed"
    APPROVAL_EXPIRED = "approval_expired"
    PERMISSION_DENIED = "permission_denied"


class Outcome(StrEnum):
    SUCCESS = "success"
    DENIED = "denied"
    FAILED = "failed"


def record(
    session: Session,
    *,
    event_type: EventType,
    actor_id: str,
    actor_role: str,
    target_type: str,
    target_id: str,
    outcome: Outcome,
    on_behalf_of_id: str | None = None,
    before_state: dict[str, Any] | None = None,
    after_state: dict[str, Any] | None = None,
    tool_name: str | None = None,
    tool_arguments: dict[str, Any] | None = None,
    approval_request_id: str | None = None,
    error_code: str | None = None,
) -> str:
    """Append an audit event to the caller's transaction.

    Deliberately does NOT commit. The caller commits, so the audit row and the
    state change it describes succeed or fail together.
    """
    event_id = f"aud-{uuid.uuid4().hex[:16]}"

    session.add(
        AuditEvent(
            id=event_id,
            event_type=event_type.value,
            actor_id=actor_id,
            actor_role=actor_role,
            on_behalf_of_id=on_behalf_of_id,
            target_type=target_type,
            target_id=target_id,
            before_state=before_state,
            after_state=after_state,
            tool_name=tool_name,
            tool_arguments=tool_arguments,
            approval_request_id=approval_request_id,
            outcome=outcome.value,
            error_code=error_code,
        )
    )

    return event_id