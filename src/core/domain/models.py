"""Modelo de dominio.

Cardinalidad:
    Programa 1 --- * Silabo 1 --- * Unidad
    Programa * --- * Competencia  (resuelta por Cobertura)
"""

from __future__ import annotations

from collections.abc import Callable, Iterator

from pydantic import BaseModel, Field


class Unidad(BaseModel):
    """Unidad de aprendizaje. Su carga horaria es la senal cuantitativa."""

    numero: int
    nombre: str
    horas: int
    temas: list[str] = Field(default_factory=list)

    @property
    def texto(self) -> str:
        return f"{self.nombre}. {' '.join(self.temas)}"


class Silabo(BaseModel):
    """Un curso. Agrega 1..* Unidad."""

    codigo: str
    nombre: str
    institucion: str
    periodo: str | None = None
    creditos: int | None = None
    unidades: list[Unidad] = Field(default_factory=list)

    @property
    def horas_totales(self) -> int:
        return sum(u.horas for u in self.unidades)

    def horas_donde(self, predicado: Callable[[Unidad], bool]) -> int:
        return sum(u.horas for u in self.unidades if predicado(u))


class Programa(BaseModel):
    """Programa academico. Agrega 1..* Silabo."""

    codigo: str
    nombre: str
    institucion: str
    silabos: list[Silabo] = Field(default_factory=list)

    @property
    def horas_totales(self) -> int:
        return sum(s.horas_totales for s in self.silabos)

    def unidades(self) -> Iterator[Unidad]:
        for s in self.silabos:
            yield from s.unidades


class Competencia(BaseModel):
    """Competencia de la taxonomia de referencia."""

    uri: str
    etiqueta: str
    tipo: str = ""
    esencial: bool = False


class Cobertura(BaseModel):
    """Relacion N:M resuelta: cuanto cubre un Programa una competencia."""

    competencia: str
    peso_demanda: float
    horas_asignadas: int
    similitud_max: float
    unidades_soporte: list[str] = Field(default_factory=list)