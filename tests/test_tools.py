import pytest

from nexa.auth.dependencies import UserContext
from nexa.auth.permissions import Role
from nexa.tools import execute_tool

LAYLA = UserContext("u-layla", Role.EMPLOYEE, "Layla")
OMAR = UserContext("u-omar", Role.MANAGER, "Omar")
HUDA = UserContext("u-huda", Role.DIRECTOR, "Huda")

VALID_UPDATE = {
    "code": "PRJ-001",
    "new_status": "on_hold",
    "reason": "vendor contract delayed by three weeks",
    "expected_current_status": "active",
}


def test_unknown_tool_is_rejected() -> None:
    result = execute_tool("drop_everything", {}, LAYLA)
    assert result.error_code == "UNKNOWN_TOOL"


def test_invalid_enum_value_is_rejected() -> None:
    result = execute_tool("query_projects", {"status": "deleted"}, LAYLA)
    assert result.error_code == "INVALID_ARGUMENTS"


@pytest.mark.parametrize(
    "injection",
    [
        {"sql": "DROP TABLE projects"},
        {"where": "1=1"},
        {"filter_expression": "true"},
        {"status": "active", "sql": "DELETE FROM users"},
    ],
)
def test_sql_injection_fields_are_structurally_impossible(injection: dict) -> None:
    result = execute_tool("query_projects", injection, LAYLA)
    assert result.error_code == "INVALID_ARGUMENTS"


def test_model_cannot_supply_its_own_identity() -> None:
    result = execute_tool(
        "query_projects",
        {"status": "active", "user_role": "director", "user_id": "u-huda"},
        LAYLA,
    )
    assert result.error_code == "INVALID_ARGUMENTS"


def test_employee_cannot_request_status_change() -> None:
    result = execute_tool("update_project_status", VALID_UPDATE, LAYLA)
    assert result.error_code == "PERMISSION_DENIED"


def test_manager_with_permission_still_requires_approval() -> None:
    result = execute_tool("update_project_status", VALID_UPDATE, OMAR)
    assert result.error_code == "APPROVAL_REQUIRED"


def test_director_is_not_exempt_from_approval() -> None:
    result = execute_tool("update_project_status", VALID_UPDATE, HUDA)
    assert result.error_code == "APPROVAL_REQUIRED"


def test_read_tools_need_no_approval() -> None:
    result = execute_tool("query_projects", {"status": "active"}, LAYLA)
    assert result.ok is True


def test_query_returns_only_matching_projects() -> None:
    result = execute_tool("query_projects", {"status": "delayed"}, LAYLA)
    assert all(p["status"] == "delayed" for p in result.data["projects"])


def test_limit_is_capped() -> None:
    result = execute_tool("query_projects", {"limit": 999}, LAYLA)
    assert result.error_code == "INVALID_ARGUMENTS"


def test_missing_project_returns_structured_error() -> None:
    result = execute_tool("get_project_details", {"code": "PRJ-999"}, LAYLA)
    assert result.ok is True
    assert result.data["found"] is False
    assert result.data["error_code"] == "PROJECT_NOT_FOUND"