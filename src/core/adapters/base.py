from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ..domain.models import Silabo

_LECTORES: dict[str, type[LectorSilabo]] = {}


class LectorSilabo(ABC):
    """Puerto: documento crudo -> Silabo. Una subclase por institución."""

    clave: str

    def __init_subclass__(cls, **kw) -> None:
        super().__init_subclass__(**kw)
        if getattr(cls, "clave", None):
            _LECTORES[cls.clave] = cls

    @abstractmethod
    def acepta(self, ruta: Path) -> bool: ...

    @abstractmethod
    def leer(self, ruta: Path) -> Silabo: ...

    @classmethod
    def para(cls, ruta: Path) -> LectorSilabo:
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