"""Servicio desplegado. Solo consume artifacts/. Sin modelo pesado."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from core.pipeline.matching import Emparejador  # noqa: E402

ART = RAIZ / "artifacts" / "emb.npz"

st.set_page_config(page_title="Curricula Viva", layout="wide")


@st.cache_resource
def cargar(umbral: float) -> Emparejador:
    return Emparejador(ART, umbral=umbral)


st.title("Currícula Viva")
st.caption("Distancia entre lo que la carrera enseña y lo que el mercado exige")

if not ART.exists():
    st.error("Falta artifacts/emb.npz. Ejecutar: python -m core.cli construir")
    st.stop()

with st.sidebar:
    st.subheader("Parámetros")
    umbral = st.slider("Umbral de similitud", 0.20, 0.70, 0.35, 0.01)
    top = st.slider("Brechas a mostrar", 5, 50, 15)
    ponderar = st.toggle(
        "Ponderar por carga horaria", value=True,
        help="Desactivar = línea base binaria, para contrastar la hipótesis",
    )
    solo_esenciales = st.toggle("Solo competencias esenciales", value=True)

e = cargar(umbral)
brechas = e.brechas(top=300, ponderar=ponderar)
if solo_esenciales:
    brechas = [b for b in brechas if b["esencial"]]
brechas = brechas[:top]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Unidades analizadas", len(e.etq_o))
c2.metric("Competencias evaluadas", len(e.etq_d))
c3.metric("Sin cobertura", sum(1 for b in brechas if b["horas_cubiertas"] == 0))
c4.metric("Horas de malla", int(e.horas.sum()))

st.divider()
st.subheader("Brechas priorizadas")

for b in brechas:
    sev = b["severidad"]
    marca = "🔴" if sev > 0.7 else "🟠" if sev > 0.4 else "🟡"
    tipo = "esencial" if b["esencial"] else "opcional"
    with st.expander(
        f"{marca}  **{b['competencia']}**  ·  severidad {sev:.2f}  ·  "
        f"{b['horas_cubiertas']} h  ·  {tipo}"
    ):
        st.progress(min(max(sev, 0.0), 1.0))
        izq, der = st.columns([1, 2])
        izq.metric("Similitud máxima", f"{b['similitud_max']:.3f}")
        izq.metric("Horas cubiertas", b["horas_cubiertas"])
        with der:
            st.markdown("**Unidades de aprendizaje que la sostienen**")
            if b["soporte"]:
                for u in b["soporte"]:
                    st.markdown(f"- {u}")
            else:
                st.warning("Ninguna unidad supera el umbral: brecha no cubierta.")

st.divider()
with st.expander("Metodología y límites declarados"):
    st.markdown(
        "Similitud coseno sobre embeddings multilingües precomputados, con "
        "umbral configurable y ponderación por carga horaria. Sin entrenamiento: "
        "cada resultado es reproducible y trazable a la unidad que lo sostiene.\n\n"
        "**Límites.** Las horas se reparten proporcionalmente entre capítulos del "
        "plan 2017-2, que no las declara. La muestra se restringe a sílabos con "
        "texto extraíble. La taxonomía de referencia es europea; su transferencia "
        "se sostiene en que las competencias técnicas son transversales, no así el "
        "contexto regulatorio."
    )