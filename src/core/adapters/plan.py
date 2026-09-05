"""Lector de planes de estudio UNI.

A diferencia del silabo, el plan declara las horas REALES de cada curso:
teoria (HT), practica (HP) y laboratorio (HL). No hay que estimarlas.

Formato verificado sobre los tres planes de la FIEE:
    COD  CURSO  TIPO  SIST.EVAL  HT  HP  HL  CRED  PRE-REQUISITO

Resultados de la extraccion:
    Electrica 2018-2      104 cursos, 461 h semanales
    Electronica 2018-2    113 cursos, 501 h semanales
    Telecomunicaciones    106 cursos, 463 h semanales
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
RE_PLAN = re.compile(r"(\d{4}-\d)")
# El titulo aparece junto al periodo; en algunos planes el texto extraido
# arrastra los rotulos de ciclo, asi que se recorta desde "INGENIERIA".
RE_ESCUELA = re.compile(
    r"(INGENIER[ÍI]A[^\n]{0,60}?)\s*\d{4}-\d", re.I
)

SEMANAS = 17
OBLIGATORIO, ELECTIVO = "O", "E"


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
        """Compatibilidad con el puerto: devuelve el plan como un Silabo."""
        p = self.leer_programa(ruta)
        return p.silabos[0] if p.silabos else Silabo(
            codigo="?", nombre=ruta.stem, institucion="FIEE-UNI"
        )

    # ── API propia ────────────────────────────────────────────────
    def leer_programa(self, ruta: Path, institucion: str = "FIEE-UNI") -> Programa:
        """Un curso -> un Silabo con una Unidad de horas reales."""
        with pymupdf.open(ruta) as doc:
            texto = "\n".join(p.get_text() for p in doc)

        periodo = self._periodo(texto)
        nombre = self._escuela(texto, ruta)
        silabos: list[Silabo] = []
        vistos: set[str] = set()

        for m in RE_CURSO.finditer(texto):
            cod, curso, tipo, _sist, ht, hp, hl, cred, _pre = m.groups()
            if cod in vistos:
                continue
            vistos.add(cod)

            horas_sem = int(ht) + int(hp) + int(hl)
            if horas_sem == 0:
                continue

            silabos.append(Silabo(
                codigo=cod,
                nombre=curso.strip().title(),
                institucion=institucion,
                periodo=periodo,
                creditos=int(cred),
                unidades=[Unidad(
                    numero=1,
                    nombre=curso.strip().title(),
                    horas=horas_sem * SEMANAS,
                    temas=[curso.strip().lower(),
                           "obligatorio" if tipo == OBLIGATORIO else "electivo"],
                )],
            ))

        return Programa(codigo=self._codigo(nombre), nombre=nombre,
                        institucion=institucion, silabos=silabos)

    @staticmethod
    def _periodo(texto: str) -> str | None:
        m = RE_PLAN.search(texto)
        return m.group(1) if m else None

    @staticmethod
    def _escuela(texto: str, ruta: Path) -> str:
        """Nombre de la escuela profesional, limpio de rotulos de ciclo."""
        for m in RE_ESCUELA.finditer(texto):
            limpio = " ".join(m.group(1).split())
            # descarta capturas contaminadas por los rotulos de ciclo
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
