"""Tablas del dominio de negocio.

Los embeddings viven en artifacts/*.npz. La base persiste datos de
negocio y resultados de analisis, no vectores.

Cada Analysis registra la version del algoritmo que lo produjo.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlmodel import JSON, Column, Field, SQLModel


class EstadoAnalisis(str, Enum):
    running = "running"
    completed = "completed"
    failed = "failed"


class University(SQLModel, table=True):
    __tablename__ = "universities"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    code: str = Field(index=True, unique=True)
    country: str = "PE"


class Program(SQLModel, table=True):
    __tablename__ = "programs"

    id: int | None = Field(default=None, primary_key=True)
    university_id: int = Field(foreign_key="universities.id", index=True)
    name: str
    code: str = Field(index=True)
    plan_period: str | None = None


class Syllabus(SQLModel, table=True):
    """Asignatura del plan. ciclo y tipo provienen del documento."""

    __tablename__ = "syllabi"

    id: int | None = Field(default=None, primary_key=True)
    program_id: int = Field(foreign_key="programs.id", index=True)
    code: str = Field(index=True)
    name: str
    credits: int | None = None
    period: str | None = None
    cycle: int | None = None          # 1..10; None si es electivo
    mandatory: bool | None = None     # None si el plan no lo declara
    source_path: str | None = None


class LearningUnit(SQLModel, table=True):
    __tablename__ = "learning_units"

    id: int | None = Field(default=None, primary_key=True)
    syllabus_id: int = Field(foreign_key="syllabi.id", index=True)
    number: int
    name: str
    hours: int
    topics: list[str] = Field(default_factory=list, sa_column=Column(JSON))


class EscoCompetency(SQLModel, table=True):
    __tablename__ = "esco_competencies"

    id: int | None = Field(default=None, primary_key=True)
    uri: str = Field(index=True, unique=True)
    label: str = Field(index=True)
    skill_type: str = ""
    essential: bool = False
    occupation_count: int = 0
    # Ocupaciones que la requieren, separadas por "|". Fuente: ESCO.
    occupations: str = ""


class Analysis(SQLModel, table=True):
    __tablename__ = "analyses"

    id: int | None = Field(default=None, primary_key=True)
    program_id: int = Field(foreign_key="programs.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: EstadoAnalisis = EstadoAnalisis.running
    threshold: float = 0.35
    floor: float = 0.55
    weighted: bool = True
    artifact_hash: str | None = None
    engine_version: str = ""
    error: str | None = None


class Gap(SQLModel, table=True):
    """Cobertura de una competencia por la malla.

    hours_covered NO son horas faltantes: son las horas curriculares de
    las asignaturas asociadas a la competencia por encima del umbral.
    """

    __tablename__ = "gaps"

    id: int | None = Field(default=None, primary_key=True)
    analysis_id: int = Field(foreign_key="analyses.id", index=True)
    competency_id: int = Field(foreign_key="esco_competencies.id", index=True)
    severity: float
    coverage: float = 0.0        # 0..1, proporcion de cobertura estimada
    hours_covered: int           # horas curriculares asociadas
    max_similarity: float
    rank: int


class Match(SQLModel, table=True):
    """Par (unidad, competencia) por encima del umbral. Da trazabilidad."""

    __tablename__ = "curriculum_competency_matches"

    id: int | None = Field(default=None, primary_key=True)
    analysis_id: int = Field(foreign_key="analyses.id", index=True)
    unit_id: int = Field(foreign_key="learning_units.id", index=True)
    competency_id: int = Field(foreign_key="esco_competencies.id", index=True)
    similarity: float