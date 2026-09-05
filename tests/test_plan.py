"""Lector de planes de estudio: extraccion real de los tres planes FIEE."""

import re
import unicodedata
from pathlib import Path

import pymupdf
import pytest

RE_CURSO = re.compile(
    r"^([A-Z]{2,3}\d{2,3})\s+(.+?)\s+([OED])\s+([A-Z])?\s*"
    r"(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(.+)$", re.M)

PLANES = Path("/mnt/user-data/uploads")


def plano(t: str) -> str:
    """Sin tildes y en mayusculas: el plan las usa de forma inconsistente."""
    return "".join(c for c in unicodedata.normalize("NFD", t.upper())
                   if unicodedata.category(c) != "Mn")


def cursos(nombre: str):
    ruta = PLANES / f"PLAN-DE-ESTUDIOS-{nombre}.pdf"
    if not ruta.exists():
        pytest.skip(f"plan no disponible: {nombre}")
    t = "\n".join(p.get_text() for p in pymupdf.open(ruta))
    vistos, out = set(), []
    for m in RE_CURSO.finditer(t):
        cod = m.group(1)
        if cod in vistos:
            continue
        vistos.add(cod)
        out.append((cod, m.group(2).strip(),
                    int(m.group(5)) + int(m.group(6)) + int(m.group(7))))
    return out


def test_electrica_extrae_cursos():
    c = cursos("ELECTRICA")
    assert len(c) > 90
    assert any("MAQUINAS ELECTRICAS" in plano(x[1]) for x in c)


def test_electronica_extrae_cursos():
    c = cursos("ELECTRONICA")
    assert len(c) > 90
    assert any("COMUNICACIONES" in plano(x[1]) for x in c)


def test_telecom_extrae_cursos():
    c = cursos("TELECOM")
    assert len(c) > 90
    assert any("ANTENAS" in plano(x[1]) or "REDES" in plano(x[1])
               for x in c)


def test_mallas_son_distintas():
    """Cada carrera tiene asignaturas propias."""
    e = {x[1] for x in cursos("ELECTRICA")}
    n = {x[1] for x in cursos("ELECTRONICA")}
    t = {x[1] for x in cursos("TELECOM")}
    assert e - n - t, "Eléctrica debe tener cursos exclusivos"
    assert t - e - n, "Telecomunicaciones debe tener cursos exclusivos"


def test_horas_positivas():
    """Las horas salen del plan, no de una estimacion."""
    c = [x for x in cursos("ELECTRICA") if x[2] > 0]
    assert len(c) > 80
    assert all(0 < x[2] <= 12 for x in c)
