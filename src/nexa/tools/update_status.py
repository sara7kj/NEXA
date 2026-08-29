from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from nexa.auth.dependencies import UserContext
from nexa.auth.permissions import Permission
from nexa.db.connection import engine
from nexa.db.models import Project
from nexa.tools.base import Sensitivity, ToolDefinition, ToolResult

Status = Literal[
    "planning", "active", "on_hold", "delayed", "completed", "cancelled"
]

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "planning": {"active", "cancelled"},
    "active": {"on_hold", "delayed", "completed", "cancelled"},
    "on_hold": {"active", "cancelled"},
    "delayed": {"active", "on_hold", "completed", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}


class UpdateStatusInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=3, max_length=32)
    new_status: Status
    reason: str = Field(min_length=10, max_length=500)
    expected_current_status: Status


def update_project_status(
    args: UpdateStatusInput, user: UserContext
) -> ToolResult:
    with Session(engine) as session:
        project = session.scalar(
            select(Project).where(Project.code == args.code.upper()).with_for_update()
        )

        if project is None:
            return ToolResult(data={
                "executed": False,
                "error_code": "PROJECT_NOT_FOUND",
            })

        if project.status != args.expected_current_status:
            return ToolResult(data={
                "executed": False,
                "error_code": "STATE_CHANGED_SINCE_REQUEST",
                "expected": args.expected_current_status,
                "actual": project.status,
            })

        if args.new_status not in ALLOWED_TRANSITIONS[project.status]:
            return ToolResult(data={
                "executed": False,
                "error_code": "INVALID_TRANSITION",
                "from_status": project.status,
                "to_status": args.new_status,
            })

        previous = project.status
        project.status = args.new_status
        project.version += 1
        session.commit()

        return ToolResult(data={
            "executed": True,
            "code": project.code,
            "previous_status": previous,
            "new_status": args.new_status,
            "executed_by": user.user_id,
            "version": project.version,
        })


UPDATE_PROJECT_STATUS = ToolDefinition(
    name="update_project_status",
    description=(
        "Change a project's status. Requires human approval before execution."
    ),
    input_schema=UpdateStatusInput,
    sensitivity=Sensitivity.SENSITIVE,
    required_permissions=frozenset({Permission.PROJECTS_UPDATE_STATUS}),
    handler=update_project_status,
)