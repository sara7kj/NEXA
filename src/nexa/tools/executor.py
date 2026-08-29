import logging

from pydantic import ValidationError

from nexa.auth.dependencies import UserContext
from nexa.auth.permissions import has_permission
from nexa.tools.base import ToolDefinition, ToolError, ToolResult

logger = logging.getLogger(__name__)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        if tool.name in self._tools:
            raise ValueError(f"tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def names(self) -> list[str]:
        return sorted(self._tools)


registry = ToolRegistry()


def execute_tool(
    name: str,
    raw_arguments: dict,
    user: UserContext,
    approval_granted: bool = False,
) -> ToolResult | ToolError:
    # 1. tool must exist
    tool = registry.get(name)
    if tool is None:
        return ToolError(error_code="UNKNOWN_TOOL", message=f"no such tool: {name}")

    # 2. arguments must validate against the strict schema
    try:
        arguments = tool.input_schema(**raw_arguments)
    except ValidationError as exc:
        return ToolError(
            error_code="INVALID_ARGUMENTS",
            message=exc.errors()[0].get("msg", "invalid arguments"),
        )

    # 3. identity comes from UserContext only - never from raw_arguments

    # 4. permissions
    missing = [
        p.value for p in tool.required_permissions
        if not has_permission(user.role, p)
    ]
    if missing:
        logger.warning(
            "permission denied: user=%s role=%s tool=%s missing=%s",
            user.user_id, user.role.value, name, missing,
        )
        return ToolError(
            error_code="PERMISSION_DENIED",
            message=f"missing permission: {missing[0]}",
        )

    # 5. sensitive tools require an approval record
    if tool.requires_approval and not approval_granted:
        return ToolError(
            error_code="APPROVAL_REQUIRED",
            message=f"{name} requires human approval before execution",
        )

    # 6. execute
    try:
        return tool.handler(arguments, user)
    except Exception:
        logger.exception("tool execution failed: %s", name)
        return ToolError(
            error_code="EXECUTION_FAILED",
            message="the tool failed to execute",
        )