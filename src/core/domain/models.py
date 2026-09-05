"""Modelo de dominio.

Cardinalidad:
    Programa 1 ─ * Silabo 1 ─ * Unidad
    Programa * ─ * Competencia  (resuelta por Cobertura)
"""

from __future__ import annotations

from collections.abc import Iterator

from pydantic import BaseModel, Field


class Unidad(BaseModel):
    """Unidad de aprendizaje. La carga horaria es la señal cuantitativa."""

    numero: int
    nombre: str
    horas: int = 0
    temas: list[str] = Field(default_factory=list)

    @property
    def texto(self) -> str:
        return f"{self.nombre}. {' '.join(self.temas)}".strip()


class Silabo(BaseModel):
    codigo: str
    nombre: str
    institucion: str = "UNI"
    periodo: str | None = None
    creditos: int | None = None
    ciclo: str | None = None
    unidades: list[Unidad] = Field(default_factory=list)

    @property
    def horas_totales(self) -> int:
        return sum(u.horas for u in self.unidades)


class Programa(BaseModel):
    codigo: str
    nombre: str
    institucion: str = "UNI"
    silabos: list[Silabo] = Field(default_factory=list)

    @property
    def horas_totales(self) -> int:
        return sum(s.horas_totales for s in self.silabos)

    def unidades(self) -> Iterator[Unidad]:
        for s in self.silabos:
            yield from s.unidades


class Competencia(BaseModel):
    """Competencia de la taxonomía de referencia."""

    uri: str
    etiqueta: str
    tipo: str | None = None          # knowledge | skill/competence
    esencial: bool = True


class Cobertura(BaseModel):
    """Resultado: cuánto cubre la malla una competencia demandada."""

    competencia: Competencia
    peso_demanda: float
    horas_asignadas: int
    similitud_max: float
    unidades_soporte: list[str] = Field(default_factory=list)

    @property
    def severidad(self) -> float:
        """Brecha: demanda alta con cobertura horaria baja."""
        cobertura = min(self.horas_asignadas / 20.0, 1.0)
        return round(self.peso_demanda * (1.0 - cobertura), 4)