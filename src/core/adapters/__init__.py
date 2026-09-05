"""Importar aqui registra las implementaciones en el registro de base."""
from .plan import LectorPlanUNI
from .base import (
    FormatoNoReconocido,
    LectorSilabo,
    lectores_registrados,
)
from .esco import FuenteESCO
from .uni import LectorUNI

__all__ = [
    "FormatoNoReconocido",
    "FuenteESCO",
    "LectorSilabo",
    "LectorUNI",
    "lectores_registrados",
]