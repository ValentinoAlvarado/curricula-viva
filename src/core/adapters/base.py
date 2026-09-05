"""Puertos abstractos. Aqui vive el polimorfismo, y solo aqui.

Cada institucion maqueta sus silabos distinto: variacion real de
comportamiento sobre un contrato estable. Anadir una universidad es una
subclase nueva, sin tocar el pipeline.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ..domain.models import Silabo

_LECTORES: dict[str, type[LectorSilabo]] = {}


class LectorSilabo(ABC):
    """Puerto: documento crudo -> Silabo."""

    clave: str

    def __init_subclass__(cls, **kw) -> None:
        super().__init_subclass__(**kw)
        if getattr(cls, "clave", None):
            _LECTORES[cls.clave] = cls

    @abstractmethod
    def acepta(self, ruta: Path) -> bool:
        """True si esta implementacion reconoce el documento."""

    @abstractmethod
    def leer(self, ruta: Path) -> Silabo:
        """Extrae el Silabo. Lanza FormatoNoReconocido si no puede."""

    @classmethod
    def para(cls, ruta: Path) -> LectorSilabo:
        """Despacho polimorfico: sin cadenas de if/elif."""
        for impl in _LECTORES.values():
            lector = impl()
            if lector.acepta(ruta):
                return lector
        raise FormatoNoReconocido(ruta)


class FormatoNoReconocido(Exception):
    def __init__(self, ruta: Path) -> None:
        super().__init__(f"formato no reconocido: {ruta}")
        self.ruta = ruta


def lectores_registrados() -> list[str]:
    return sorted(_LECTORES)