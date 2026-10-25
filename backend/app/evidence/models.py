from dataclasses import dataclass
from typing import Literal

EvidenceValue = float | bool | str
Method = Literal["api", "manual", "computed"]


@dataclass(frozen=True)
class EvidenceRecord:
    """One raw value behind an indicator, with where it came from."""

    country: str
    metric: str
    value: EvidenceValue
    unit: str
    year: int | None
    source_name: str
    source_url: str
    retrieved_at: str  # ISO 8601, UTC
    method: Method
