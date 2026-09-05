from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..db import get_session
from ..models import LearningUnit, Syllabus

router = APIRouter(prefix="/syllabi", tags=["syllabi"])


@router.get("/{sid}")
def obtener(sid: int, s: Session = Depends(get_session)) -> Syllabus:
    x = s.get(Syllabus, sid)
    if not x:
        raise HTTPException(404, "silabo no encontrado")
    return x


@router.get("/{sid}/units")
def unidades(sid: int, s: Session = Depends(get_session)) -> list[LearningUnit]:
    if not s.get(Syllabus, sid):
        raise HTTPException(404, "silabo no encontrado")
    return s.exec(
        select(LearningUnit).where(LearningUnit.syllabus_id == sid)
    ).all()
