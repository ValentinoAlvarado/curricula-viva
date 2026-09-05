"""Flujo critico end-to-end contra la API en ejecucion.

    universidad -> programa -> malla -> analisis -> brecha -> evidencia

Prueban comportamiento, no que un objeto no sea None. Si la API no esta
levantada, la suite se salta con un motivo explicito.
"""

from __future__ import annotations

import os
import unicodedata

import httpx
import pytest

API = os.getenv("API_URL", "http://127.0.0.1:8000")
UNI = {"name": "Universidad Nacional de Ingeniería", "code": "UNI"}
ESPERADOS = {"electrica", "electronica", "telecomunicaciones"}


def _clave(t: str) -> str:
    p = "".join(c for c in unicodedata.normalize("NFD", t.lower())
                if unicodedata.category(c) != "Mn")
    for w in ("ingenieria", " de ", " del ", " la ", " en "):
        p = p.replace(w, " ")
    return " ".join(p.split())


@pytest.fixture(scope="session")
def api():
    try:
        r = httpx.get(f"{API}/health", timeout=5)
        r.raise_for_status()
    except Exception:
        pytest.skip(f"API no disponible en {API}")
    return API


@pytest.fixture(scope="session")
def universidad(api):
    unis = httpx.get(f"{api}/universities", timeout=30).json()
    fila = next((u for u in unis if u["code"] == UNI["code"]), None)
    if fila is None:
        fila = httpx.post(f"{api}/universities", json=UNI, timeout=60).json()
    return fila


@pytest.fixture(scope="session")
def programas(api, universidad):
    return httpx.get(f"{api}/universities/{universidad['id']}/programs",
                     timeout=120).json()


@pytest.fixture(scope="session")
def analisis(api, programas):
    """Un analisis completado por cada programa."""
    out = {}
    for p in programas:
        prev = [a for a in httpx.get(f"{api}/analyses",
                                     params={"program_id": p["id"],
                                             "vigentes": True},
                                     timeout=30).json()
                if a["status"] == "completed"]
        if prev:
            out[p["id"]] = max(prev, key=lambda a: a["id"])
        else:
            out[p["id"]] = httpx.post(f"{api}/analyses",
                                      json={"program_id": p["id"]},
                                      timeout=900).json()
    return out


# ── salud y endpoints ────────────────────────────────────────
def test_health_reporta_estado(api):
    h = httpx.get(f"{api}/health", timeout=10).json()
    assert h["status"] == "ok"
    assert h["database"] in {"sqlite", "postgresql"}


def test_endpoints_principales_responden(api, programas):
    pid = programas[0]["id"]
    for ruta in ("/universities", "/programs", "/competencies",
                 "/analyses", "/engine", f"/programs/{pid}/syllabi"):
        assert httpx.get(f"{api}{ruta}", timeout=60).status_code == 200


def test_endpoint_inexistente_devuelve_404(api):
    assert httpx.get(f"{api}/analyses/999999", timeout=10).status_code == 404


# ── tres carreras ────────────────────────────────────────────
def test_existen_las_tres_carreras(programas):
    claves = {_clave(p["name"]) for p in programas}
    faltan = ESPERADOS - claves
    assert not faltan, f"faltan carreras: {faltan}"


def test_cada_carrera_tiene_su_propia_malla(api, programas):
    """Tres nombres NO pueden apuntar a los mismos cursos."""
    mallas = {}
    for p in programas:
        cursos = httpx.get(f"{api}/programs/{p['id']}/syllabi",
                           params={"limit": 500}, timeout=60).json()
        mallas[p["name"]] = {c["code"] for c in cursos}
        assert len(cursos) > 50, f"{p['name']} tiene pocos cursos"

    nombres = list(mallas)
    for i, a in enumerate(nombres):
        for b in nombres[i + 1:]:
            assert mallas[a] != mallas[b], f"{a} y {b} comparten malla"
            assert mallas[a] - mallas[b], f"{a} no tiene cursos exclusivos"


def test_cursos_tienen_ciclo_y_tipo(api, programas):
    """Ciclo y obligatoriedad vienen del plan, no se inventan."""
    cursos = httpx.get(f"{api}/programs/{programas[0]['id']}/syllabi",
                       params={"limit": 500}, timeout=60).json()
    con_ciclo = [c for c in cursos if c.get("cycle")]
    assert len(con_ciclo) >= 30, "casi ningun curso trae ciclo"
    assert all(1 <= c["cycle"] <= 10 for c in con_ciclo)
    assert any(c.get("mandatory") is True for c in cursos)


