from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..db import get_session
from ..ingest import descubrir_programas
from ..models import Program, University
from ..schemas import UniversityIn

router = APIRouter(prefix="/universities", tags=["universities"])


@router.get("")
def listar(s: Session = Depends(get_session)) -> list[University]:
    return s.exec(select(University)).all()


@router.post("", status_code=201)
def crear(datos: UniversityIn, s: Session = Depends(get_session)) -> University:
    if s.exec(select(University).where(University.code == datos.code)).first():
        raise HTTPException(409, f"Ya existe una institución con siglas {datos.code}")
    u = University(**datos.model_dump())
    s.add(u)
    s.commit()
    s.refresh(u)
    descubrir_programas(s, u)   # registra los planes disponibles
    return u


@router.get("/{uid}")
def obtener(uid: int, s: Session = Depends(get_session)) -> University:
    u = s.get(University, uid)
    if not u:
        raise HTTPException(404, "Institución no encontrada")
    return u


@router.get("/{uid}/programs")
def programas(uid: int, s: Session = Depends(get_session)) -> list[Program]:
    u = s.get(University, uid)
    if not u:
        raise HTTPException(404, "Institución no encontrada")
    # El descubrimiento es idempotente: se ejecuta siempre para incorporar
    # planes anadidos despues del alta de la institucion.
    descubrir_programas(s, u)
    return s.exec(select(Program).where(Program.university_id == uid)).all()


@router.post("/{uid}/discover", status_code=200)
def descubrir(uid: int, s: Session = Depends(get_session)) -> dict:
    """Registra los programas de los planes disponibles."""
    u = s.get(University, uid)
    if not u:
        raise HTTPException(404, "Institución no encontrada")
    return {"nuevos": descubrir_programas(s, u)}