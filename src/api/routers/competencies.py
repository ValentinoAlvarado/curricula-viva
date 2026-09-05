from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session, col, select

from ..db import get_session
from ..models import EscoCompetency

router = APIRouter(prefix="/competencies", tags=["competencies"])


@router.get("")
def listar(q: str | None = None, essential: bool | None = None,
           limit: int = 50, offset: int = 0,
           s: Session = Depends(get_session)) -> list[EscoCompetency]:
    consulta = select(EscoCompetency)
    if q:
        consulta = consulta.where(col(EscoCompetency.label).contains(q))
    if essential is not None:
        consulta = consulta.where(EscoCompetency.essential == essential)
    return s.exec(
        consulta.order_by(col(EscoCompetency.occupation_count).desc())
        .offset(offset).limit(limit)
    ).all()
