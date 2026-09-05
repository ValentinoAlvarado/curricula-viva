from __future__ import annotations

import csv
from pathlib import Path

from ..domain.models import Competencia


def _primera_forma(etiqueta: str) -> str:
    """'ingeniero X/ingeniera X' -> 'ingeniero X'."""
    return etiqueta.split("/")[0].strip()


class FuenteESCO:
    """Demanda estructurada: ocupación -> competencias requeridas."""

    clave = "esco"

    def __init__(self, base: Path) -> None:
        self.base = Path(base)

    def _leer(self, nombre: str) -> list[dict]:
        with open(self.base / nombre, encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def ocupaciones_ingenieria(self) -> dict[str, str]:
        """uri -> etiqueta, solo ocupaciones de ingeniería."""
        return {
            r["conceptUri"]: _primera_forma(r["preferredLabel"])
            for r in self._leer("occupations_es.csv")
            if "ingenier" in r["preferredLabel"].lower()
        }

    def competencias(self) -> dict[str, str]:
        """uri -> etiqueta en español."""
        return {
            r["conceptUri"]: _primera_forma(r["preferredLabel"])
            for r in self._leer("skills_es.csv")
        }

    def demanda(self) -> list[Competencia]:
        """Competencias requeridas por ocupaciones de ingeniería."""
        ocup = self.ocupaciones_ingenieria()
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