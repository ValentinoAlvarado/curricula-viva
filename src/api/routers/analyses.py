"""Ejecucion y consulta de analisis, con trazabilidad.

Un analisis calculado con una version anterior del algoritmo se marca
como obsoleto. La aplicacion lo detecta y recalcula.
"""

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
from ..schemas import AnalysisIn, AnalysisOut, EvidenceOut, EvidenceUnit, GapOut

router = APIRouter(tags=["analyses"])


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
            severity=g.severity, hours_covered=g.hours_covered,
            max_similarity=g.max_similarity,
        )
        for g, c in filas
    ]


@router.get("/gaps/{gid}/evidence")
def evidencia(gid: int, s: Session = Depends(get_session)) -> EvidenceOut:
    """Trazabilidad: cursos que sostienen la brecha."""
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

    return EvidenceOut(
        gap_id=g.id, competency=comp.label, severity=g.severity,
        hours_covered=g.hours_covered,
        units=[
            EvidenceUnit(
                unit_id=u.id, unit_name=u.name, syllabus_code=sy.code,
                syllabus_name=sy.name, hours=u.hours, similarity=m.similarity,
            )
            for m, u, sy in filas
        ],
    )