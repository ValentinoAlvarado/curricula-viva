"""Currícula Viva — interfaz Streamlit con respaldo local para la demo.

El backend sigue siendo la fuente principal en localhost cuando está disponible.
En Streamlit Cloud, si API_URL no responde, se usan los datos versionados en
app/demo_data.py para que la demo no dependa de FastAPI, Render ni SQLite remoto.
"""
from __future__ import annotations

import difflib
import os
import unicodedata
from datetime import datetime

import httpx
import pandas as pd
import streamlit as st

from app.demo_data import COURSES, GAPS, PROGRAMS, UNIVERSITY, evidence

API = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")
ESPERA = 900.0

st.set_page_config(page_title="Currícula Viva", page_icon="📐", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
.stMetric{background:#12161c;border:1px solid #232a33;border-radius:8px;padding:14px}
div[data-testid="stMetricValue"]{font-size:2rem}
.cv-critica{border-left:4px solid #d64545;padding-left:12px}
.cv-media{border-left:4px solid #d68a45;padding-left:12px}
.cv-baja{border-left:4px solid #45a06d;padding-left:12px}
</style>
""", unsafe_allow_html=True)

class ErrorServicio(Exception):
    pass


def _get(ruta: str, **params):
    try:
        r = httpx.get(f"{API}{ruta}", params=params, timeout=60.0)
    except httpx.RequestError as e:
        raise ErrorServicio("El servicio no responde.") from e
    if r.status_code >= 400:
        raise ErrorServicio(f"El servicio devolvió un error ({r.status_code}).")
    return r.json()


def _post(ruta: str, cuerpo: dict, timeout: float = 60.0):
    try:
        r = httpx.post(f"{API}{ruta}", json=cuerpo, timeout=timeout)
    except httpx.RequestError as e:
        raise ErrorServicio("El servicio no responde.") from e
    if r.status_code >= 400:
        raise ErrorServicio(f"El servicio devolvió un error ({r.status_code}).")
    return r.json()


def backend_disponible() -> bool:
    try:
        return _get("/health").get("status") == "ok"
    except ErrorServicio:
        return False


# Importante: no se fija una URL remota obligatoria. En localhost se conserva
# el flujo API actual; en Cloud el fallback local evita el bloqueo de la demo.
LOCAL_DEMO = not backend_disponible()


def consultar(ruta: str, alterno=None, **params):
    if LOCAL_DEMO:
        return [] if alterno is None else alterno
    try:
        return _get(ruta, **params)
    except ErrorServicio:
        return [] if alterno is None else alterno


def universidades():
    return [UNIVERSITY] if LOCAL_DEMO else consultar("/universities")


def programas(uid: int):
    return PROGRAMS if LOCAL_DEMO and uid == UNIVERSITY["id"] else ([] if LOCAL_DEMO else consultar(f"/universities/{uid}/programs"))


def cursos_programa(pid: int):
    return COURSES.get(pid, []) if LOCAL_DEMO else consultar(f"/programs/{pid}/syllabi", limit=500)


def gaps_programa(pid: int):
    if LOCAL_DEMO:
        return GAPS.get(pid, [])
    prev = consultar("/analyses", program_id=pid, vigentes=True)
    prev = [a for a in prev if a["status"] == "completed" and not a.get("stale", False)]
    if not prev:
        return []
    aid = max(prev, key=lambda a: a["id"])["id"]
    return consultar(f"/analyses/{aid}/gaps", top=500)


def evidence_gap(gap_id):
    return evidence(gap_id) if LOCAL_DEMO else consultar(f"/gaps/{gap_id}/evidence", alterno={})


def ejecutar(pid: int, mensaje: str) -> bool:
    if LOCAL_DEMO:
        st.info("La demo usa el análisis curricular versionado localmente.")
        return True
    with st.spinner(mensaje):
        try:
            r = _post("/analyses", {"program_id": pid}, timeout=ESPERA)
        except ErrorServicio as e:
            st.error(str(e))
            return False
    if r.get("status") == "failed":
        st.error(r.get("error") or "El análisis no pudo completarse.")
        return False
    return True


def _normalizar(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t.lower()) if unicodedata.category(c) != "Mn")


def buscar(consulta: str, opciones: list[str], limite: int = 8) -> list[str]:
    if not consulta.strip():
        return opciones[:limite]
    q = _normalizar(consulta)
    normalizadas = {o: _normalizar(o) for o in opciones}
    exactas = [o for o, n in normalizadas.items() if q in n]
    resto = [o for o in opciones if o not in exactas]
    aproximadas = sorted(resto, key=lambda o: difflib.SequenceMatcher(None, q, normalizadas[o]).ratio(), reverse=True)
    return (exactas + [o for o in aproximadas if difflib.SequenceMatcher(None, q, normalizadas[o]).ratio() > .35])[:limite]


def selector(etiqueta: str, opciones: list[str], clave: str) -> str | None:
    if not opciones:
        return None
    if len(opciones) <= 6:
        return st.selectbox(etiqueta, opciones, key=f"sel_{clave}")
    q = st.text_input(etiqueta, key=f"txt_{clave}", placeholder="Escriba para buscar")
    encontrados = buscar(q, opciones)
    if not encontrados:
        st.caption("Sin coincidencias")
        return None
    return st.radio("Resultados", encontrados, key=f"rad_{clave}", label_visibility="collapsed")


def semaforo(sev: float):
    return ("Alta", "cv-critica") if sev > .6 else ("Media", "cv-media") if sev > .35 else ("Baja", "cv-baja")


def criticidad(sev: float):
    return "Alta" if sev > .6 else "Media" if sev > .35 else "Baja"


def tipo_txt(m):
    if m is None:
        return "No disponible"
    return "Obligatorio" if m else "Electivo"


with st.sidebar:
    st.markdown("### Currícula Viva")
    st.caption("Inteligencia curricular")
    st.caption("Base curricular local" if LOCAL_DEMO else "Servicio conectado")
    st.divider()
    unis = universidades()
    umap = {u["name"]: u["id"] for u in unis}
    uni = selector("Institución", list(umap), "uni")
    if uni is None:
        st.stop()
    uid = umap[uni]
    progs = programas(uid)
    if not progs:
        st.warning("Sin programas")
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
    vista = st.radio("Vista", ["Diagnóstico", "Brechas", "Informe"], label_visibility="collapsed")
    st.divider()
    st.caption("Datos locales de demo" if LOCAL_DEMO else "Datos del servicio")

cursos = cursos_programa(pid)
brechas = gaps_programa(pid)
indice = round(sum(b.get("coverage", 0) for b in brechas) / len(brechas), 3) if brechas else 0.0
criticas = [b for b in brechas if b["severity"] > .6]
sin_cob = [b for b in brechas if b.get("hours_associated", 0) == 0]

if vista == "Diagnóstico":
    c1, c2 = st.columns([3, 1])
    c1.title(prog)
    c1.caption(f"{uni} · Plan {plan or 'no declarado'}")
    if c2.button("Actualizar análisis", use_container_width=True):
        ejecutar(pid, "Recalculando…")
    st.divider()
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Cobertura media del plan", f"{indice:.0%}")
    k2.metric("Asignaturas de la malla", len(cursos))
    k3.metric("Competencias evaluadas", len(brechas))
    k4.metric("Criticidad alta", len(criticas))
    st.divider()
    izq, der = st.columns([3, 2])
    with izq:
        st.subheader("Prioridades de revisión")
        for b in brechas[:5]:
            nivel, clase = semaforo(b["severity"])
            st.markdown(f"<div class='{clase}'><b>{b['competency']}</b><br><span style='font-size:.85rem'>Criticidad {nivel} · Cobertura {b.get('coverage',0):.0%} · {b.get('hours_associated',0)} h asociadas · {'esencial' if b['essential'] else 'complementaria'}</span></div>", unsafe_allow_html=True)
            st.write("")
    with der:
        st.subheader("Distribución de cobertura")
        st.bar_chart(pd.DataFrame({"Estado":["Sin cobertura","Marginal","Cubierta"],"Competencias":[len(sin_cob),len([b for b in brechas if b.get('hours_associated',0)>0 and b['severity']>.35]),len([b for b in brechas if b['severity']<=.35])]}).set_index("Estado"), height=260)
    st.divider()
    st.subheader("Malla curricular")
    st.dataframe(pd.DataFrame([{"Código":c["course_code"],"Asignatura":c["course_name"],"Ciclo":c["cycle"],"Horas":c["hours"],"Tipo":tipo_txt(c.get("mandatory"))} for c in cursos]), use_container_width=True, hide_index=True)

elif vista == "Brechas":
    st.title("Brechas detectadas")
    st.caption(f"{prog} · {uni}")
    f1, f2, f3 = st.columns([2,1,1])
    txt = f1.text_input("Buscar competencia", placeholder="Escriba para filtrar")
    nivel_f = f2.selectbox("Severidad", ["Todas", "Crítica", "Moderada", "Menor"])
    tipo_f = f3.selectbox("Tipo", ["Todas", "Esenciales", "Complementarias"])
    vis = brechas
    if txt.strip():
        labels = buscar(txt, [b["competency"] for b in vis], 60)
        vis = [b for b in vis if b["competency"] in labels]
    mapa_nivel = {"Crítica":"Alta", "Moderada":"Media", "Menor":"Baja"}
    if nivel_f != "Todas":
        vis = [b for b in vis if semaforo(b["severity"])[0] == mapa_nivel[nivel_f]]
    if tipo_f == "Esenciales":
        vis = [b for b in vis if b["essential"]]
    elif tipo_f == "Complementarias":
        vis = [b for b in vis if not b["essential"]]
    st.caption(f"{len(vis)} de {len(brechas)} competencias")
    for b in vis:
        nivel, _ = semaforo(b["severity"])
        with st.expander(f"{b['competency']} · Criticidad {nivel} · Cobertura {b.get('coverage',0):.0%}"):
            ev = evidence_gap(b["id"])
            m1, m2, m3 = st.columns(3)
            m1.metric("Cobertura curricular", f"{b.get('coverage',0):.0%}")
            m2.metric("Horas asociadas", b.get("hours_associated", 0))
            m3.metric("Criticidad", nivel)
            st.markdown("**Competencia / perfil profesional**")
            st.write(ev.get("competency", b["competency"]))
            for o in ev.get("occupations") or b.get("occupations") or []:
                st.write(f"· {o}")
            st.markdown("**Cobertura encontrada**")
            rows = ev.get("courses", [])
            if rows:
                st.dataframe(pd.DataFrame([{"Curso":c["course_name"],"Código":c["course_code"],"Ciclo":c.get("cycle"),"Horas":c["hours"],"Tipo":tipo_txt(c.get("mandatory")),"Correspondencia":f"{c['similarity']:.2f}"} for c in rows]), use_container_width=True, hide_index=True)
            else:
                st.warning("Ninguna asignatura supera el umbral de correspondencia.")
            st.markdown("**Acción sugerida**")
            st.info(ev.get("action") or b.get("action") or "No disponible")

else:
    st.title("Informe de sustento")
    st.caption(f"{prog} · {uni} · {datetime.now():%d/%m/%Y}")
    st.markdown(f"### Resumen ejecutivo\n\nEl programa **{prog}** de **{uni}**, plan **{plan or 'no declarado'}**, presenta una **cobertura media del {indice:.0%}** sobre las competencias evaluadas.\n\nSe evaluaron **{len(brechas)}** competencias; **{len(criticas)}** presentan criticidad alta.")
    tabla = pd.DataFrame([{"Competencia":b["competency"],"Criticidad":criticidad(b["severity"]),"Cobertura":f"{b.get('coverage',0):.0%}","Horas curriculares asociadas":b.get("hours_associated",0),"Tipo":"Esencial" if b["essential"] else "Complementaria"} for b in brechas])
    st.dataframe(tabla, use_container_width=True, hide_index=True)
    st.download_button("Descargar informe (CSV)", tabla.to_csv(index=False).encode("utf-8"), file_name=f"brechas_{prog.replace(' ','_')}_{datetime.now():%Y%m%d}.csv", mime="text/csv", type="primary")
    st.divider()
    st.markdown("**Horas curriculares asociadas** indican la carga de asignaturas relacionadas con la competencia; no son horas faltantes. **Cobertura** expresa la proporción estimada de tratamiento.")
