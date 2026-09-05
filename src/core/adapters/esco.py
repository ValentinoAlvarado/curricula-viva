"""Fuente de demanda: ESCO v1.2.1 (es).

Dos trampas del dataset, verificadas:
  - occupationSkillRelations_es.csv trae etiquetas en INGLES pese al
    sufijo _es. Hay que unir por URI contra los otros dos archivos.
  - Las etiquetas traen ambos generos separados por "/". Se corta antes
    de encodear para no contaminar el vector.
"""

from __future__ import annotations

import csv
from pathlib import Path

from ..domain.models import Competencia


def _primera_forma(etiqueta: str) -> str:
    """'ingeniero X/ingeniera X' -> 'ingeniero X'."""
    return etiqueta.split("/")[0].strip()


class FuenteESCO:
    """Ocupacion -> competencias requeridas, filtrado por dominio."""

    clave = "esco"

    DOMINIO = (
        "eléctric", "electric", "electrón", "electron", "electrotec",
        "energí", "energi", "potencia", "fotovoltaic", "eólic", "eolic",
        "automatiz", "mecatrón", "mecatron", "robótic", "robotic",
        "telecomunicac", "instrumentac", "domótic", "domotic",
        "control de procesos", "sistemas de control", "ingeniero de control",
    )

    EXCLUIR = (
        "calidad", "plagas", "tráfico aéreo", "trafico aereo",
        "textil", "cuero", "calzado", "ropa", "alimentari",
        "buque", "naval", "marítim", "maritim", "aduaner",
    )

    def ocupaciones(self) -> dict[str, str]:
        """uri -> etiqueta, restringido al dominio y sin falsos positivos."""
        res = {}
        for r in self._leer("occupations_es.csv"):
            etq = r["preferredLabel"].lower()
            if any(x in etq for x in self.EXCLUIR):
                continue
            if any(k in etq for k in self.dominio):
                res[r["conceptUri"]] = _primera_forma(r["preferredLabel"])
        return res

    def __init__(self, base: Path, dominio: tuple[str, ...] | None = None) -> None:
        self.base = Path(base)
        self.dominio = tuple(d.lower() for d in (dominio or self.DOMINIO))

    def _leer(self, nombre: str) -> list[dict]:
        with open(self.base / nombre, encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def competencias(self) -> dict[str, str]:
        """uri -> etiqueta en espanol."""
        return {
            r["conceptUri"]: _primera_forma(r["preferredLabel"])
            for r in self._leer("skills_es.csv")
        }

    def demanda(self) -> list[Competencia]:
        """Competencias requeridas por las ocupaciones del dominio."""
        ocup = self.ocupaciones()
        skills = self.competencias()
        vistas: dict[str, Competencia] = {}

        for r in self._leer("occupationSkillRelations_es.csv"):
            if r["occupationUri"] not in ocup:
                continue
            uri = r["skillUri"]
            etiqueta = skills.get(uri)
            if not etiqueta:
                continue
            esencial = r["relationType"] == "essential"
            if uri in vistas:
                vistas[uri].esencial = vistas[uri].esencial or esencial
            else:
                vistas[uri] = Competencia(
                    uri=uri, etiqueta=etiqueta,
                    tipo=r.get("skillType", ""), esencial=esencial,
                )
        return list(vistas.values())