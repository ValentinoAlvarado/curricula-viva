"""Emparejamiento determinista con jerarquia de decision explicita.

    dominio ocupacional -> pertinencia -> cobertura -> severidad

SEMANTICA DE LAS METRICAS
  horas_asociadas  horas curriculares de las asignaturas cuya
                   correspondencia con la competencia supera el umbral.
                   NO son horas faltantes ni un deficit.
  cobertura        0..1. Combina cuanta carga horaria del programa esta
                   asociada a la competencia y cuan estrecha es la
                   correspondencia semantica.
  severidad        0..1. Prioridad de revision = (1 - cobertura)
                   ponderada por la esencialidad de la competencia.

Evidencia medida sobre el corpus:
    ruido      sim_max 0.29-0.39
    pertinente sim_max 0.83-0.96
El piso por defecto se situa entre ambos grupos.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

VERSION = "3.0-cobertura"

UMBRAL = 0.35
PISO_PERTINENCIA = 0.55
PESO_ESENCIAL = 1.0
PESO_OPCIONAL = 0.6

# Composicion de la cobertura.
W_HORAS = 0.5
W_SIMILITUD = 0.35
W_AFINIDAD = 0.15


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
        self._sim = self.vd @ self.vo.T
        self._pert = self._sim.max(axis=1)
        self._afin = self._sim.mean(axis=1)

    @property
    def n_pertinentes(self) -> int:
        return int((self._pert >= self.piso).sum())

    @property
    def n_descartadas(self) -> int:
        return int((self._pert < self.piso).sum())

    def brechas(self, top: int = 20, ponderar: bool = True,
                solo_esenciales: bool = False) -> list[dict]:
        pertinente = self._pert >= self.piso
        if solo_esenciales:
            pertinente &= self.esencial.astype(bool)
        idx = np.flatnonzero(pertinente)
        if idx.size == 0:
            return []

        peso = np.where(self.esencial[idx], PESO_ESENCIAL, PESO_OPCIONAL)
        cubre = self._sim[idx] >= self.umbral
        horas = cubre @ self.horas if ponderar else cubre.sum(axis=1)

        # Cobertura: tres senales normalizadas a [0,1].
        maxh = horas.max() or 1
        c_horas = horas / maxh
        c_sim = self._sim[idx].max(axis=1).clip(0, 1)
        c_afin = (self._afin[idx] / (self._afin.max() or 1)).clip(0, 1)
        cobertura = (W_HORAS * c_horas + W_SIMILITUD * c_sim
                     + W_AFINIDAD * c_afin).clip(0, 1)

        severidad = (peso * (1 - cobertura)).clip(0, 1)

        orden = idx[np.argsort(-severidad)][:top]
        cob = dict(zip(idx.tolist(), cobertura.tolist()))
        sev = dict(zip(idx.tolist(), severidad.tolist()))
        hrs = dict(zip(idx.tolist(), horas.tolist()))

        return [self._fila(int(i), hrs[int(i)], cob[int(i)], sev[int(i)])
                for i in orden]

    def _fila(self, i: int, horas, cobertura, severidad) -> dict:
        sims = self._sim[i]
        soporte = [
            {"unidad": str(self.etq_o[j]), "horas": int(self.horas[j]),
             "similitud": round(float(sims[j]), 3)}
            for j in np.argsort(-sims)[:6] if sims[j] >= self.umbral
        ]
        return {
            "competencia": str(self.etq_d[i]),
            "esencial": bool(self.esencial[i]),
            "pertinencia": round(float(self._pert[i]), 3),
            "similitud_max": round(float(sims.max()), 3),
            "horas_asociadas": int(horas),
            "cobertura": round(float(cobertura), 3),
            "severidad": round(float(severidad), 3),
            "soporte": soporte,
        }

    def candidatos(self, competencia: str, k: int = 30) -> list[tuple[int, float]]:
        i = int(np.where(self.etq_d == competencia)[0][0])
        idx = np.argsort(-self._sim[i])[:k]
        return [(int(j), float(self._sim[i][j])) for j in idx]