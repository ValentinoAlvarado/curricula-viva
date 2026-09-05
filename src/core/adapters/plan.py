"""Lector de planes de estudio UNI.

El plan declara las horas REALES de cada curso: teoria (HT), practica (HP)
y laboratorio (HL). Tambien el ciclo y si el curso es obligatorio o
electivo. Nada de eso se estima.

Estructura verificada sobre los tres planes de la FIEE: diez bloques de
tabla, uno por ciclo, seguidos de un bloque de electivos.

    Electrica 2018-2      104 cursos | 10 ciclos + 55 electivos
    Electronica 2018-2    112 cursos | 10 ciclos + 66 electivos
    Telecomunicaciones    106 cursos | 10 ciclos + 58 electivos
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pymupdf

from ..domain.models import Programa, Silabo, Unidad
from .base import LectorSilabo

RE_CURSO = re.compile(
    r"^([A-Z]{2,3}\d{2,3})\s+(.+?)\s+([OED])\s+([A-Z])?\s*"
    r"(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(.+)$",
    re.M,
)
RE_CABECERA = re.compile(r"^COD\s+CURSO\s+TIPO", re.M)
RE_PLAN = re.compile(r"(\d{4}-\d)")
RE_ESCUELA = re.compile(r"(INGENIER[ÍI]A[^\n]{0,60}?)\s*\d{4}-\d", re.I)

SEMANAS = 17
CICLOS_MALLA = 10
OBLIGATORIO = "O"


def _sin_tildes(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t)
                   if unicodedata.category(c) != "Mn")


class LectorPlanUNI(LectorSilabo):
    """Plan de estudios completo de una escuela profesional."""

    clave = "plan-uni"

    def acepta(self, ruta: Path) -> bool:
        try:
            with pymupdf.open(ruta) as doc:
                if doc.page_count == 0:
                    return False
                t = _sin_tildes(doc[0].get_text()[:3000]).upper()
        except Exception:
            return False
        return "PLAN DE ESTUDIOS" in t and "PRE-REQUISITO" in t

    def leer(self, ruta: Path) -> Silabo:
        p = self.leer_programa(ruta)
        return p.silabos[0] if p.silabos else Silabo(
            codigo="?", nombre=ruta.stem, institucion="FIEE-UNI")

    # ── API propia ────────────────────────────────────────────────
    def leer_programa(self, ruta: Path, institucion: str = "FIEE-UNI") -> Programa:
        """Un curso -> un Silabo con ciclo, tipo y horas reales."""
        with pymupdf.open(ruta) as doc:
            texto = "\n".join(p.get_text() for p in doc)

        periodo = self._periodo(texto)
        nombre = self._escuela(texto, ruta)
        silabos: list[Silabo] = []
        vistos: set[str] = set()

        for ciclo, bloque in self._bloques(texto):
            for m in RE_CURSO.finditer(bloque):
                cod, curso, tipo, _sist, ht, hp, hl, cred, _pre = m.groups()
                if cod in vistos:
                    continue
                vistos.add(cod)

                horas_sem = int(ht) + int(hp) + int(hl)
                if horas_sem == 0:
                    continue

                obligatorio = tipo == OBLIGATORIO
                silabos.append(Silabo(
                    codigo=cod,
                    nombre=curso.strip().title(),
                    institucion=institucion,
                    periodo=periodo,
                    creditos=int(cred),
                    ciclo=ciclo,
                    obligatorio=obligatorio,
                    unidades=[Unidad(
                        numero=1,
                        nombre=curso.strip().title(),
                        horas=horas_sem * SEMANAS,
                        temas=[curso.strip().lower()],
                    )],
                ))

        return Programa(codigo=self._codigo(nombre), nombre=nombre,
                        institucion=institucion, silabos=silabos)

    @staticmethod
    def _bloques(texto: str) -> list[tuple[int | None, str]]:
        """Divide el plan en sus tablas.

        Los diez primeros bloques son los ciclos 1..10 en orden; el resto
        son cursos electivos, que no pertenecen a un ciclo fijo.
        """
        inicios = [m.start() for m in RE_CABECERA.finditer(texto)]
        if not inicios:
            return [(None, texto)]

        out: list[tuple[int | None, str]] = []
        for i, ini in enumerate(inicios):
            fin = inicios[i + 1] if i + 1 < len(inicios) else len(texto)
            ciclo = i + 1 if i < CICLOS_MALLA else None
            out.append((ciclo, texto[ini:fin]))
        return out

    @staticmethod
    def _periodo(texto: str) -> str | None:
        m = RE_PLAN.search(texto)
        return m.group(1) if m else None

    @staticmethod
    def _escuela(texto: str, ruta: Path) -> str:
        for m in RE_ESCUELA.finditer(texto):
            limpio = " ".join(m.group(1).split())
            if _sin_tildes(limpio).upper().count("CICLO"):
                continue
            if 8 < len(limpio) < 60:
                return limpio.title()
        base = ruta.stem.replace("PLAN-DE-ESTUDIOS-", "").replace("-", " ")
        return f"Ingeniería {base.title()}"

    @staticmethod
    def _codigo(nombre: str) -> str:
        plano = _sin_tildes(nombre).upper()
        for clave, cod in (("ELECTRICA", "IE"), ("ELECTRONICA", "IEL"),
                           ("TELECOM", "ITC"), ("MECANICA", "IM"),
                           ("SISTEMAS", "IS"), ("CIVIL", "IC")):
            if clave in plano:
                return cod
        return "".join(w[0] for w in plano.split()[:3]) or "PRG"