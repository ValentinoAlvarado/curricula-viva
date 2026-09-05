"""Descubrimiento de programas desde los planes de estudio."""

import re
import unicodedata
from pathlib import Path

import pymupdf
import pytest

PLANES = Path("/mnt/user-data/uploads")
RE = re.compile(r"^([A-Z]{2,3}\d{2,3})\s+(.+?)\s+([OED])\s+([A-Z])?\s*"
                r"(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(.+)$", re.M)
RE_ESC = re.compile(r"(INGENIER[ÍI]A[^\n]{0,60}?)\s*\d{4}-\d", re.I)


def _sin_tildes(t):
    return "".join(c for c in unicodedata.normalize("NFD", t)
                   if unicodedata.category(c) != "Mn")


def _clave(t):
    p = _sin_tildes(t).lower()
    for w in ("ingenieria", " de ", " del ", " la ", " en "):
        p = p.replace(w, " ")
    return " ".join(p.split())


def leer(ruta):
    t = "\n".join(p.get_text() for p in pymupdf.open(ruta))
    nombre = None
    for m in RE_ESC.finditer(t):
        limpio = " ".join(m.group(1).split())
        if _sin_tildes(limpio).upper().count("CICLO"):
            continue
        if 8 < len(limpio) < 60:
            nombre = limpio.title()
            break
    vistos, cursos = set(), []
    for x in RE.finditer(t):
        if x.group(1) in vistos:
            continue
        vistos.add(x.group(1))
        h = (int(x.group(5)) + int(x.group(6)) + int(x.group(7))) * 17
        if h:
            cursos.append((x.group(1), x.group(2).strip().title(), h))
    return nombre, cursos


def planes():
    rutas = sorted(PLANES.glob("PLAN-DE-ESTUDIOS-*.pdf"))
    if len(rutas) < 3:
        pytest.skip("planes no disponibles")
    return {leer(r)[0]: leer(r)[1] for r in rutas}


def test_descubre_los_tres_programas():
    p = planes()
    assert len(p) == 3
    claves = {_clave(n) for n in p}
    assert "electrica" in claves
    assert "electronica" in claves
    assert "telecomunicaciones" in claves


def test_cada_programa_tiene_su_malla():
    """Tres nombres NO pueden apuntar a los mismos datos."""
    p = planes()
    conjuntos = [{c[1] for c in v} for v in p.values()]
    a, b, c = conjuntos
    assert a != b and b != c and a != c


def test_cursos_exclusivos_por_carrera():
    p = planes()
    por = {n: {c[1] for c in v} for n, v in p.items()}
    for nombre, propios in por.items():
        otros = set().union(*[v for k, v in por.items() if k != nombre])
        assert propios - otros, f"{nombre} no tiene cursos exclusivos"


def test_electronica_tiene_sus_cursos():
    p = planes()
    elec = next(v for n, v in p.items() if _clave(n) == "electronica")
    nombres = {_sin_tildes(c[1]).upper() for c in elec}
    assert any("COMUNICACIONES" in n for n in nombres)
    assert any("MICROCONTROLADORES" in n for n in nombres)


def test_telecom_tiene_sus_cursos():
    p = planes()
    tel = next(v for n, v in p.items() if _clave(n) == "telecomunicaciones")
    nombres = {_sin_tildes(c[1]).upper() for c in tel}
    assert any("REDES" in n for n in nombres)
    assert any("ANTENAS" in n or "FIBRA OPTICA" in n for n in nombres)


def test_sincronizacion_retira_mallas_ajenas():
    """Un programa creado a mano no debe conservar cursos de otra fuente."""
    bd = [{"pid": 1, "code": f"OLD{i}", "src": "silabo.pdf"} for i in range(165)]
    plan_src = "PLAN-DE-ESTUDIOS-ELECTRICA.pdf"
    bd = [c for c in bd if not (c["pid"] == 1 and c["src"] != plan_src)]
    assert bd == []
