"""Conexion, sesion y migracion ligera del esquema.

PostgreSQL si DATABASE_URL lo indica, SQLite si no. El codigo es identico
en ambos casos.

Al arrancar se comprueba que las tablas tengan las columnas que el modelo
declara y se anaden las que falten. Evita que una actualizacion del
sistema exija borrar la base a mano.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine

RAIZ = Path(__file__).resolve().parents[2]
POR_DEFECTO = f"sqlite:///{RAIZ / 'curricula.db'}"

DATABASE_URL = os.getenv("DATABASE_URL", POR_DEFECTO)

_kwargs = {"echo": False}
if DATABASE_URL.startswith("sqlite"):
    _kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **_kwargs)

# Columnas anadidas despues de la version inicial.
_MIGRACIONES: dict[str, dict[str, str]] = {
    "analyses": {
        "engine_version": "VARCHAR DEFAULT ''",
        "artifact_hash": "VARCHAR",
        "error": "VARCHAR",
    },
    "esco_competencies": {
        "occupation_count": "INTEGER DEFAULT 0",
        "occupations": "VARCHAR DEFAULT ''",
    },
    "syllabi": {
        "cycle": "INTEGER",
        "mandatory": "BOOLEAN",
    },
    "gaps": {
        "coverage": "FLOAT DEFAULT 0",
    },
}


def _migrar() -> list[str]:
    """Anade columnas ausentes. Idempotente y sin perdida de datos."""
    aplicadas: list[str] = []
    insp = inspect(engine)
    tablas = set(insp.get_table_names())

    with engine.begin() as con:
        for tabla, columnas in _MIGRACIONES.items():
            if tabla not in tablas:
                continue
            existentes = {c["name"] for c in insp.get_columns(tabla)}
            for nombre, tipo in columnas.items():
                if nombre in existentes:
                    continue
                con.execute(text(f"ALTER TABLE {tabla} ADD COLUMN {nombre} {tipo}"))
                aplicadas.append(f"{tabla}.{nombre}")
    return aplicadas


def init_db() -> list[str]:
    """Crea tablas nuevas y migra las existentes."""
    from . import models  # noqa: F401  registra los modelos

    SQLModel.metadata.create_all(engine)
    return _migrar()


def get_session() -> Iterator[Session]:
    with Session(engine) as sesion:
        yield sesion


def motor() -> str:
    return "postgresql" if DATABASE_URL.startswith("postgres") else "sqlite"