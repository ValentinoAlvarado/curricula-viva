"""Ejecucion y consulta de analisis, con evidencia interpretable."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, col, func, select

from core.pipeline.matching import VERSION as MOTOR

from ..db import get_session
from ..ingest import ejecutar_analisis, ingerir_competencias
from ..models import (
    Analysis,
    EscoCompetency,
    Gap,
    LearningUnit,
    Match,
    Program,
    Syllabus,
)
from ..schemas import (
    AnalysisIn,
    AnalysisOut,
    EvidenceCourse,
    EvidenceOut,
    GapOut,
)

router = APIRouter(tags=["analyses"])
MAX_OCUPACIONES = 5


def _ocupaciones(c: EscoCompetency) -> list[str]:
    if not c.occupations:
        return []
    return [o for o in c.occupations.split("|") if o][:MAX_OCUPACIONES]


def _accion(g: Gap, esencial: bool, n_cursos: int) -> str:
    """Accion sugerida a partir de la cobertura medida."""
    if n_cursos == 0:
        return ("Ninguna asignatura del plan aborda esta competencia por "
                "encima del umbral. Evaluar su incorporación en un curso "
                "existente o la creación de contenido nuevo.")
    grado = "esencial" if esencial else "complementaria"
    if g.coverage < 0.35:
        return (f"Cobertura baja ({g.coverage:.0%}) para una competencia "
                f"{grado}. Revisar la profundidad del tratamiento en las "
                "asignaturas indicadas.")
    if g.coverage < 0.6:
        return (f"Cobertura parcial ({g.coverage:.0%}). Contrastar el nivel "
                "alcanzado con el que exige el perfil ocupacional.")
    return (f"Cobertura suficiente ({g.coverage:.0%}). Sin acción requerida "
            "en este ciclo.")


def _salida(a: Analysis, s: Session) -> AnalysisOut:
    n = s.exec(
        select(func.count()).select_from(Gap).where(Gap.analysis_id == a.id)
    ).one()
    return AnalysisOut(
        id=a.id, program_id=a.program_id, status=a.status.value,
        created_at=a.created_at, threshold=a.threshold, floor=a.floor,
        weighted=a.weighted, n_gaps=n, engine_version=a.engine_version,
        stale=(a.engine_version != MOTOR), error=a.error,
    )


@router.post("/analyses", status_code=201)
def crear(datos: AnalysisIn, s: Session = Depends(get_session)) -> AnalysisOut:
    programa = s.get(Program, datos.program_id)
    if not programa:
        raise HTTPException(404, "Programa no encontrado")

    a = Analysis(**datos.model_dump(), engine_version=MOTOR)
    s.add(a)
    s.commit()
    s.refresh(a)

    ingerir_competencias(s)
    ejecutar_analisis(s, a, programa)
    s.refresh(a)
    return _salida(a, s)


@router.get("/analyses")
def listar(program_id: int | None = None, vigentes: bool = False,
           s: Session = Depends(get_session)) -> list[AnalysisOut]:
    consulta = select(Analysis)
    if program_id is not None:
        consulta = consulta.where(Analysis.program_id == program_id)
    if vigentes:
        consulta = consulta.where(Analysis.engine_version == MOTOR)
    return [_salida(a, s) for a in s.exec(consulta).all()]


@router.get("/engine")
def motor() -> dict:
    return {"version": MOTOR}


@router.get("/analyses/{aid}")
def obtener(aid: int, s: Session = Depends(get_session)) -> AnalysisOut:
    a = s.get(Analysis, aid)
    if not a:
        raise HTTPException(404, "Análisis no encontrado")
    return _salida(a, s)


@router.get("/analyses/{aid}/gaps")
def brechas(aid: int, top: int = 15, min_severity: float = 0.0,
            s: Session = Depends(get_session)) -> list[GapOut]:
    if not s.get(Analysis, aid):
        raise HTTPException(404, "Análisis no encontrado")

    filas = s.exec(
        select(Gap, EscoCompetency)
        .join(EscoCompetency, col(Gap.competency_id) == col(EscoCompetency.id))
        .where(Gap.analysis_id == aid, Gap.severity >= min_severity)
        .order_by(col(Gap.rank))
        .limit(top)
    ).all()

    return [
        GapOut(
            id=g.id, rank=g.rank, competency=c.label, essential=c.essential,
            severity=g.severity, coverage=g.coverage,
            hours_associated=g.hours_covered,
            max_similarity=g.max_similarity, occupations=_ocupaciones(c),
        )
        for g, c in filas
    ]


@router.get("/gaps/{gid}/evidence")
def evidencia(gid: int, s: Session = Depends(get_session)) -> EvidenceOut:
    """Trazabilidad completa: asignaturas, ciclo, tipo y perfiles."""
    g = s.get(Gap, gid)
    if not g:
        raise HTTPException(404, "Brecha no encontrada")
    comp = s.get(EscoCompetency, g.competency_id)

    filas = s.exec(
        select(Match, LearningUnit, Syllabus)
        .join(LearningUnit, col(Match.unit_id) == col(LearningUnit.id))
        .join(Syllabus, col(LearningUnit.syllabus_id) == col(Syllabus.id))
        .where(Match.analysis_id == g.analysis_id,
               Match.competency_id == g.competency_id)
        .order_by(col(Match.similarity).desc())
    ).all()

    cursos = [
        EvidenceCourse(
            unit_id=u.id, course_code=sy.code, course_name=sy.name,
            unit_name=u.name, cycle=sy.cycle, mandatory=sy.mandatory,
            hours=u.hours, similarity=m.similarity,
        )
        for m, u, sy in filas
    ]

    return EvidenceOut(
        gap_id=g.id, competency=comp.label, severity=g.severity,
        coverage=g.coverage, hours_associated=g.hours_covered,
        essential=comp.essential, occupations=_ocupaciones(comp),
        courses=cursos, action=_accion(g, comp.essential, len(cursos)),
    )