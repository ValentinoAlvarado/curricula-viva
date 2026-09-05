"""Puente pipeline -> base de datos.

Importa el pipeline existente y persiste su salida. matching.py y los
adaptadores no se modifican desde aqui.

Los planes de estudio viven en data/planes/*.pdf. Cada plan es un
programa academico distinto con su propia malla: el sistema los detecta
y los registra sin intervencion manual.
"""

from __future__ import annotations

import glob
import hashlib
import unicodedata
from pathlib import Path

from sqlmodel import Session, select

from core.adapters import FuenteESCO, LectorUNI
from core.adapters.plan import LectorPlanUNI
from core.domain.models import Programa
from core.pipeline.encoding import construir_artefactos
from core.pipeline.matching import Emparejador

from .models import (
    Analysis,
    EscoCompetency,
    EstadoAnalisis,
    Gap,
    LearningUnit,
    Match,
    Program,
    Syllabus,
    University,
)

RAIZ = Path(__file__).resolve().parents[2]
PLANES = RAIZ / "data" / "planes"
SILABOS = RAIZ / "data" / "silabos"
ESCO = RAIZ / "data" / "esco"
ARTEFACTOS = RAIZ / "artifacts"


def _hash(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()[:16]


def artefacto_de(program_id: int) -> Path:
    """Cada programa tiene su propio artefacto de vectores."""
    return ARTEFACTOS / f"emb_{program_id}.npz"


# ─────────────────────────────────────────────────────────────
# Descubrimiento de programas
# ─────────────────────────────────────────────────────────────
def descubrir_programas(sesion: Session, universidad: University) -> int:
    """Registra un programa por cada plan de estudios encontrado.

    Idempotente: se puede llamar en cada consulta. Si un programa ya existe
    (por codigo o por nombre) se reutiliza y se sincroniza su malla con el
    plan, de modo que un registro manual previo no bloquea el descubrimiento.
    """
    if not PLANES.exists():
        return 0

    lector = LectorPlanUNI()
    nuevos = 0

    for ruta in sorted(PLANES.glob("*.pdf")):
        if not lector.acepta(ruta):
            continue
        prog = lector.leer_programa(ruta, universidad.name)
        if not prog.silabos:
            continue

        existentes = sesion.exec(
            select(Program).where(Program.university_id == universidad.id)
        ).all()

        fila = next(
            (p for p in existentes
             if p.code == prog.codigo or _mismo(p.name, prog.nombre)),
            None,
        )

        if fila is None:
            fila = Program(
                university_id=universidad.id, name=prog.nombre,
                code=prog.codigo, plan_period=prog.silabos[0].periodo,
            )
            sesion.add(fila)
            sesion.flush()
            nuevos += 1
        else:
            # Alinea el registro previo con los datos del plan.
            fila.name = prog.nombre
            fila.code = prog.codigo
            fila.plan_period = prog.silabos[0].periodo
            sesion.add(fila)

        _persistir_malla(sesion, fila, prog, ruta)

    sesion.commit()
    return nuevos


def _clave(t: str) -> str:
    """Nombre comparable: sin tildes, sin 'ingenieria', sin conectores."""
    plano = "".join(
        c for c in unicodedata.normalize("NFD", t.lower())
        if unicodedata.category(c) != "Mn"
    )
    for palabra in ("ingenieria", " de ", " del ", " la ", " en "):
        plano = plano.replace(palabra, " ")
    return " ".join(plano.split())


def _mismo(a: str, b: str) -> bool:
    return _clave(a) == _clave(b)


def _persistir_malla(sesion: Session, fila: Program,
                     prog: Programa, ruta: Path) -> None:
    """Vuelca los cursos del plan. Idempotente por codigo de curso."""
    existentes = {
        s.code for s in sesion.exec(
            select(Syllabus).where(Syllabus.program_id == fila.id)
        ).all()
    }
    for s in prog.silabos:
        if s.codigo in existentes:
            continue
        curso = Syllabus(
            program_id=fila.id, code=s.codigo, name=s.nombre,
            credits=s.creditos, period=s.periodo, source_path=ruta.name,
        )
        sesion.add(curso)
        sesion.flush()
        for u in s.unidades:
            sesion.add(LearningUnit(
                syllabus_id=curso.id, number=u.numero, name=u.nombre,
                hours=u.horas, topics=u.temas,
            ))


def ingerir_silabos(sesion: Session, program: Program) -> int:
    """Silabos detallados, si los hay. Complementa la malla del plan."""
    if not SILABOS.exists():
        return 0

    lector = LectorUNI()
    rutas = [Path(f) for f in glob.glob(str(SILABOS / "**" / "*.pdf"),
                                        recursive=True)]
    existentes = {
        s.code for s in sesion.exec(
            select(Syllabus).where(Syllabus.program_id == program.id)
        ).all()
    }
    n = 0
    for ruta in rutas:
        if not lector.acepta(ruta):
            continue
        s = lector.leer(ruta)
        if s.codigo in existentes:
            continue
        existentes.add(s.codigo)
        curso = Syllabus(
            program_id=program.id, code=s.codigo, name=s.nombre,
            credits=s.creditos, period=s.periodo, source_path=ruta.name,
        )
        sesion.add(curso)
        sesion.flush()
        for u in s.unidades:
            sesion.add(LearningUnit(
                syllabus_id=curso.id, number=u.numero, name=u.nombre,
                hours=u.horas, topics=u.temas,
            ))
        n += 1

    sesion.commit()
    return n


def ingerir_competencias(sesion: Session) -> int:
    """ESCO -> esco_competencies, con frecuencia de demanda."""
    fuente = FuenteESCO(ESCO)
    ocup = fuente.ocupaciones()
    skills = fuente.competencias()

    frecuencia: dict[str, int] = {}
    for r in fuente._leer("occupationSkillRelations_es.csv"):
        if r["occupationUri"] in ocup and r["skillUri"] in skills:
            frecuencia[r["skillUri"]] = frecuencia.get(r["skillUri"], 0) + 1

    existentes = {
        c.uri: c for c in sesion.exec(select(EscoCompetency)).all()
    }
    n = 0
    for c in fuente.demanda():
        if c.uri in existentes:
            existentes[c.uri].occupation_count = frecuencia.get(c.uri, 0)
            continue
        sesion.add(EscoCompetency(
            uri=c.uri, label=c.etiqueta, skill_type=c.tipo,
            essential=c.esencial, occupation_count=frecuencia.get(c.uri, 0),
        ))
        n += 1

    sesion.commit()
    return n


# ─────────────────────────────────────────────────────────────
# Analisis
# ─────────────────────────────────────────────────────────────
def _programa_de_bd(sesion: Session, program: Program) -> Programa:
    """Reconstruye el Programa del dominio desde la base."""
    cursos = sesion.exec(
        select(Syllabus).where(Syllabus.program_id == program.id)
    ).all()
    from core.domain.models import Silabo as SilaboDom
    from core.domain.models import Unidad as UnidadDom

    silabos = []
    for c in cursos:
        unidades = sesion.exec(
            select(LearningUnit).where(LearningUnit.syllabus_id == c.id)
        ).all()
        silabos.append(SilaboDom(
            codigo=c.code, nombre=c.name, institucion=program.code,
            periodo=c.period, creditos=c.credits,
            unidades=[UnidadDom(numero=u.number, nombre=u.name,
                                horas=u.hours, temas=u.topics or [])
                      for u in unidades],
        ))
    return Programa(codigo=program.code, nombre=program.name,
                    institucion=program.code, silabos=silabos)


def ejecutar_analisis(sesion: Session, analysis: Analysis,
                      program: Program, top: int = 300) -> None:
    """Vectoriza la malla del programa y persiste brechas y evidencia."""
    try:
        artefacto = artefacto_de(program.id)
        prog = _programa_de_bd(sesion, program)
        if not list(prog.unidades()):
            raise RuntimeError("El programa no tiene cursos registrados.")

        competencias = [
            type("C", (), {"etiqueta": c.label, "esencial": c.essential})()
            for c in sesion.exec(select(EscoCompetency)).all()
        ]
        if not competencias:
            raise RuntimeError("No hay competencias de referencia cargadas.")

        construir_artefactos(prog, competencias, artefacto)
        analysis.artifact_hash = _hash(artefacto)

        emp = Emparejador(artefacto, umbral=analysis.threshold,
                          piso=analysis.floor)

        por_etiqueta = {
            c.label: c for c in sesion.exec(select(EscoCompetency)).all()
        }
        unidades = {
            u.name: u for u in sesion.exec(
                select(LearningUnit)
                .join(Syllabus, LearningUnit.syllabus_id == Syllabus.id)
                .where(Syllabus.program_id == program.id)
            ).all()
        }

        for i, b in enumerate(emp.brechas(top=top,
                                          ponderar=analysis.weighted), 1):
            comp = por_etiqueta.get(b["competencia"])
            if comp is None:
                continue
            sesion.add(Gap(
                analysis_id=analysis.id, competency_id=comp.id,
                severity=b["severidad"], hours_covered=b["horas_cubiertas"],
                max_similarity=b["similitud_max"], rank=i,
            ))
            for s in b["soporte"]:
                u = unidades.get(s["unidad"])
                if u is not None:
                    sesion.add(Match(
                        analysis_id=analysis.id, unit_id=u.id,
                        competency_id=comp.id, similarity=s["similitud"],
                    ))

        analysis.status = EstadoAnalisis.completed
    except Exception as exc:  # noqa: BLE001
        analysis.status = EstadoAnalisis.failed
        analysis.error = str(exc)[:500]
    finally:
        sesion.add(analysis)
        sesion.commit()