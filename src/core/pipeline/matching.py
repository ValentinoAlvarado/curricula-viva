from __future__ import annotations

from pathlib import Path

import numpy as np

UMBRAL = 0.45


class Emparejador:
    """Consume artefactos. Determinista: coseno + umbral + horas."""

    def __init__(self, artefacto: Path, umbral: float = UMBRAL) -> None:
        d = np.load(artefacto, allow_pickle=False)
        self.vo, self.vd = d["v_oferta"], d["v_demanda"]
        self.etq_o, self.etq_d = d["etq_oferta"], d["etq_demanda"]
        self.horas, self.esencial = d["horas"], d["esencial"]
        self.umbral = umbral
        self._sim = self.vd @ self.vo.T          # (demanda, oferta)

    def brechas(self, top: int = 20, ponderar: bool = True) -> list[dict]:
        peso = np.where(self.esencial, 1.0, 0.5)
        cubre = self._sim >= self.umbral
        horas_cub = cubre @ self.horas if ponderar else cubre.sum(axis=1)
        maxh = horas_cub.max() or 1
        cob_h = horas_cub / maxh
        cob_s = self._sim.max(axis=1).clip(0, 1)
        sev = peso * (1 - 0.6 * cob_h - 0.4 * cob_s)

        orden = np.argsort(-sev)[:top]
        return [
            {
                "competencia": str(self.etq_d[i]),
                "esencial": bool(self.esencial[i]),
                "similitud_max": float(self._sim[i].max()),
                "horas_cubiertas": int(horas_cub[i]),
                "severidad": float(sev[i]),
                "soporte": [str(self.etq_o[j]) for j in np.argsort(-self._sim[i])[:3]
                            if self._sim[i][j] >= self.umbral],
            }
            for i in orden
        ]