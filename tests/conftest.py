import pytest

from core.domain.models import Silabo, Unidad


@pytest.fixture
def silabo():
    return Silabo(
        codigo="BMA01", nombre="Calculo Diferencial", institucion="FIEE-UNI",
        periodo="2017-2", creditos=5,
        unidades=[
            Unidad(numero=1, nombre="FUNCIONES", horas=8, temas=["dominio", "rango"]),
            Unidad(numero=2, nombre="LIMITES", horas=20, temas=["continuidad"]),
            Unidad(numero=3, nombre="DERIVADA", horas=18, temas=["regla de la cadena"]),
        ],
    )