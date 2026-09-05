from __future__ import annotations

from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class Encoder:
    """Encoding offline. No se instancia en el servicio desplegado."""

    def __init__(self, modelo: str = MODELO) -> None:
        self._m = SentenceTransformer(modelo)

    def encode(self, textos: list[str]) -> np.ndarray:
        return self._m.encode(
            textos, batch_size=64, normalize_embeddings=True,
            show_progress_bar=True,
        )


def construir_artefactos(programa, competencias, destino: Path) -> Path:
    """Vectoriza oferta y demanda; persiste todo en un solo .npz."""
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