"""Encoding offline. NO se instancia en el servicio desplegado.

El modelo pesa cientos de MB; el servicio solo consume el .npz que
produce este modulo. Medido: 4320 textos en ~15 s en CPU.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class Encoder:
    """Envuelve el bi-encoder. Vectores normalizados: coseno = producto punto."""

    def __init__(self, modelo: str = MODELO, device: str = "cpu") -> None:
        self._m = SentenceTransformer(modelo, device=device)

    @property
    def dimension(self) -> int:
        return self._m.get_embedding_dimension()

    def encode(self, textos: list[str], batch_size: int = 64) -> np.ndarray:
        return self._m.encode(
            textos,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=True,
        )


def construir_artefactos(programa, competencias, destino: Path) -> Path:
    """Vectoriza oferta y demanda; persiste todo en un unico .npz."""
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)

    unidades = list(programa.unidades())
    enc = Encoder()

    np.savez_compressed(
        destino,
        v_oferta=enc.encode([u.texto for u in unidades]),
        v_demanda=enc.encode([c.etiqueta for c in competencias]),
        etq_oferta=np.array([u.nombre for u in unidades]),
        horas=np.array([u.horas for u in unidades], dtype=np.int32),
        etq_demanda=np.array([c.etiqueta for c in competencias]),
        esencial=np.array([c.esencial for c in competencias]),
    )
    return destino