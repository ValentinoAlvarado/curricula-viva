from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..db import get_session
from ..models import Program, Syllabus, University
from ..schemas import ProgramIn

router = APIRouter(prefix="/programs", tags=["programs"])


@router.get("")
def listar(s: Session = Depends(get_session)) -> list[Program]:
    return s.exec(select(Program)).all()


@router.post("", status_code=201)
def crear(datos: ProgramIn, s: Session = Depends(get_session)) -> Program:
    if not s.get(University, datos.university_id):
        raise HTTPException(404, "universidad no encontrada")
    p = Program(**datos.model_dump())
    s.add(p)
    s.commit()
    s.refresh(p)
    return p


@router.get("/{pid}")
def obtener(pid: int, s: Session = Depends(get_session)) -> Program:
    p = s.get(Program, pid)
    if not p:
        raise HTTPException(404, "programa no encontrado")
    return p


@router.get("/{pid}/syllabi")
def silabos(pid: int, limit: int = 50, s: Session = Depends(get_session)) -> list[Syllabus]:
    if not s.get(Program, pid):
        raise HTTPException(404, "programa no encontrado")
    return s.exec(
        select(Syllabus).where(Syllabus.program_id == pid).limit(limit)
    ).all()
