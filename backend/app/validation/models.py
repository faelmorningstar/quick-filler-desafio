from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class WarningSeverity(str, Enum):
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class ValidationWarning:
    """
    Representa um problema derivado da transcrição.

    Os avisos não fazem parte do JSON original do documento.
    São calculados posteriormente para revisão e exportação.
    """

    code: str
    message: str
    page: int
    row: int | None = None
    severity: WarningSeverity = WarningSeverity.WARNING