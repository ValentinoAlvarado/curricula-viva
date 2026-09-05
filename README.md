# Currícula Viva

Mide la distancia entre lo que una carrera enseña y lo que el mercado laboral
pide, y señala en qué competencias y con qué prioridad. Convierte un
diagnóstico curricular hoy cualitativo en un indicador reproducible y
trazable.

**Equipo NOMYRA** · BRODT Hackathon 2026 · Track *Future of Education*

---

## Problema & Enfoque Lean

**Problema.** Un plan de estudios se revisa cada varios años; el mercado que
debe atender cambia de forma continua. No existe hoy un instrumento que mida
esa distancia. Evidencia propia: la Escuela Profesional de Ingeniería
Eléctrica de la FIEE-UNI publica 267 sílabos del plan **2017-2**, mientras el
plan que ejecuta es el **2018-2 con convalidaciones al 2021-1**. El documento
que dice qué se enseña va un plan por detrás del plan que se dicta.

**Usuario objetivo.** Coordinador o director de escuela profesional, y los
comités de currículo que preparan expedientes de revisión de malla. El
comprador es la universidad, vía la oficina de calidad y acreditación, que
debe sustentar documentalmente la pertinencia de su oferta formativa.

**MVP.** Ingesta de sílabos en PDF, extracción estructurada de contenidos,
normalización contra una taxonomía de competencias, emparejamiento semántico
contra requerimientos ocupacionales, e informe de brechas priorizadas por
severidad para un programa académico completo.

---

## Stack Tecnológico & IA

| Capa | Tecnología | Por qué |
|---|---|---|
| Extracción | PyMuPDF 1.28.2 | 267/267 sílabos son texto nativo; sin OCR |
| Representación | sentence-transformers 6.0.1, `paraphrase-multilingual-MiniLM-L12-v2` | multilingüe, 384 dim, corre en CPU |
| Emparejamiento | NumPy 2.5.2 | coseno determinista; FAISS es sobreingeniería a esta escala |
| Validación de esquemas | Pydantic 2.13.5 | entidades del dominio tipadas |
| Interfaz | Streamlit 1.63.0 | despliegue rápido, consume artefactos |

**Decisión de arquitectura.** El pipeline pesado corre offline y produce
artefactos versionados; el servicio desplegado solo los consume. El modelo de
representación **no** se carga en producción: el runtime son tres paquetes
(`streamlit`, `numpy`, `pydantic`), verificado sin torch. Costo marginal por
consulta cercano a cero.

**Sin entrenamiento de modelos.** El emparejamiento es determinista —
similitud coseno, umbral, ponderación por carga horaria—, de modo que cada
resultado es reproducible y trazable hasta la unidad de aprendizaje que lo
sostiene. Es condición necesaria para un instrumento que sustenta decisiones
académicas.

### Fuentes de datos

| Fuente | Volumen | Estado |
|---|---|---|
| Sílabos FIEE-UNI, plan 2017-2 | 267 PDF · 1 765 capítulos | texto nativo verificado |
| ESCO v1.2.1 (es) — competencias | 13 960 | descargado |
| ESCO v1.2.1 (es) — ocupaciones | 3 043 (193 de ingeniería) | descargado |
| ESCO — relaciones ocupación/competencia | 126 051 (67 600 esenciales) | descargado |
| SUNEDU — programas de pregrado | 3 592 en 95 universidades | descargado |

Nota sobre ESCO: las etiquetas de `occupationSkillRelations_es.csv` vienen en
inglés pese al sufijo; se resuelven por unión de URI contra `skills_es.csv` y
`occupations_es.csv`. Las etiquetas de ocupación traen ambos géneros separados
por `/` y se normalizan antes de encodear.

---

## Setup Local

```bash
git clone https://github.com/ValentinoAlvarado/curricula-viva.git
cd curricula-viva
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements-dev.txt
pytest
python -m core.cli parse data/silabos
```

Solo el runtime del servicio:

```bash
pip install -r requirements.txt
```

---

## Arquitectura

Documento completo con diagramas Mermaid en
[`docs/arquitectura.md`](docs/arquitectura.md).

### Casos de uso (UML 2.5)

![Casos de uso](docs/1_casos_uso.png)

El coordinador de escuela y el comité de currículo consultan brechas
priorizadas; el caso de uso de comparación contra línea base sostiene la
hipótesis de ponderación horaria.

### Componentes y frontera de despliegue

![Componentes](docs/2_componentes.png)

El artefacto `emb.npz` marca la frontera: el pipeline pesado corre offline, el
servicio desplegado solo consume vectores precomputados.

### Modelo de dominio y puertos

![Modelo de dominio](docs/3_clases.png)

Cardinalidad `Programa 1─* Silabo 1─* Unidad`. Los adaptadores se auto-registran,
de modo que incorporar otra universidad es una subclase sin tocar el pipeline.

Los diagramas de secuencia, actividad, despliegue y estados están en
[`docs/arquitectura.md`](docs/arquitectura.md), con sus fuentes `.puml`.

---

## Supuestos del modelo

- Los sílabos del plan 2017-2 declaran créditos pero no horas por capítulo.
  La carga horaria se reparte proporcionalmente entre los capítulos de cada
  curso. La aproximación conserva el peso relativo entre cursos, que es lo que
  importa para priorizar brechas.
- La muestra se limita a sílabos con texto extraíble. Sesgo de selección
  declarado.
- La taxonomía de referencia es europea; su transferencia al contexto peruano
  se sostiene en que las competencias técnicas de ingeniería son
  transversales, no así el contexto regulatorio. Incorporar una fuente de
  demanda local está en el roadmap.

---

## Integrantes & Roles

| Nombre | GitHub | Rol |
|---|---|---|
| Valentino Stefano Alvarado Rojas | @ValentinoAlvarado | núcleo: extracción, normalización, emparejamiento |
| Juan Antonio Ataco León | | datos y métricas |
| Alexander Fabián Zeña Cornejo | | repositorio, pruebas y despliegue |

---

## Estado final

- **URL de producción:**
- **Entregado:**
- **Fuera de alcance (roadmap):**