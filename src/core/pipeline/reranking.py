"""Segunda etapa de recuperacion: cross-encoder.

El bi-encoder comprime cada texto a 384 dimensiones por separado y
pierde el matiz de la interaccion. El cross-encoder lee el par completo.
Se aplica solo sobre el top-k del retriever: coste acotado.

API verificada en sentence-transformers 6.0.1:
  CrossEncoder(model_name_or_path, *, device=...)
  .predict(inputs, batch_size=..., show_progress_bar=...)
  .rank(query, documents, top_k=..., return_documents=...)
Nota: el antiguo kwarg activation_fct se llama ahora activation_fn.
"""

from __future__ import annotations

import numpy as np
from sentence_transformers import CrossEncoder

MODELO = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"


class Reranker:
    """Puntua pares (competencia, unidad) leyendo ambos textos juntos."""

    def __init__(self, modelo: str = MODELO, device: str = "cpu") -> None:
        self._ce = CrossEncoder(modelo, device=device)

    def puntuar(self, pares: list[tuple[str, str]], batch_size: int = 32) -> np.ndarray:
        return np.asarray(
            self._ce.predict(pares, batch_size=batch_size, show_progress_bar=False)
        )

    def rerank(self, competencia: str, unidades: list[str], top_k: int = 3) -> list[dict]:
        """Reordena unidades para una competencia; devuelve los mejores."""
        return self._ce.rank(
            competencia, unidades, top_k=top_k,
            return_documents=True, show_progress_bar=False,
        )