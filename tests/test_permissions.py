import pytest

from nexa.auth.permissions import Permission, Role, has_permission

P = Permission
R = Role

EXPECTED: dict[tuple[Role, Permission], bool] = {
    (R.EMPLOYEE, P.KB_READ): True,
    (R.EMPLOYEE, P.PROJECTS_READ): True,
    (R.EMPLOYEE, P.PROJECTS_SUMMARIZE): False,
    (R.EMPLOYEE, P.PROJECTS_UPDATE_STATUS): False,
    (R.EMPLOYEE, P.APPROVALS_DECIDE): False,
    (R.EMPLOYEE, P.AUDIT_READ): False,

    (R.MANAGER, P.KB_READ): True,
    (R.MANAGER, P.PROJECTS_READ): True,
    (R.MANAGER, P.PROJECTS_SUMMARIZE): True,
    (R.MANAGER, P.PROJECTS_UPDATE_STATUS): True,
    (R.MANAGER, P.APPROVALS_DECIDE): False,
    (R.MANAGER, P.AUDIT_READ): False,

    (R.DIRECTOR, P.KB_READ): True,
    (R.DIRECTOR, P.PROJECTS_READ): True,
    (R.DIRECTOR, P.PROJECTS_SUMMARIZE): True,
    (R.DIRECTOR, P.PROJECTS_UPDATE_STATUS): True,
    (R.DIRECTOR, P.APPROVALS_DECIDE): True,
    (R.DIRECTOR, P.AUDIT_READ): True,
}


@pytest.mark.parametrize(("pair", "allowed"), EXPECTED.items())
def test_permission_matrix(pair: tuple[Role, Permission], allowed: bool) -> None:
    role, permission = pair
    assert has_permission(role, permission) is allowed


def test_matrix_covers_every_combination() -> None:
    assert len(EXPECTED) == len(Role) * len(Permission)


def test_manager_cannot_approve_own_requests() -> None:
    assert has_permission(R.MANAGER, P.PROJECTS_UPDATE_STATUS) is True
    assert has_permission(R.MANAGER, P.APPROVALS_DECIDE) is False


def test_unknown_role_is_denied_everything() -> None:
    for permission in Permission:
        assert has_permission("ghost", permission) is False