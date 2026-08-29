from enum import StrEnum


class Role(StrEnum):
    EMPLOYEE = "employee"
    MANAGER = "manager"
    DIRECTOR = "director"


class Permission(StrEnum):
    KB_READ = "kb:read"
    PROJECTS_READ = "projects:read"
    PROJECTS_SUMMARIZE = "projects:summarize"
    PROJECTS_UPDATE_STATUS = "projects:update_status"
    APPROVALS_DECIDE = "approvals:decide"
    AUDIT_READ = "audit:read"


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.EMPLOYEE: frozenset({
        Permission.KB_READ,
        Permission.PROJECTS_READ,
    }),
    Role.MANAGER: frozenset({
        Permission.KB_READ,
        Permission.PROJECTS_READ,
        Permission.PROJECTS_SUMMARIZE,
        Permission.PROJECTS_UPDATE_STATUS,
    }),
    Role.DIRECTOR: frozenset({
        Permission.KB_READ,
        Permission.PROJECTS_READ,
        Permission.PROJECTS_SUMMARIZE,
        Permission.PROJECTS_UPDATE_STATUS,
        Permission.APPROVALS_DECIDE,
        Permission.AUDIT_READ,
    }),
}


def has_permission(role: Role, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, frozenset())