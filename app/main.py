"""Currícula Viva — plataforma de inteligencia curricular.

Producto para direcciones académicas: mide la distancia entre la oferta
formativa y la demanda ocupacional, y la traduce en decisiones de malla.

Sin caché de Streamlit: todas las consultas van a un servicio local y son
baratas. Cachear introducía fallos de hashabilidad sin ganancia real.
"""

from __future__ import annotations

import difflib
import os
import unicodedata
from datetime import datetime

import httpx
import pandas as pd
import streamlit as st

API = os.getenv("API_URL", "http://127.0.0.1:8000")
ESPERA = 900.0

st.set_page_config(page_title="Currícula Viva", page_icon="📐",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
  .stMetric {background:#12161c;border:1px solid #232a33;border-radius:8px;padding:14px}
  div[data-testid="stMetricValue"] {font-size:2rem}
  .cv-critica {border-left:4px solid #d64545;padding-left:12px}
  .cv-media   {border-left:4px solid #d68a45;padding-left:12px}
  .cv-baja    {border-left:4px solid #45a06d;padding-left:12px}
</style>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════
# Acceso al servicio
# ═════════════════════════════════════════════════════════════
class ErrorServicio(Exception):
    """Fallo del servicio expresado en lenguaje de usuario."""


def _get(ruta: str, **params):
    try:
        r = httpx.get(f"{API}{ruta}", params=params, timeout=60.0)
    except httpx.RequestError as e:
        raise ErrorServicio("El servicio no responde.") from e
    if r.status_code >= 400:
        raise ErrorServicio(f"El servicio devolvió un error ({r.status_code}).")
    return r.json()


def consultar(ruta: str, alterno=None, **params):
    """Consulta que nunca interrumpe la pantalla."""
    try:
        return _get(ruta, **params)
    except ErrorServicio:
        return [] if alterno is None else alterno


def _post(ruta: str, cuerpo: dict, timeout: float = 60.0):
    try:
        r = httpx.post(f"{API}{ruta}", json=cuerpo, timeout=timeout)
    except httpx.RequestError as e:
        raise ErrorServicio("El servicio no responde.") from e
    if r.status_code >= 400:
        try:
            detalle = r.json().get("detail", "")
        except Exception:  # noqa: BLE001
            detalle = ""
        raise ErrorServicio(detalle or "No se pudo completar la operación.")
    return r.json()


# ═════════════════════════════════════════════════════════════
# Búsqueda tolerante
# ═════════════════════════════════════════════════════════════
def _normalizar(t: str) -> str:
    """Minúsculas sin tildes, para comparar sin exigir acentuación."""
    return "".join(
        c for c in unicodedata.normalize("NFD", t.lower())
        if unicodedata.category(c) != "Mn"
    )


def buscar(consulta: str, opciones: list[str], limite: int = 8) -> list[str]:
    """Coincidencia por subcadena y, si no basta, por similitud.

    'telecom'  -> Ingeniería de Telecomunicaciones
    'electrica'-> Ingeniería Eléctrica
    'electrnc' -> Ingeniería Electrónica  (tolerante a erratas)
    """
    if not consulta.strip():
        return opciones[:limite]

    q = _normalizar(consulta)
    normalizadas = {o: _normalizar(o) for o in opciones}

    exactas = [o for o, n in normalizadas.items() if q in n]
    if len(exactas) >= limite:
        return exactas[:limite]

    resto = [o for o in opciones if o not in exactas]
    aproximadas = sorted(
        resto,
        key=lambda o: difflib.SequenceMatcher(None, q, normalizadas[o]).ratio(),
        reverse=True,
    )
    aproximadas = [
        o for o in aproximadas
        if difflib.SequenceMatcher(None, q, normalizadas[o]).ratio() > 0.35
        or any(difflib.SequenceMatcher(None, q, p).ratio() > 0.7
               for p in normalizadas[o].split())
    ]
    return (exactas + aproximadas)[:limite]


def selector(etiqueta: str, opciones: list[str], clave: str,
             umbral_busqueda: int = 6) -> str | None:
    """Lista corta -> desplegable. Lista larga -> búsqueda textual."""
    if not opciones:
        return None
    if len(opciones) <= umbral_busqueda:
        return st.selectbox(etiqueta, opciones, key=f"sel_{clave}")

    consulta = st.text_input(etiqueta, key=f"txt_{clave}",
                             placeholder="Escriba para buscar")
    encontrados = buscar(consulta, opciones)
    if not encontrados:
        st.caption("Sin coincidencias")
        return None
    if len(encontrados) == 1:
        st.caption(f"→ {encontrados[0]}")
        return encontrados[0]
    return st.radio("Resultados", encontrados, key=f"rad_{clave}",
                    label_visibility="collapsed")


# ═════════════════════════════════════════════════════════════
# Datos
# ═════════════════════════════════════════════════════════════
def universidades():
    return consultar("/universities")


def programas(uid: int):
    return consultar(f"/universities/{uid}/programs")


def analisis_vigentes(pid: int):
    datos = consultar("/analyses", program_id=pid, vigentes=True)
    return [a for a in datos
            if a["status"] == "completed" and not a.get("stale", False)]


def obsoletos(pid: int) -> int:
    return sum(1 for a in consultar("/analyses", program_id=pid)
               if a.get("stale") and a["status"] == "completed")


def ejecutar(pid: int, mensaje: str) -> bool:
    with st.spinner(mensaje):
        try:
            r = _post("/analyses", {"program_id": pid}, timeout=ESPERA)
        except ErrorServicio as e:
            st.error(str(e))
            return False
        except Exception:  # noqa: BLE001
            st.error("No se pudo completar el análisis. "
                     "Inténtelo de nuevo en unos momentos.")
            return False
    if r["status"] == "failed":
        st.error(r.get("error") or "El análisis no pudo completarse.")
        return False
    return True


def salud():
    return consultar("/health", alterno=False) or None


def semaforo(sev: float) -> tuple[str, str]:
    if sev > 0.6:
        return "Crítica", "cv-critica"
    if sev > 0.35:
        return "Moderada", "cv-media"
    return "Menor", "cv-baja"


def recomendacion(b: dict) -> str:
    horas, sev = b["hours_covered"], b["severity"]
    if horas == 0:
        return ("Ninguna asignatura del plan aborda esta competencia. "
                "Requiere incorporación explícita en un curso existente "
                "o creación de contenido nuevo.")
    if sev > 0.6:
        return (f"Presencia marginal ({horas} h). Conviene ampliar la carga "
                "horaria o profundizar el tratamiento en las asignaturas "
                "que ya la abordan.")
    if sev > 0.35:
        return ("Cobertura parcial. Revisar si el nivel de profundidad "
                "corresponde a lo que exige el perfil ocupacional.")
    return "Cobertura suficiente. Sin acción requerida en este ciclo."


# ═════════════════════════════════════════════════════════════
# Barra lateral
# ═════════════════════════════════════════════════════════════
h = salud()
with st.sidebar:
    st.markdown("### Currícula Viva")
    st.caption("Inteligencia curricular")
    if not h:
        st.error("Servicio no disponible")
        st.caption("Vuelva a intentarlo en unos momentos.")
        st.stop()
    st.divider()

    unis = universidades()
    if not unis:
        st.warning("Sin instituciones registradas")
        with st.form("alta_u"):
            st.markdown("**Registrar institución**")
            n = st.text_input("Nombre")
            c = st.text_input("Siglas")
            if st.form_submit_button("Registrar", type="primary") and n and c:
                try:
                    _post("/universities", {"name": n, "code": c.upper()})
                except ErrorServicio as e:
                    st.error(str(e))
                else:
                    st.rerun()
        st.stop()

    umap = {u["name"]: u["id"] for u in unis}
    uni = selector("Institución", list(umap), "uni")
    if uni is None:
        st.stop()
    uid = umap[uni]

    progs = programas(uid)
    if not progs:
        st.warning("Sin programas")
        if st.button("Buscar planes de estudio", use_container_width=True):
            try:
                _post(f"/universities/{uid}/discover", {})
            except ErrorServicio as e:
                st.error(str(e))
            else:
                st.rerun()
        st.stop()

    pmap = {p["name"]: p["id"] for p in progs}
    prog = selector("Programa", list(pmap), "prog")
    if prog is None:
        st.stop()
    pid = pmap[prog]
    datos_prog = next(p for p in progs if p["id"] == pid)
    plan = datos_prog.get("plan_period")

    st.caption(f"{len(progs)} programas disponibles")
    st.divider()
    vista = st.radio("Vista", ["Diagnóstico", "Brechas", "Informe"],
                     label_visibility="collapsed")
    st.divider()
    st.caption(f"Base {h['database']}")


# ═════════════════════════════════════════════════════════════
prev = analisis_vigentes(pid)

if not prev:
    st.title(prog)
    st.caption(f"{uni} · Plan {plan or 'no declarado'}")

    cursos = consultar(f"/programs/{pid}/syllabi", limit=500)
    st.caption(f"{len(cursos)} asignaturas registradas en la malla")

    if obsoletos(pid):
        st.info("El motor de análisis se ha actualizado. "
                "Los resultados anteriores se están recalculando.")
        if ejecutar(pid, "Actualizando el análisis…"):
            st.rerun()
        st.stop()

    st.info("Este programa aún no ha sido analizado. El sistema contrastará "
            "su malla con el estándar ocupacional de referencia.")
    col, _ = st.columns([1, 2])
    with col:
        if st.button("Iniciar análisis", type="primary",
                     use_container_width=True):
            if ejecutar(pid, "Procesando plan de estudios…"):
                st.rerun()
    st.stop()

ultimo = max(prev, key=lambda a: a["id"])
aid = ultimo["id"]
brechas = consultar(f"/analyses/{aid}/gaps", top=500)
criticas = [b for b in brechas if b["severity"] > 0.6]
sin_cob = [b for b in brechas if b["hours_covered"] == 0]
indice = (round(1 - sum(b["severity"] for b in brechas) / len(brechas), 3)
          if brechas else 0.0)


# ═════════════════════════════════════════════════════════════
if vista == "Diagnóstico":
    c1, c2 = st.columns([3, 1])
    c1.title(prog)
    c1.caption(f"{uni} · Plan {plan or 'no declarado'} · "
               f"Análisis del {ultimo['created_at'][:10]}")
    if c2.button("Actualizar análisis", use_container_width=True):
        if ejecutar(pid, "Recalculando…"):
            st.rerun()

    st.divider()
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Índice de alineamiento", f"{indice:.0%}",
              help="Proporción de la demanda ocupacional cubierta por la malla")
    k2.metric("Competencias evaluadas", len(brechas))
    k3.metric("Brechas críticas", len(criticas),
              delta=f"{len(criticas)/len(brechas):.0%}" if brechas else None,
              delta_color="inverse")
    k4.metric("Sin cobertura", len(sin_cob), delta_color="inverse")

    st.divider()
    izq, der = st.columns([3, 2])

    with izq:
        st.subheader("Prioridades de revisión")
        st.caption("Las cinco competencias con mayor severidad")
        for b in brechas[:5]:
            nivel, clase = semaforo(b["severity"])
            st.markdown(
                f"<div class='{clase}'><b>{b['competency']}</b><br>"
                f"<span style='color:#8b95a1;font-size:.85rem'>"
                f"{nivel} · {b['hours_covered']} h en la malla · "
                f"{'esencial' if b['essential'] else 'complementaria'}"
                f"</span></div>", unsafe_allow_html=True)
            st.write("")

    with der:
        st.subheader("Distribución de cobertura")
        st.bar_chart(pd.DataFrame({
            "Estado": ["Sin cobertura", "Marginal", "Cubierta"],
            "Competencias": [
                len(sin_cob),
                len([b for b in brechas
                     if b["hours_covered"] > 0 and b["severity"] > 0.35]),
                len([b for b in brechas if b["severity"] <= 0.35]),
            ],
        }).set_index("Estado"), height=260)

    st.divider()
    st.subheader("Lectura del diagnóstico")
    if indice >= 0.7:
        st.success(f"La malla cubre el {indice:.0%} de la demanda ocupacional "
                   f"evaluada. Las {len(criticas)} brechas críticas son "
                   "abordables mediante ajustes de contenido.")
    elif indice >= 0.45:
        st.warning(f"Cobertura del {indice:.0%}. Hay {len(criticas)} "
                   f"competencias con tratamiento insuficiente y {len(sin_cob)} "
                   "sin presencia en la malla. Se recomienda una revisión "
                   "focalizada antes del próximo ciclo.")
    else:
        st.error(f"Cobertura del {indice:.0%}. La distancia respecto al perfil "
                 "ocupacional sugiere una revisión estructural del plan.")


# ═════════════════════════════════════════════════════════════
elif vista == "Brechas":
    st.title("Brechas detectadas")
    st.caption(f"{prog} · {uni}")

    f1, f2, f3 = st.columns([2, 1, 1])
    txt = f1.text_input("Buscar competencia", placeholder="Escriba para filtrar")
    nivel_f = f2.selectbox("Severidad", ["Todas", "Crítica", "Moderada", "Menor"])
    tipo_f = f3.selectbox("Tipo", ["Todas", "Esenciales", "Complementarias"])

    vis = brechas
    if txt.strip():
        etiquetas = buscar(txt, [b["competency"] for b in vis], limite=60)
        vis = [b for b in vis if b["competency"] in etiquetas]
    if nivel_f != "Todas":
        vis = [b for b in vis if semaforo(b["severity"])[0] == nivel_f]
    if tipo_f == "Esenciales":
        vis = [b for b in vis if b["essential"]]
    elif tipo_f == "Complementarias":
        vis = [b for b in vis if not b["essential"]]

    st.caption(f"{len(vis)} de {len(brechas)} competencias")

    for b in vis[:40]:
        nivel, _ = semaforo(b["severity"])
        with st.expander(f"{b['competency']}  ·  {nivel}  ·  "
                         f"{b['hours_covered']} h"):
            a, c = st.columns([1, 3])
            with a:
                st.metric("Severidad", f"{b['severity']:.2f}")
                st.metric("Horas en la malla", b["hours_covered"])
                st.caption("Esencial" if b["essential"] else "Complementaria")
            with c:
                st.markdown("**Recomendación**")
                st.info(recomendacion(b))
                st.markdown("**Evidencia curricular**")
                ev = consultar(f"/gaps/{b['id']}/evidence",
                               alterno={"units": []})
                if ev["units"]:
                    st.dataframe(pd.DataFrame([{
                        "Código": u["syllabus_code"],
                        "Asignatura": u["syllabus_name"],
                        "Horas": u["hours"],
                    } for u in ev["units"]]),
                        use_container_width=True, hide_index=True)
                else:
                    st.warning("Ninguna asignatura de la malla aborda esta "
                               "competencia.")


# ═════════════════════════════════════════════════════════════
elif vista == "Informe":
    st.title("Informe de sustento")
    st.caption(f"{prog} · {uni} · {datetime.now():%d/%m/%Y}")

    st.markdown(f"""
### Resumen ejecutivo

El programa **{prog}** de **{uni}**, plan **{plan or 'no declarado'}**,
presenta un índice de alineamiento del **{indice:.0%}** respecto al estándar
ocupacional de referencia.

Sobre **{len(brechas)}** competencias evaluadas, **{len(criticas)}** presentan
severidad crítica y **{len(sin_cob)}** no tienen presencia alguna en la malla.

### Competencias que requieren intervención prioritaria
""")

    tabla = pd.DataFrame([{
        "Competencia": b["competency"],
        "Severidad": round(b["severity"], 2),
        "Horas en la malla": b["hours_covered"],
        "Tipo": "Esencial" if b["essential"] else "Complementaria",
    } for b in brechas[:20]])
    st.dataframe(tabla, use_container_width=True, hide_index=True)

    st.download_button(
        "Descargar informe (CSV)",
        tabla.to_csv(index=False).encode("utf-8"),
        file_name=f"brechas_{prog.replace(' ', '_')}_{datetime.now():%Y%m%d}.csv",
        mime="text/csv", type="primary")

    st.divider()
    st.markdown("""
### Metodología

Cada asignatura del plan y cada competencia del estándar ocupacional se
representan en un mismo espacio semántico. La correspondencia entre ambas se
pondera por la carga horaria que la malla dedica a cada asignatura. El
procedimiento es determinista: dos ejecuciones con los mismos parámetros
producen el mismo resultado, y cada brecha es trazable hasta las asignaturas
concretas que la sostienen.

Antes de evaluar cobertura, el sistema descarta las competencias cuya
pertinencia al campo del programa está por debajo del umbral calibrado sobre
la distribución observada. Una competencia ajena al campo no constituye una
brecha.

### Límites declarados

Las horas provienen de la carga declarada en el plan de estudios (teoría,
práctica y laboratorio). El estándar ocupacional de referencia es europeo; su
transferencia se sostiene en que las competencias técnicas son transversales,
no así el contexto regulatorio local.
""")