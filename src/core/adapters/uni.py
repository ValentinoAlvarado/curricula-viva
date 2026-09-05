import re
from pathlib import Path

import pymupdf

from ..domain.models import Silabo, Unidad
from .base import LectorSilabo

RE_COD   = re.compile(r'\b([A-Z]{2}-?\d{3})\b')
RE_CRED  = re.compile(r'CR[EÉ]DITOS\s*:?\s*(\d+)', re.I)
RE_CICLO = re.compile(r'CICLO\s*:?\s*([A-ZÁÉÍÓÚ]+)', re.I)
RE_CAP   = re.compile(r'^\s*Cap[íi]tulo\s+(\d+)\s*\.?-?\s*(.+)$', re.M | re.I)

import unicodedata

def _sin_tildes(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t)
                   if unicodedata.category(c) != "Mn")

class LectorUNI(LectorSilabo):
    clave = "uni"

    def acepta(self, ruta: Path) -> bool:
        """True si el PDF tiene la plantilla institucional UNI."""
        try:
            with pymupdf.open(ruta) as doc:
                if doc.page_count == 0:
                    return False
                cabecera = doc[0].get_text()[:1200].upper()
        except Exception:
            return False
        return "UNIVERSIDAD NACIONAL DE INGENIERIA" in _sin_tildes(cabecera) or \
               "INGENIERIA ELECTRICA" in _sin_tildes(cabecera)

    def leer(self, ruta: Path) -> Silabo:
        with pymupdf.open(ruta) as doc:
            texto = "\n".join(p.get_text() for p in doc)

        cod = RE_COD.search(texto)
        cred = RE_CRED.search(texto)
        ciclo = RE_CICLO.search(texto)

        return Silabo(
            codigo=cod.group(1).replace("-", "") if cod else ruta.stem,
            nombre=self._nombre(texto, ruta),
            institucion="FIEE-UNI",
            periodo="2017-2",
            creditos=int(cred.group(1)) if cred else None,
            unidades=self._unidades(texto, int(cred.group(1)) if cred else 3),
        )

    @staticmethod
    def _nombre(texto: str, ruta: Path) -> str:
        for linea in texto.splitlines():
            l = linea.strip()
            if len(l) > 5 and l.isupper() and not RE_COD.search(l):
                return l.title()
        return ruta.stem

    @staticmethod
    def _unidades(texto: str, creditos: int) -> list[Unidad]:
        caps = list(RE_CAP.finditer(texto))
        horas_curso = creditos * 17

        if not caps:
            return [Unidad(numero=1, nombre="CONTENIDO", horas=horas_curso,
                           temas=[t.strip() for t in texto.splitlines() if len(t.strip()) > 30][:20])]

        por_cap = max(1, horas_curso // len(caps))
        unidades = []
        for i, m in enumerate(caps):
            fin = caps[i + 1].start() if i + 1 < len(caps) else len(texto)
            cuerpo = texto[m.end():fin]
            temas = [t.strip() for t in cuerpo.splitlines() if len(t.strip()) > 10]
            unidades.append(Unidad(numero=int(m.group(1)), nombre=m.group(2).strip(),
                                   horas=por_cap, temas=temas[:15]))
        return unidades