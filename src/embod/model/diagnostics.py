from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from embod.model.schema import SchemaModel


class DiagnosticLevel(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(slots=True, frozen=True)
class Diagnostic(SchemaModel):
    code: str
    level: DiagnosticLevel
    message: str
    subject: str | None = None
    hint: str | None = None


@dataclass(slots=True, frozen=True)
class DiagnosticsReport(SchemaModel):
    schema_version: str = "embod.diagnostics.v1"
    diagnostics: list[Diagnostic] | tuple[Diagnostic, ...] = ()

    @property
    def has_errors(self) -> bool:
        return any(item.level == DiagnosticLevel.ERROR for item in self.diagnostics)
