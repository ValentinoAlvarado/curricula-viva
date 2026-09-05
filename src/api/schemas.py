"""DTOs de entrada y salida. Separados de las tablas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class UniversityIn(BaseModel):
    name: str
    code: str
    country: str = "PE"


class ProgramIn(BaseModel):
    university_id: int
    name: str
    code: str
    plan_period: str | None = None


class AnalysisIn(BaseModel):
    program_id: int
    threshold: float = 0.35
    floor: float = 0.55
    weighted: bool = True


class AnalysisOut(BaseModel):
    id: int
    program_id: int
    status: str
    created_at: datetime
    threshold: float
    floor: float
    weighted: bool
    n_gaps: int = 0
    engine_version: str = ""
    stale: bool = False           # calculado con una version anterior
    error: str | None = None


class GapOut(BaseModel):
    id: int
    rank: int
    competency: str
    essential: bool
    severity: float
    hours_covered: int
    max_similarity: float


class EvidenceUnit(BaseModel):
    """Unidad curricular que sostiene una brecha. Trazabilidad."""

    unit_id: int
    unit_name: str
    syllabus_code: str
    syllabus_name: str
    hours: int
    similarity: float


class EvidenceOut(BaseModel):
    gap_id: int
    competency: str
    severity: float
    hours_covered: int
    units: list[EvidenceUnit]