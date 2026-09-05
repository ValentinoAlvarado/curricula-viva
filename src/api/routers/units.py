from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..db import get_session
from ..models import LearningUnit

router = APIRouter(prefix="/units", tags=["units"])


@router.get("")
def listar(limit: int = 50, offset: int = 0,
           s: Session = Depends(get_session)) -> list[LearningUnit]:
    return s.exec(select(LearningUnit).offset(offset).limit(limit)).all()


@router.get("/{uid}")
def obtener(uid: int, s: Session = Depends(get_session)) -> LearningUnit:
    u = s.get(LearningUnit, uid)
    if not u:
        raise HTTPException(404, "unidad no encontrada")
    return u
