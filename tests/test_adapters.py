"""Contrato polimorfico y errores criticos."""

from pathlib import Path

import pytest

from core.adapters import FormatoNoReconocido, LectorSilabo, lectores_registrados
from core.adapters.esco import _primera_forma


def test_registro_autopoblado():
    """Definir la subclase la registra: sin if/elif de despacho."""
    assert "uni" in lectores_registrados()


def test_puerto_es_abstracto():
    """No se puede instanciar el puerto: obliga a implementar el contrato."""
    with pytest.raises(TypeError):
        LectorSilabo()


def test_corte_de_genero():
    """Las etiquetas ESCO traen ambos generos separados por '/'."""
    assert _primera_forma("ingeniero de control/ingeniera de control") == \
        "ingeniero de control"


def test_archivo_inexistente_falla_controlada():
    """Error critico: ruta invalida no revienta, lanza excepcion tipada."""
    with pytest.raises(FormatoNoReconocido):
        LectorSilabo.para(Path("no_existe.pdf"))