# ── analisis ─────────────────────────────────────────────────
def test_analisis_completa_y_usa_su_programa(analisis, programas):
    for p in programas:
        a = analisis[p["id"]]
        assert a["status"] == "completed", f"{p['name']}: {a.get('error')}"
        assert a["program_id"] == p["id"]
        assert a["n_gaps"] > 0


def test_cambiar_de_carrera_cambia_los_resultados(api, analisis, programas):
    """Distinta malla debe producir distinto ranking y distintas metricas."""
    rankings, coberturas = {}, {}
    for p in programas:
        gs = httpx.get(f"{api}/analyses/{analisis[p['id']]['id']}/gaps",
                       params={"top": 25}, timeout=60).json()
        rankings[p["name"]] = [g["competency"] for g in gs]
        coberturas[p["name"]] = round(
            sum(g.get("coverage", 0) for g in gs) / max(len(gs), 1), 3)

    nombres = list(rankings)
    for i, a in enumerate(nombres):
        for b in nombres[i + 1:]:
            assert rankings[a] != rankings[b], \
                f"{a} y {b} devuelven el mismo ranking"
    assert len(set(coberturas.values())) > 1, "todas las coberturas coinciden"


# ── brecha y evidencia ───────────────────────────────────────
def test_brecha_tiene_competencia_severidad_y_cobertura(api, analisis,
                                                        programas):
    gs = httpx.get(f"{api}/analyses/{analisis[programas[0]['id']]['id']}/gaps",
                   params={"top": 10}, timeout=60).json()
    assert gs
    for g in gs:
        assert g["competency"].strip()
        assert 0.0 <= g["severity"] <= 1.0
        assert 0.0 <= g["coverage"] <= 1.0
        assert g["hours_associated"] >= 0
        assert isinstance(g["essential"], bool)


def test_severidad_ordena_el_ranking(api, analisis, programas):
    gs = httpx.get(f"{api}/analyses/{analisis[programas[0]['id']]['id']}/gaps",
                   params={"top": 20}, timeout=60).json()
    sev = [g["severity"] for g in gs]
    assert sev == sorted(sev, reverse=True), "el ranking no ordena por severidad"


def test_evidencia_apunta_a_asignaturas_reales(api, analisis, programas):
    """La evidencia debe existir en la malla del propio programa."""
    p = programas[0]
    gs = httpx.get(f"{api}/analyses/{analisis[p['id']]['id']}/gaps",
                   params={"top": 20}, timeout=60).json()
    cursos = {c["code"] for c in httpx.get(
        f"{api}/programs/{p['id']}/syllabi",
        params={"limit": 500}, timeout=60).json()}

    con_evidencia = 0
    for g in gs:
        ev = httpx.get(f"{api}/gaps/{g['id']}/evidence", timeout=30).json()
        assert ev["gap_id"] == g["id"]
        assert ev["action"].strip(), "toda brecha debe traer accion sugerida"
        for c in ev["courses"]:
            assert c["course_code"] in cursos, \
                f"{c['course_code']} no pertenece a la malla de {p['name']}"
            assert c["hours"] > 0
            assert 0.0 <= c["similarity"] <= 1.0
        if ev["courses"]:
            con_evidencia += 1
    assert con_evidencia > 0, "ninguna brecha trae evidencia curricular"


def test_horas_asociadas_coinciden_con_la_evidencia(api, analisis, programas):
    """hours_associated no puede ser menor que las horas que se muestran."""
    gs = httpx.get(f"{api}/analyses/{analisis[programas[0]['id']]['id']}/gaps",
                   params={"top": 10}, timeout=60).json()
    for g in gs:
        ev = httpx.get(f"{api}/gaps/{g['id']}/evidence", timeout=30).json()
        if ev["courses"]:
            assert g["hours_associated"] >= max(c["hours"]
                                                for c in ev["courses"])


def test_cobertura_alta_implica_severidad_baja(api, analisis, programas):
    """Coherencia entre las dos metricas."""
    gs = httpx.get(f"{api}/analyses/{analisis[programas[0]['id']]['id']}/gaps",
                   params={"top": 100}, timeout=60).json()
    altas = [g for g in gs if g["coverage"] > 0.7]
    for g in altas:
        assert g["severity"] < 0.5, \
            f"{g['competency']}: cobertura {g['coverage']} y severidad {g['severity']}"
