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
Department = Literal[
    "operations", "hr", "finance", "legal", "procurement"
]
Priority = Literal["low", "medium", "high", "critical"]
SortBy = Literal["deadline", "priority", "code", "progress_percent"]


class QueryProjectsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Status | None = None
    department: Department | None = None
    priority: Priority | None = None
    sort_by: SortBy = "deadline"
    sort_order: Literal["asc", "desc"] = "asc"
    limit: int = Field(default=10, ge=1, le=50)


class GetProjectInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=3, max_length=32)


def _summary(project: Project) -> dict:
    return {
        "code": project.code,
        "name_en": project.name_en,
        "name_ar": project.name_ar,
        "status": project.status,
        "department": project.department,
        "priority": project.priority,
        "deadline": project.deadline.isoformat(),
        "progress_percent": project.progress_percent,
    }


def query_projects(args: QueryProjectsInput, user: UserContext) -> ToolResult:
    statement = select(Project)

    if args.status:
        statement = statement.where(Project.status == args.status)
    if args.department:
        statement = statement.where(Project.department == args.department)
    if args.priority:
        statement = statement.where(Project.priority == args.priority)

    column = getattr(Project, args.sort_by)
    statement = statement.order_by(
        column.desc() if args.sort_order == "desc" else column.asc()
    )

    with Session(engine) as session:
        total = len(session.scalars(statement).all())
        rows = session.scalars(statement.limit(args.limit)).all()

        return ToolResult(data={
            "projects": [_summary(p) for p in rows],
            "returned_count": len(rows),
            "total_matching": total,
            "truncated": total > len(rows),
            "filters_applied": args.model_dump(exclude_none=True),
        })


def get_project_details(args: GetProjectInput, user: UserContext) -> ToolResult:
    with Session(engine) as session:
        project = session.scalar(
            select(Project).where(Project.code == args.code.upper())
        )

        if project is None:
            return ToolResult(data={
                "found": False,
                "error_code": "PROJECT_NOT_FOUND",
                "code": args.code,
            })

        return ToolResult(data={
            "found": True,
            **_summary(project),
            "description": project.description,
            "owner_id": project.owner_id,
            "start_date": project.start_date.isoformat(),
            "budget_allocated": str(project.budget_allocated),
            "budget_spent": str(project.budget_spent),
            "version": project.version,
        })


QUERY_PROJECTS = ToolDefinition(
    name="query_projects",
    description=(
        "Find projects using structured filters. "
        "Only the listed filter values are accepted."
    ),
    input_schema=QueryProjectsInput,
    sensitivity=Sensitivity.READ,
    required_permissions=frozenset({Permission.PROJECTS_READ}),
    handler=query_projects,
)

GET_PROJECT_DETAILS = ToolDefinition(
    name="get_project_details",
    description="Retrieve the full record for one project by its code.",
    input_schema=GetProjectInput,
    sensitivity=Sensitivity.READ,
    required_permissions=frozenset({Permission.PROJECTS_READ}),
    handler=get_project_details,
)