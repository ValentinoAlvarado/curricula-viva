"""API de Curricula Viva.

El pipeline offline (core/) permanece intacto: esta capa persiste sus
resultados y los expone. Los embeddings siguen en artifacts/emb.npz.

    uvicorn api.main:app --reload --app-dir src
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from .db import init_db, motor
from .routers import (
    analyses,
    competencies,
    programs,
    syllabi,
    units,
    universities,
)

ARTEFACTO = Path(__file__).resolve().parents[2] / "artifacts" / "emb.npz"


@asynccontextmanager
async def ciclo_vida(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Currícula Viva API",
    description="Medición de brecha entre oferta formativa y demanda ocupacional",
    version="0.1.0",
    lifespan=ciclo_vida,
)

for r in (universities, programs, syllabi, units, competencies, analyses):
    app.include_router(r.router)


@app.get("/health", tags=["health"])
def health() -> dict:
    return {
        "status": "ok",
        "database": motor(),
        "artifact": ARTEFACTO.exists(),
        "artifact_mb": round(ARTEFACTO.stat().st_size / 1e6, 1)
        if ARTEFACTO.exists() else None,
    }
