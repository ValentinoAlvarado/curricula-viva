"""Busqueda tolerante en los selectores."""

import difflib
import unicodedata


def _normalizar(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t.lower())
                   if unicodedata.category(c) != "Mn")


def buscar(consulta: str, opciones: list[str], limite: int = 8) -> list[str]:
    if not consulta.strip():
        return opciones[:limite]
    q = _normalizar(consulta)
    norm = {o: _normalizar(o) for o in opciones}
    exactas = [o for o, n in norm.items() if q in n]
    if len(exactas) >= limite:
        return exactas[:limite]
    resto = [o for o in opciones if o not in exactas]
    aprox = sorted(resto,
                   key=lambda o: difflib.SequenceMatcher(None, q, norm[o]).ratio(),
                   reverse=True)
    aprox = [o for o in aprox
             if difflib.SequenceMatcher(None, q, norm[o]).ratio() > 0.35
             or any(difflib.SequenceMatcher(None, q, p).ratio() > 0.7
                    for p in norm[o].split())]
    return (exactas + aprox)[:limite]


PROGRAMAS = ["Ingeniería Eléctrica", "Ingeniería Electrónica",
             "Ingeniería De Telecomunicaciones"]


def test_telecom():
    assert buscar("telecom", PROGRAMAS)[0] == "Ingeniería De Telecomunicaciones"


def test_electrica_sin_tilde():
    assert buscar("electrica", PROGRAMAS)[0] == "Ingeniería Eléctrica"


def test_electronica():
    assert buscar("electronica", PROGRAMAS)[0] == "Ingeniería Electrónica"


def test_errata():
    """Tolera erratas de escritura."""
    assert "Ingeniería Electrónica" in buscar("electrnica", PROGRAMAS)


def test_vacio_devuelve_todo():
    assert len(buscar("", PROGRAMAS)) == 3


def test_sin_coincidencias():
    assert buscar("zzzqqq", PROGRAMAS) == []
