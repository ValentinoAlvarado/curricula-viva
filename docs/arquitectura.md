# Arquitectura — Currícula Viva

Los diagramas se generan desde los `.puml` de esta misma carpeta:

```bash
cd docs
java -jar plantuml.jar -tpng *.puml
```

`comun.puml` define la paleta y se incluye en todos.

| # | Diagrama | Fuente | Imagen |
|---|---|---|---|
| 1 | Casos de uso | `1_casos_uso.puml` | `1_casos_uso.png` |
| 2 | Componentes | `2_componentes.puml` | `2_componentes.png` |
| 3 | Clases y puertos | `3_clases.puml` | `3_clases.png` |
| 4 | Secuencia | `4_secuencia.puml` | `4_secuencia.png` |
| 5 | Actividad | `5_actividad.puml` | `5_actividad.png` |
| 6 | Despliegue | `6_despliegue.puml` | `6_despliegue.png` |
| 7 | Estados | `7_estados.puml` | `7_estados.png` |

---

## 1. Casos de uso

![Casos de uso](1_casos_uso.png)

## 2. Componentes y frontera de despliegue

![Componentes](2_componentes.png)

## 3. Modelo de dominio y puertos

![Clases](3_clases.png)

## 4. Secuencia de una consulta

![Secuencia](4_secuencia.png)

## 5. Actividad del pipeline offline

![Actividad](5_actividad.png)

## 6. Despliegue

![Despliegue](6_despliegue.png)

## 7. Estados de una competencia

![Estados](7_estados.png)

---

Los bloques Mermaid siguientes son una vista alternativa embebida.

## Vista de componentes

```mermaid
flowchart LR
    subgraph OFF["Offline · máquina local"]
        PDF[(Sílabos PDF)] --> EXT[Extracción<br/>PyMuPDF + regex]
        ESCO[(ESCO v1.2.1 es)] --> NRM[Normalización<br/>taxonomía]
        EXT --> NRM
        NRM --> EMB[Encoding<br/>MiniLM multilingüe]
    end

    EMB --> ART[("artifacts/<br/>embeddings.npz")]

    subgraph ON["Online · servicio desplegado"]
        ART --> MCH[Emparejamiento<br/>coseno + umbral]
        MCH --> PND[Ponderación<br/>por carga horaria]
        PND --> REP[Informe de brechas<br/>trazable a unidades]
        REP --> UI[Interfaz Streamlit]
    end
```

El artefacto marca la frontera de despliegue. El servicio no carga el modelo
de representación: runtime de tres paquetes, sin torch. Verificado.

## Modelo de dominio

```mermaid
classDiagram
    class Programa {
        +codigo: str
        +nombre: str
        +horasTotales() int
    }
    class Silabo {
        +codigo: str
        +periodo: str
        +creditos: int
        +horasTotales() int
    }
    class Unidad {
        +numero: int
        +nombre: str
        +horas: int
        +temas: list
    }
    class Competencia {
        +uri: str
        +etiqueta: str
        +tipo: str
        +esencial: bool
    }
    class Cobertura {
        +pesoDemanda: float
        +horasAsignadas: int
        +similitudMax: float
        +severidad() float
    }

    Programa "1" *-- "1..*" Silabo : agrega
    Silabo "1" *-- "1..*" Unidad : agrega
    Cobertura "*" --> "1" Competencia : evalúa
    Unidad "*" -- "*" Competencia : resuelto por Cobertura
```

## Puertos y adaptadores

```mermaid
classDiagram
    class LectorSilabo {
        <<abstract>>
        +acepta(ruta) bool
        +leer(ruta) Silabo
        +para(ruta)$ LectorSilabo
    }
    class LectorUNI {
        +clave = "uni"
    }
    class FuenteDemanda {
        <<abstract>>
        +obtener(limite) list
    }
    class FuenteESCO {
        +clave = "esco"
    }

    LectorSilabo <|.. LectorUNI
    FuenteDemanda <|.. FuenteESCO
```

Las subclases se auto-registran mediante `__init_subclass__`, de modo que el
despacho ocurre sin cadenas de condicionales. Incorporar otra universidad
requiere una subclase nueva y ningún cambio en el pipeline: ese es el
mecanismo de escalabilidad, no una promesa.

## Flujo de una consulta

```mermaid
sequenceDiagram
    actor C as Coordinador
    participant UI as Interfaz
    participant M as Emparejamiento
    participant A as artifacts/

    C->>UI: selecciona programa
    UI->>A: carga vectores
    A-->>UI: matriz de embeddings
    UI->>M: vectores de oferta y demanda
    M->>M: coseno + umbral + ponderación horaria
    M-->>UI: coberturas ordenadas por severidad
    UI-->>C: informe con evidencia por unidad
```

## Decisiones y alternativas descartadas

| Decisión | Alternativa | Razón |
|---|---|---|
| Embeddings precomputados como artefacto | Modelo en el servicio | cientos de MB; excede el plan de entrada del proveedor |
| Coseno determinista | Clasificador entrenado | sin datos etiquetados; la trazabilidad es requisito |
| NumPy | FAISS | miles de vectores: sobreingeniería visible |
| Ponderación por carga horaria | Emparejamiento binario | convierte una coincidencia en una medida |
| ESCO como taxonomía y demanda | Scraping de portales de empleo | el portal del MTPE deniega acceso automatizado |
| Adaptadores por institución | Parser único | dos plantillas incompatibles entre planes 2017-2 y 2018-2 |

## Límites conocidos

- Reparto proporcional de horas por capítulo en el plan 2017-2.
- Muestra restringida a sílabos con texto extraíble.
- Taxonomía europea aplicada a contexto peruano.
- Sin frecuencias de demanda local; ESCO aporta esencialidad, no volumen de
  mercado.

## Ruta de despliegue

```mermaid
flowchart LR
    DEV[Máquina local<br/>pipeline offline] -->|artifacts/emb.npz| REPO[(GitHub)]
    REPO -->|build automático| RENDER[Render<br/>requirements.txt]
    RENDER -->|HTTPS| NAV[Navegador]
```

El repositorio versiona el artefacto precomputado. El proveedor de despliegue
instala únicamente el runtime declarado en `requirements.txt` — tres paquetes,
sin el modelo de representación — y sirve la interfaz por HTTPS. El pipeline
offline nunca se ejecuta en producción.