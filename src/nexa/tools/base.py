from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from pydantic import BaseModel

from nexa.auth.dependencies import UserContext
from nexa.auth.permissions import Permission


class Sensitivity(StrEnum):
    READ = "read"
    SENSITIVE = "sensitive"


class ToolError(BaseModel):
    ok: bool = False
    error_code: str
    message: str


class ToolResult(BaseModel):
    ok: bool = True
    data: dict[str, Any]


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    input_schema: type[BaseModel]
    sensitivity: Sensitivity
    required_permissions: frozenset[Permission]
    handler: Callable[[BaseModel, UserContext], ToolResult]

    @property
    def requires_approval(self) -> bool:
        return self.sensitivity is Sensitivity.SENSITIVE