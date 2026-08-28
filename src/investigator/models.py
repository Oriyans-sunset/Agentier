from pydantic import BaseModel
from typing import Literal

class Finding(BaseModel):
    column: str
    issue: str
    description: str
    evidence: dict
    severity: Literal["low", "medium", "high"]
    confidence: float
    potentially_safely_fixable: bool
    reasoning: str


class InvestigationResult(BaseModel):
    findings: list[Finding]