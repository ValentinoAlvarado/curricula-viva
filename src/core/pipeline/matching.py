"""Emparejamiento determinista. Corre en el servicio desplegado.

Sin entrenamiento: similitud coseno + umbral + ponderacion por carga
horaria. Cada resultado es reproducible y trazable a las unidades que lo
sostienen, condicion necesaria para un instrumento que sustenta
decisiones academicas.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

UMBRAL = 0.35
PESO_ESENCIAL = 1.0
PESO_OPCIONAL = 0.5


class Emparejador:
    """Consume artefactos precomputados. No carga el modelo."""

    def __init__(self, artefacto: Path, umbral: float = UMBRAL) -> None:
        d = np.load(artefacto, allow_pickle=False)
        self.vo, self.vd = d["v_oferta"], d["v_demanda"]
        self.etq_o, self.etq_d = d["etq_oferta"], d["etq_demanda"]
        self.horas, self.esencial = d["horas"], d["esencial"]
        self.umbral = umbral
        self._sim = self.vd @ self.vo.T  # (demanda, oferta)

    def brechas(self, top: int = 20, ponderar: bool = True) -> list[dict]:
        """Competencias ordenadas por severidad.

        ponderar=False es la linea base binaria: mismo pipeline sin
        ponderacion horaria, para contrastar el efecto de la hipotesis.
        """
        peso = np.where(self.esencial, PESO_ESENCIAL, PESO_OPCIONAL)
        cubre = self._sim >= self.umbral
        horas_cub = cubre @ self.horas if ponderar else cubre.sum(axis=1)

        maxh = horas_cub.max() or 1
        cob_h = horas_cub / maxh
        cob_s = self._sim.max(axis=1).clip(0, 1)
        sev = peso * (1 - 0.6 * cob_h - 0.4 * cob_s)

        orden = np.argsort(-sev)[:top]
        return [self._fila(i, horas_cub[i], sev[i]) for i in orden]

    def _fila(self, i: int, horas_cub, sev) -> dict:
        sims = self._sim[i]
        soporte = [
            str(self.etq_o[j])
            for j in np.argsort(-sims)[:3]
            if sims[j] >= self.umbral
        ]
        return {
            "competencia": str(self.etq_d[i]),
            "esencial": bool(self.esencial[i]),
            "similitud_max": float(sims.max()),
            "horas_cubiertas": int(horas_cub),
            "severidad": float(sev),
            "soporte": soporte,
        }

    def candidatos(self, competencia: str, k: int = 30) -> list[tuple[int, float]]:
        """Top-k unidades para una competencia. Entrada del reranker."""
        i = int(np.where(self.etq_d == competencia)[0][0])
        idx = np.argsort(-self._sim[i])[:k]
        return [(int(j), float(self._sim[i][j])) for j in idx]