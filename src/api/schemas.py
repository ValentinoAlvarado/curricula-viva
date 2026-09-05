"""DTOs de entrada y salida.

Nomenclatura de las metricas, deliberada:
  hours_associated  horas curriculares de las asignaturas asociadas a la
                    competencia. NO son horas faltantes.
  coverage          proporcion de cobertura estimada (0..1).
  severity          prioridad de revision (0..1), combina cobertura
                    horaria, correspondencia semantica y esencialidad.
"""

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
    stale: bool = False
    error: str | None = None


class GapOut(BaseModel):
    id: int
    rank: int
    competency: str
    essential: bool
    severity: float
    coverage: float               # 0..1
    hours_associated: int         # horas curriculares asociadas
    max_similarity: float
    occupations: list[str] = []   # perfiles ESCO que la requieren


class EvidenceCourse(BaseModel):
    """Asignatura de la malla que sostiene la competencia."""

    unit_id: int
    course_code: str
    course_name: str
    unit_name: str
    cycle: int | None = None      # None = electivo o no declarado
    mandatory: bool | None = None
    hours: int
    similarity: float


class EvidenceOut(BaseModel):
    gap_id: int
    competency: str
    severity: float
    coverage: float
    hours_associated: int
    essential: bool
    occupations: list[str] = []
    courses: list[EvidenceCourse] = []
    action: str = ""