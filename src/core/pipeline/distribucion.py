"""Análisis de la estructura de la demanda antes de decidir el filtro."""

from __future__ import annotations

import collections
from pathlib import Path

import numpy as np

from core.adapters.esco import FuenteESCO
from core.pipeline.matching import Emparejador

ESCO = Path("data/esco")
ART = Path("artifacts/emb.npz")


def distribucion_tipos() -> None:
    f = FuenteESCO(ESCO)
    ocup = f.ocupaciones()
    skills = f.competencias()

    tipos = collections.Counter()
    por_uri = {}
    for r in f._leer("occupationSkillRelations_es.csv"):
        if r["occupationUri"] not in ocup:
            continue
        uri = r["skillUri"]
        if uri not in skills:
            continue
        t = r.get("skillType") or "(vacio)"
        if uri not in por_uri:
            por_uri[uri] = (t, skills[uri], r["relationType"])
            tipos[t] += 1

    print("=== TIPOS DE COMPETENCIA EN EL DOMINIO ===")
    for t, n in tipos.most_common():
        print(f"{t:20s} {n:5d}")

    print("\n=== MUESTRA POR TIPO ===")
    for t in tipos:
        ej = [v[1] for v in por_uri.values() if v[0] == t][:12]
        print(f"\n{t}:")
        for e in ej:
            print(f"  - {e}")


def tipos_en_brechas(top: int = 30) -> None:
    f = FuenteESCO(ESCO)
    ocup = f.ocupaciones()
    skills = f.competencias()
    tipo_de = {}
    for r in f._leer("occupationSkillRelations_es.csv"):
        if r["occupationUri"] in ocup and r["skillUri"] in skills:
            tipo_de.setdefault(skills[r["skillUri"]], r.get("skillType") or "(vacio)")

    e = Emparejador(ART, umbral=0.35)
    b = e.brechas(top=top)
    c = collections.Counter(tipo_de.get(x["competencia"], "?") for x in b)
    print(f"\n=== TIPOS EN EL TOP-{top} DE BRECHAS ===")
    for t, n in c.most_common():
        print(f"{t:20s} {n:3d}")


def relevancia_al_programa() -> None:
    """Cuánto se parece cada competencia al programa en su conjunto.

    Hipotesis: las competencias absurdas tienen baja similitud MEDIA con
    todas las unidades, no solo baja cobertura. La severidad actual no usa
    esta senal.
    """
    e = Emparejador(ART, umbral=0.35)
    media = e._sim.mean(axis=1)
    maxi = e._sim.max(axis=1)

    print("\n=== RELEVANCIA vs COBERTURA ===")
    print("competencia                                    sim_media  sim_max")
    orden = np.argsort(-e._sim.max(axis=1))
    for i in list(orden[:10]) + list(orden[-10:]):
        print(f"{str(e.etq_d[i])[:45]:45s}  {media[i]:8.3f}  {maxi[i]:7.3f}")

    print(f"\nsim_media global: {media.mean():.3f} "
          f"(p10={np.percentile(media,10):.3f}, p90={np.percentile(media,90):.3f})")


if __name__ == "__main__":
    distribucion_tipos()
    tipos_en_brechas()
    relevancia_al_programa()