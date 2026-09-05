"""Pipeline offline. El servicio (app/) no ejecuta esto.

    python -m core.cli construir
    python -m core.cli brechas --top 15
"""

from __future__ import annotations

import argparse
import glob
from pathlib import Path

from .adapters import FuenteESCO, LectorUNI
from .domain.models import Programa

SILABOS = Path("data/silabos")
ESCO = Path("data/esco")
ARTEFACTO = Path("artifacts/emb.npz")


def cargar_programa() -> Programa:
    lector = LectorUNI()
    rutas = [Path(f) for f in glob.glob(str(SILABOS / "**" / "*.pdf"), recursive=True)]
    silabos = [lector.leer(r) for r in rutas if lector.acepta(r)]
    return Programa(codigo="IE", nombre="Ingenieria Electrica",
                    institucion="FIEE-UNI", silabos=silabos)


def cmd_construir() -> None:
    from .pipeline.encoding import construir_artefactos

    p = cargar_programa()
    c = FuenteESCO(ESCO).demanda()
    print(f"{len(p.silabos)} silabos | {len(list(p.unidades()))} unidades "
          f"| {len(c)} competencias | {p.horas_totales} horas")
    construir_artefactos(p, c, ARTEFACTO)
    print(f"artefacto: {ARTEFACTO} "
          f"({ARTEFACTO.stat().st_size / 1e6:.1f} MB)")


def cmd_brechas(top: int) -> None:
    from .pipeline.matching import Emparejador

    for b in Emparejador(ARTEFACTO).brechas(top=top):
        marca = "!" if b["esencial"] else " "
        print(f"{marca} {b['severidad']:.3f}  {b['competencia'][:55]:55s} "
              f"{b['horas_cubiertas']:5d} h")


def main() -> None:
    p = argparse.ArgumentParser(prog="core")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("construir")
    b = sub.add_parser("brechas")
    b.add_argument("--top", type=int, default=15)

    args = p.parse_args()
    if args.cmd == "construir":
        cmd_construir()
    else:
        cmd_brechas(args.top)


if __name__ == "__main__":
    main()