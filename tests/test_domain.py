"""Camino feliz del modelo de dominio."""

from core.domain.models import Programa


def test_horas_totales(silabo):
    assert silabo.horas_totales == 46


def test_horas_donde(silabo):
    """Agregacion selectiva por predicado."""
    assert silabo.horas_donde(lambda u: u.horas > 10) == 38


def test_texto_unidad_concatena(silabo):
    """El texto que se encodea combina nombre y temas."""
    assert silabo.unidades[0].texto == "FUNCIONES. dominio rango"


def test_programa_agrega(silabo):
    """Cardinalidad 1..*: el programa suma las horas de sus silabos."""
    p = Programa(codigo="IE", nombre="Ing. Electrica",
                 institucion="FIEE-UNI", silabos=[silabo, silabo])
    assert p.horas_totales == 92
    assert len(list(p.unidades())) == 6