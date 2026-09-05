"""Emparejamiento determinista con jerarquia de decision explicita.

    dominio ocupacional -> pertinencia -> cobertura -> severidad

La pertinencia es la senal que faltaba: una competencia que el programa
no puede cubrir porque es ajena a su campo no es una brecha, es ruido.

Evidencia medida sobre el corpus (n=1541 competencias, 1805 unidades):
    ruido      sim_max 0.29-0.39   sim_media 0.009-0.099
    pertinente sim_max 0.83-0.96   sim_media 0.189-0.307
La separacion es limpia; el piso por defecto se situa entre ambos grupos.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

# Version del algoritmo. Cambiarla invalida los analisis previos:
# la aplicacion detecta el desfase y recalcula sin intervencion manual.
VERSION = "2.0-pertinencia"

UMBRAL = 0.35
PISO_PERTINENCIA = 0.55
PESO_ESENCIAL = 1.0
PESO_OPCIONAL = 0.5

# Pesos de la severidad. Suman 1 sobre las tres senales de cobertura.
W_HORAS = 0.5
W_SIMILITUD = 0.3
W_PERTINENCIA = 0.2


class Emparejador:
    """Consume artefactos precomputados. No carga el modelo."""

    def __init__(self, artefacto: Path, umbral: float = UMBRAL,
                 piso: float = PISO_PERTINENCIA) -> None:
        d = np.load(artefacto, allow_pickle=False)
        self.vo, self.vd = d["v_oferta"], d["v_demanda"]
        self.etq_o, self.etq_d = d["etq_oferta"], d["etq_demanda"]
        self.horas, self.esencial = d["horas"], d["esencial"]
        self.umbral = umbral
        self.piso = piso
        self._sim = self.vd @ self.vo.T          # (demanda, oferta)
        self._pert = self._sim.max(axis=1)       # pertinencia al programa
        self._afinidad = self._sim.mean(axis=1)  # afinidad media al campo

    # ── consultas de estado ───────────────────────────────────────
    @property
    def n_pertinentes(self) -> int:
        return int((self._pert >= self.piso).sum())

    @property
    def n_descartadas(self) -> int:
        return int((self._pert < self.piso).sum())

    def resumen(self, ponderar: bool = True) -> dict:
        """Indicadores agregados del programa frente a la demanda."""
        b = self.brechas(top=10_000, ponderar=ponderar)
        if not b:
            return {"evaluadas": 0, "sin_cobertura": 0, "criticas": 0,
                    "indice_alineamiento": 0.0, "horas_malla": int(self.horas.sum())}

        sin_cob = sum(1 for x in b if x["horas_cubiertas"] == 0)
        criticas = sum(1 for x in b if x["severidad"] > 0.6)
        return {
            "evaluadas": len(b),
            "sin_cobertura": sin_cob,
            "criticas": criticas,
            "indice_alineamiento": round(1 - float(np.mean([x["severidad"] for x in b])), 3),
            "horas_malla": int(self.horas.sum()),
        }

    def distribucion(self, ponderar: bool = True) -> dict[str, int]:
        """Reparto de competencias por nivel de cobertura."""
        b = self.brechas(top=10_000, ponderar=ponderar)
        d = {"Sin cobertura": 0, "Cobertura marginal": 0, "Cubierta": 0}
        for x in b:
            if x["horas_cubiertas"] == 0:
                d["Sin cobertura"] += 1
            elif x["severidad"] > 0.4:
                d["Cobertura marginal"] += 1
            else:
                d["Cubierta"] += 1
        return d

    # ── nucleo ────────────────────────────────────────────────────
    def brechas(self, top: int = 20, ponderar: bool = True,
                solo_esenciales: bool = False) -> list[dict]:
        """Competencias pertinentes ordenadas por severidad.

        ponderar=False desactiva la carga horaria: linea base binaria
        para contrastar el efecto de la hipotesis.
        """
        pertinente = self._pert >= self.piso
        if solo_esenciales:
            pertinente &= self.esencial.astype(bool)
        idx = np.flatnonzero(pertinente)
        if idx.size == 0:
            return []

        peso = np.where(self.esencial[idx], PESO_ESENCIAL, PESO_OPCIONAL)
        cubre = self._sim[idx] >= self.umbral
        horas_cub = cubre @ self.horas if ponderar else cubre.sum(axis=1)

        maxh = horas_cub.max() or 1
        cob_h = horas_cub / maxh
        cob_s = self._sim[idx].max(axis=1).clip(0, 1)
        cob_a = (self._afinidad[idx] / (self._afinidad.max() or 1)).clip(0, 1)

        sev = peso * (1 - W_HORAS * cob_h - W_SIMILITUD * cob_s - W_PERTINENCIA * cob_a)
        sev = sev.clip(0, 1)

        orden = idx[np.argsort(-sev)][:top]
        sev_map = dict(zip(idx.tolist(), sev.tolist()))
        horas_map = dict(zip(idx.tolist(), horas_cub.tolist()))

        return [self._fila(int(i), horas_map[int(i)], sev_map[int(i)]) for i in orden]

    def _fila(self, i: int, horas_cub, sev) -> dict:
        sims = self._sim[i]
        soporte = [
            {"unidad": str(self.etq_o[j]), "horas": int(self.horas[j]),
             "similitud": round(float(sims[j]), 3)}
            for j in np.argsort(-sims)[:5] if sims[j] >= self.umbral
        ]
        return {
            "competencia": str(self.etq_d[i]),
            "esencial": bool(self.esencial[i]),
            "pertinencia": round(float(self._pert[i]), 3),
            "similitud_max": round(float(sims.max()), 3),
            "horas_cubiertas": int(horas_cub),
            "severidad": round(float(sev), 3),
            "soporte": soporte,
        }

    def candidatos(self, competencia: str, k: int = 30) -> list[tuple[int, float]]:
        """Top-k unidades para una competencia. Entrada del reranker."""
        i = int(np.where(self.etq_d == competencia)[0][0])
        idx = np.argsort(-self._sim[i])[:k]
        return [(int(j), float(self._sim[i][j])) for j in idx]