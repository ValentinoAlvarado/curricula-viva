"""Benchmark del reranker y barrido de umbral.

Los datos deciden si el cross-encoder entra al release, no la intuicion.
Ejecutar:  python src/core/pipeline/benchmark.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, "src")

from core.pipeline.matching import Emparejador  # noqa: E402

ART = Path("artifacts/emb.npz")
K = 30
N = 20


def barrido_umbral() -> None:
    print("=== BARRIDO DE UMBRAL ===")
    for u in (0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.60):
        e = Emparejador(ART, umbral=u)
        b = e.brechas(top=len(e.etq_d))
        sin_cob = sum(1 for x in b if x["horas_cubiertas"] == 0)
        sev = np.mean([x["severidad"] for x in b])
        print(f"umbral {u:.2f} | sin cobertura {sin_cob:5d} "
              f"({100 * sin_cob / len(b):5.1f}%) | severidad media {sev:.3f}")


def linea_base() -> None:
    print("\n=== PONDERADO POR HORAS vs LINEA BASE BINARIA (top 10) ===")
    e = Emparejador(ART, umbral=0.35)
    pond = [b["competencia"] for b in e.brechas(10, ponderar=True)]
    base = [b["competencia"] for b in e.brechas(10, ponderar=False)]
    comunes = len(set(pond) & set(base))
    print(f"coincidencias: {comunes}/10  ->  {10 - comunes} posiciones cambian")
    for i, (p, b) in enumerate(zip(pond, base), 1):
        print(f"{i:2d}. {p[:42]:42s} | {b[:42]}")


def reranker() -> None:
    from core.pipeline.reranking import Reranker

    print("\n=== BI-ENCODER vs CROSS-ENCODER ===")
    e = Emparejador(ART, umbral=0.35)
    r = Reranker()

    coincidencias, latencias = [], []
    for b in e.brechas(top=N):
        cand = e.candidatos(b["competencia"], k=K)
        pares = [(b["competencia"], str(e.etq_o[j])) for j, _ in cand]

        t0 = time.perf_counter()
        scores = r.puntuar(pares)
        latencias.append(time.perf_counter() - t0)

        bi3 = [str(e.etq_o[j]) for j, _ in cand[:3]]
        ce3 = [pares[k][1] for k in np.argsort(-scores)[:3]]
        coincidencias.append(len(set(bi3) & set(ce3)))
        print(f"\n{b['competencia'][:52]}")
        print(f"  bi : {bi3[0][:52]}")
        print(f"  ce : {ce3[0][:52]}")

    m = np.mean(coincidencias)
    print("\n=== RESUMEN ===")
    print(f"competencias evaluadas  : {N}")
    print(f"candidatos por consulta : {K}")
    print(f"coincidencia top-3      : {m:.2f}/3 ({100 * (1 - m / 3):.0f}% cambia)")
    print(f"latencia media          : {np.mean(latencias) * 1000:.0f} ms")
    print(f"latencia total          : {sum(latencias):.1f} s")


if __name__ == "__main__":
    barrido_umbral()
    linea_base()
    reranker()