# Guía del Trabajo 2: sistema RAG

Grupo 3: Alejandro, Miguel y Javier. Repo: https://github.com/JavierCagigal/proy-rag

Esta guía explica qué nos piden, qué vamos a construir, cómo nos repartimos el trabajo y en qué orden. Léela entera una vez antes de empezar; después, cada uno vuelve a su apartado.

---

## 1. Qué nos piden

Un **RAG** (*Retrieval-Augmented Generation*) sobre un subtema de nuestra temática (deporte, nutrición y ejercicio). Hay que **demostrar con pruebas** que responde mejor que el mismo LLM sin contexto: que se inventa menos y da datos concretos y actuales.

| Fase | Qué es | Dónde está en el repo |
|---|---|---|
| **A. Pipeline de datos** | Un script que descarga, limpia y prepara el corpus **sin ningún paso manual**. Las fuentes se pueden mezclar: PDFs, APIs, scraping, datasets. | `src/pipeline.py` |
| **B. Arquitectura** | Un framework (usamos LangChain), una base vectorial (usamos ChromaDB) y un **chunking justificado técnicamente**. | `src/indexar.py`, `src/rag.py` |
| **C. Evaluación** | De 5 a 10 preguntas difíciles y de nicho, respondidas **sin RAG** (se inventa) y **con RAG** (acierta y cita el fragmento). Se documenta la comparativa. | `evaluacion/preguntas.csv`, `src/evaluar.py` |
| **D. Interfaz** | App en Streamlit desplegada públicamente (Streamlit Cloud o Hugging Face Spaces). | `app.py` |
| **E. Extra (opcional)** | Reranking, filtros por metadatos o búsqueda híbrida (BM25 + vectorial). | lo que toque |

**Entrega:** el código en `rag_project/` y una web de Quarto en GitHub Pages con la motivación, el pipeline, el chunking, los resultados de la comparativa, los enlaces a la app y al repo, y extractos de código explicados. La URL se comparte en Loop.

**Exposición:** cada uno defiende su parte y se valora el dominio técnico **individual**. Por eso cada uno escribe el código de su parte y entiende el de los demás.

---

## 2. El tema: asistente de competición para triatletas ✅ decidido

Un asistente que contesta lo que un triatleta pregunta antes de una carrera y un chatbot genérico contesta mal. Tiene dos partes:

1. **Reglamento y antidopaje**: penalizaciones, neopreno, transiciones y qué sustancias están prohibidas.
2. **"¿Me da positivo?"**: el deportista escribe el **nombre comercial** de un medicamento español ("Ventolin", "Frenadol"…). El RAG encuentra su principio activo y su vía de administración en CIMA (la base de datos de la Agencia Española del Medicamento) y lo cruza con la lista de la WADA.

### Por qué triatlón y no "gimnasio" en general

La nota depende de **demostrar que el RAG gana al LLM solo**. Eso pasa cuando la respuesta es:

- **Concreta**: una cifra, un tiempo de penalización o una temperatura exacta.
- **Actual**: algo que cambia cada año (el reglamento, la lista de sustancias prohibidas).
- **De nicho**: algo que aparece poco en internet y el modelo no ha memorizado bien.

Del gimnasio "en general" (cuántas series hacer, qué es una sentadilla…) el LLM ya sabe bastante, así que la diferencia con RAG sería pequeña y difícil de enseñar. El reglamento de triatlón o la lista de la WADA de este año son justo lo contrario: el LLM se inventa la cifra o da la de una versión antigua, y el RAG la saca del documento y cita la página. Con los medicamentos pasa lo mismo: el LLM no conoce los nombres comerciales españoles ni sabe qué vía de administración tiene cada presentación, y la vía cambia la respuesta (un mismo principio activo puede estar permitido inhalado y prohibido en jarabe o inyectado).

### Fuentes (P1 confirma las URLs vigentes y la licencia)

| Fuente | Tipo | Para qué preguntas |
|---|---|---|
| Reglamento de competición de World Triathlon (el vigente) | PDF | Drafting, penalizaciones, neopreno, transiciones |
| Reglamento de competiciones de la Federación Española de Triatlón | PDF | Lo mismo, en español y con normas nacionales |
| Lista de sustancias prohibidas de la WADA del año en curso | PDF | "¿Está prohibido X? ¿Solo en competición? ¿Por qué vía?" |
| **CIMA** (Agencia Española del Medicamento) | API REST, gratis y sin clave | "¿Qué lleva el medicamento X y cómo se toma?" |

Así cumplimos lo de mezclar fuentes (PDF + API) y todo se descarga desde el script.

**Cómo usar CIMA** (comprobado el 20/11):
- `https://cima.aemps.es/cima/rest/medicamentos?practiv1=salbutamol` devuelve los medicamentos que llevan ese principio activo (con salbutamol salen 20). Cada uno trae su nombre comercial, `viasAdministracion` y si necesita receta.
- `https://cima.aemps.es/cima/rest/medicamento?nregistro=...` devuelve el detalle de uno, con `principiosActivos` y su cantidad.
- No se descargan los 20.000 medicamentos de España: el pipeline tiene una **lista de unos 20-30 principios activos** que importan en el deporte (broncodilatadores para el asma, corticoides, descongestionantes como la pseudoefedrina, analgésicos, estimulantes…) y baja los medicamentos de cada uno. Cada medicamento se convierte en un texto corto para el corpus, por ejemplo: *"VENTOLIN 100 microgramos/inhalación. Principio activo: salbutamol. Vía: inhalatoria. Con receta."*

### Proyección

- **Se actualiza sin reentrenar**: cuando salga el reglamento o la lista WADA del año que viene, basta con volver a ejecutar `pipeline.py` e `indexar.py`. Es el mejor argumento para la exposición: un modelo entrenado se queda anticuado y un RAG no.
- **Tiene uso real**: "¿este medicamento me da positivo?" o "¿me dejan usar neopreno con el agua a 22 °C?" son preguntas que un deportista se hace de verdad, y la respuesta tiene que ser exacta y con fuente.
- **Encaja con nuestros otros proyectos de deporte**: más adelante se podría conectar con datos de entrenamiento (Garmin, por ejemplo) para responder sobre los entrenos de cada uno. Eso queda **fuera** de este trabajo.

> **Plan B si vamos justos de tiempo:** la parte 2 (CIMA) es la más difícil. Si no llega, se entrega solo la parte 1 y la 2 se cuenta en la exposición como mejora futura.

---

## 3. Cómo funciona un RAG (lo que tenemos que saber explicar)

```
                 UNA VEZ (preparar)                                CADA PREGUNTA (responder)
 ┌────────────┐   ┌───────────────┐   ┌──────────┐   ┌────────┐     pregunta del usuario
 │ PDFs, API, │ → │ pipeline.py   │ → │ trocear  │ → │ Chroma │            │
 │ dataset    │   │ corpus.jsonl  │   │ (chunks) │   │ (base  │ ←── embedding de la pregunta
 └────────────┘   └───────────────┘   │ + embed. │   │ vecto- │            │
                                      └──────────┘   │ rial)  │ ──→ los 4 trozos más parecidos
                                                     └────────┘            │
                                                         prompt = instrucciones + trozos + pregunta
                                                                           │
                                                                   LLM → respuesta con citas
```

1. **Corpus**: el texto limpio de todas las fuentes, con de dónde sale cada página.
2. **Chunking**: partir el texto en trozos. Un trozo pequeño es preciso pero puede cortar la respuesta por la mitad; uno grande la contiene, pero mete ruido y se parece menos a la pregunta. Por eso lo medimos.
3. **Embedding**: convertir cada trozo en un vector de números de forma que textos con significado parecido den vectores cercanos. Lo hace un modelo pequeño (`multilingual-e5-small`), no el LLM.
4. **Base vectorial** (Chroma): guarda los vectores y encuentra rápido los más cercanos a la pregunta.
5. **Generación**: el LLM recibe la pregunta **junto con** los trozos recuperados y la orden de responder solo con eso y citar la fuente.

La idea clave: **el LLM no aprende nada nuevo**; le damos los apuntes en el momento de la pregunta.

### La comparativa: el mismo modelo con y sin apuntes

El RAG **usa Ollama por dentro**: no son dos modelos distintos. En la evaluación se le hace la misma pregunta al mismo modelo (qwen2.5:3b) de dos formas: **sin RAG** (solo la pregunta, contesta de memoria) y **con RAG** (la pregunta + los trozos recuperados). Como lo único que cambia es el contexto, la diferencia en las respuestas se debe al RAG.

### Las preguntas de medicamentos: recuperar en dos pasos

*"¿Puedo competir si uso Ventolin?"* tiene un problema: la lista de la WADA habla de **salbutamol** y nunca dice "Ventolin", así que una sola búsqueda no encuentra los dos trozos que hacen falta. Por eso `recuperar()` busca en dos pasos:

1. Busca con la pregunta → sale el trozo de CIMA de Ventolin, que dice que su principio activo es el salbutamol.
2. Vuelve a buscar con *"salbutamol"* → sale el trozo de la WADA que habla del salbutamol.
3. Se le pasan al LLM los trozos de las dos búsquedas.

Esto se llama **expansión de la consulta** y es un buen punto técnico para la exposición. El principio activo del paso 2 se saca de la metadata del trozo de CIMA (por eso `pipeline.py` lo guarda aparte, en el campo `principio_activo`).

---

## 4. Decisiones técnicas (y cómo justificarlas)

| Decisión | Elegimos | Por qué (para defenderlo) |
|---|---|---|
| Framework | **LangChain** | Tiene cargadores de PDF, *splitters*, Chroma y Ollama integrados. Es el que más ejemplos tiene. |
| Base vectorial | **ChromaDB** | Funciona en local, sin servidor, y se guarda en una carpeta. Para unos miles de trozos sobra. |
| Embeddings | **intfloat/multilingual-e5-small** | Gratis, corre en CPU y es **multilingüe**: preguntamos en español y muchos documentos están en inglés. Lee como mucho 512 tokens por trozo, lo que pone un techo al tamaño de trozo. |
| Chunking | `RecursiveCharacterTextSplitter`, **comparando 300, 800 y 1500 caracteres** con solape de 100 | Corta primero por párrafos, luego por frases y luego por palabras. El tamaño final lo elige el experimento, no una opinión (igual que los hiperparámetros del Trabajo 1). |
| LLM | **Ollama + qwen2.5:3b** en local | Funciona sin internet y sin coste. Es pequeño, así que sin contexto se inventa cosas, y eso hace la comparativa más clara. |
| LLM en la nube | **Pendiente** (ver apartado 10) | Streamlit Cloud no puede ejecutar Ollama. `llamar_llm()` es el único sitio que cambia. |
| Interfaz | **Streamlit** | Una app en un único archivo Python, y Streamlit Cloud despliega directamente desde el repo de GitHub. |

**Qué une cada parte (no se cambia sin avisar a los otros):**

- `pipeline.py` genera `data/processed/corpus.jsonl` con una línea por página de PDF y una por medicamento:
  `{"fuente": "reglamento_world_triathlon", "url": "https://...", "pagina": 12, "texto": "..."}`
  `{"fuente": "cima", "url": "https://cima.aemps.es/...", "pagina": null, "principio_activo": "salbutamol", "texto": "VENTOLIN 100 microgramos..."}`
- `indexar.py` crea en `chroma/` las colecciones `trozos_300`, `trozos_800` y `trozos_1500`.
- `rag.py` ofrece `cargar_base()`, `recuperar(base, pregunta)`, `responder_sin_rag(pregunta)` y `responder_con_rag(base, pregunta) → (respuesta, trozos)`. La app y `evaluar.py` solo usan estas funciones.

---

## 5. Estructura del repo

```
proy-rag/
├── GUIA_PROYECTO.md          ← esta guía
├── README.md                 instalación y cómo ejecutar
├── requirements.txt          librerías (sin versiones)
├── _quarto.yml, index.qmd    la web (portada)
└── rag_project/
    ├── src/
    │   ├── pipeline.py       A  · P1
    │   ├── indexar.py        B  · P2
    │   ├── rag.py            B  · P3 (recuperar() con P2)
    │   └── evaluar.py        C  · P2
    ├── app.py                D  · P3
    ├── evaluacion/
    │   └── preguntas.csv     C  · todos
    ├── data/raw/             descargas originales (no se suben)
    ├── data/processed/       corpus.jsonl (sí se sube)
    ├── chroma/               base vectorial (no se sube: se regenera)
    ├── resultados/           comparativa.csv y chunking.csv (sí se suben)
    ├── 01-datos.qmd          P1
    ├── 02-arquitectura.qmd   P2
    ├── 03-evaluacion.qmd     P2
    └── 04-app-y-conclusiones.qmd   P3 + todos
```

Los `.py` son **esqueletos**: cada función tiene su explicación y los pasos en comentarios, y tiene que rellenarla quien la va a defender. Cada `.qmd` lleva un comentario con lo que debe contar.

---

## 6. Reparto en 3 roles

La guía del profesor pone 4 roles de ejemplo; somos 3, así que los juntamos así:

### P1: Datos (fase A)
- **Archivos**: `src/pipeline.py`, `01-datos.qmd`.
- **Hace**: la descarga de los 3 PDFs, la extracción de texto página a página y la limpieza; la lista de principios activos y la descarga desde la API de CIMA; y genera `corpus.jsonl`.
- **Defiende**: de dónde salen los datos, por qué esas fuentes, cómo se automatiza todo, por qué esos principios activos y qué problemas de limpieza hubo (cabeceras repetidas, tablas que el PDF rompe…).
- **Orden**: primero los PDFs (con eso P2 y P3 ya pueden trabajar) y después CIMA.

### P2: Recuperación y evaluación (fases B y C)
- **Archivos**: `src/indexar.py`, `recuperar()` en `src/rag.py`, `src/evaluar.py`, `02-arquitectura.qmd`, `03-evaluacion.qmd`.
- **Hace**: el chunking y los embeddings, la base Chroma, la recuperación en dos pasos para los medicamentos, el experimento de tamaños de trozo y la comparativa sin RAG / con RAG.
- **Defiende**: qué es un embedding, por qué ese modelo, el tamaño de trozo elegido **con datos**, la expansión de la consulta y los resultados de la comparativa.
- **Extra si va por delante (fase E)**: búsqueda híbrida (BM25 + vectorial). Aquí está muy justificada: los nombres de medicamentos y sustancias son **palabras exactas**, y en eso BM25 acierta más que los embeddings. Hay que medir si mejora con las mismas preguntas.

### P3: Generación, app y web (fase D + web)
- **Archivos**: el resto de `src/rag.py` (prompt y LLM), `app.py`, `_quarto.yml`, `index.qmd`, `04-app-y-conclusiones.qmd`, el despliegue y la publicación.
- **Hace**: el prompt, la conexión con el LLM, la app de Streamlit, el despliegue y la web.
- **Defiende**: cómo se construye el prompt y por qué obliga a citar, qué LLM se usa y por qué, cómo está desplegado.

### Todos
- Escribir juntos las **preguntas de evaluación** (lo primero de todo, ver apartado 8).
- Poner los **veredictos** de la comparativa (uno lo propone y otro lo revisa).
- Las conclusiones y el ensayo de la exposición.

### Cómo no bloquearnos unos a otros
- **P1 entrega una primera versión del corpus en 1-2 días con una sola fuente** (el reglamento, por ejemplo). Con eso P2 y P3 ya pueden trabajar; el resto de fuentes se añaden después sin cambiar nada más.
- **P3 monta la app con una respuesta falsa** mientras `rag.py` no está listo.
- **P2 puede probar el chunking con cualquier PDF** mientras llega el corpus de verdad.

---

## 7. Plan y ritmo

> ⚠️ **Fecha de entrega sin confirmar.** Los días cuentan desde que empezamos (día 1 = el primer día de trabajo). Si no hay tiempo para todo: primero la parte 1 completa (hitos 1-5) y CIMA solo si sobra margen.

| Hito | Días | Qué tiene que estar | Quién |
|---|---|---|---|
| **0. Arranque** | día 1 | Todos instalan (README) y ejecutan `quarto preview`. **Preguntas escritas.** URLs de los 3 PDFs confirmadas. | Todos |
| **1. Primera versión de punta a punta** | días 2-3 | Una pregunta sobre el reglamento → respuesta con cita en local (un PDF y un solo tamaño de trozo). | P1 → P2 → P3 |
| **2. Corpus completo + evaluación** | días 4-5 | Los 3 PDFs + CIMA en el corpus, recuperación en dos pasos. `comparativa.csv` y `chunking.csv` generados y con veredictos. | P1, P2 |
| **3. Despliegue** | días 4-6 | App pública funcionando con su URL. | P3 |
| **4. Web** | días 6-7 | Las 4 páginas de Quarto con texto, código y resultados. Fase E si da tiempo. | Todos |
| **5. Cierre** | día 8 | PR `test` → `master`, publicar la web, URL en Loop, ensayo. | Todos |

**Tiempo estimado por tarea** (orientativo, para gente que empieza con Python):

| Tarea | Horas | Dificultad |
|---|---|---|
| Descargar PDFs y extraer el texto página a página | 3 | baja |
| Lista de principios activos + descarga desde CIMA | 3 | media |
| Limpieza del texto | 2 | media |
| Chunking + embeddings + Chroma | 3 | media |
| Recuperación en dos pasos (medicamentos) | 2-3 | media-alta |
| Experimento de chunking | 2-3 | media |
| `rag.py` (prompt + Ollama) | 2-3 | media |
| Comparativa + veredictos | 3 | baja (mucha lectura) |
| App de Streamlit | 2-3 | baja |
| Despliegue con LLM en la nube | 2-4 | media-alta |
| Cada página de Quarto | 2 | baja |
| Fase E (híbrido o reranking) | 3-4 | alta |

---

## 8. Las preguntas de evaluación (empezamos por aquí)

Se escriben **antes** de buscar fuentes, porque son las que deciden qué documentos necesitamos. Van en `evaluacion/preguntas.csv` con las columnas `id, pregunta, respuesta_esperada, fuente` (la respuesta esperada, sacada del documento a mano).

**Cómo tiene que ser una buena pregunta:** tiene una respuesta exacta en nuestras fuentes, es difícil de acertar de memoria y se puede comprobar. Por ejemplo:

1. ¿Cuánto tiempo de penalización hay por *drafting* en una prueba de grupos de edad, según el reglamento de World Triathlon?
2. ¿A partir de qué temperatura del agua está prohibido el neopreno en una prueba de distancia estándar?
3. ¿Qué pasa si un triatleta deja el casco desabrochado al coger la bici?
4. ¿Está prohibida en competición [una sustancia concreta] según la lista WADA de este año? ¿Y fuera de competición?
5. Tengo asma y uso Ventolin inhalado, ¿puedo usarlo el día de la carrera? ¿Hay un límite de dosis?
6. Estoy resfriado, ¿me da positivo tomar [un antigripal con pseudoefedrina] antes de una prueba?
7. ¿Qué cambió en el reglamento de este año respecto al anterior? (aquí el LLM falla seguro)
8. Una pregunta cuya respuesta **no** esté en el corpus, para comprobar que con RAG dice "no lo sé" en vez de inventar.

En las de medicamentos, la respuesta esperada se comprueba a mano en CIMA y en la lista de la WADA, y se apuntan las dos fuentes.

**Veredictos** (columnas a mano en `comparativa.csv`): `correcta`, `parcial`, `inventada` o `no sabe`. El resultado final es una tabla del tipo "sin RAG: 2 correctas de 8; con RAG: 7 de 8".

---

## 9. Git

- `master` y `test` están protegidas: **nada de push directo**, todo por PR.
- Antes de empezar una tarea: `git switch test && git pull && git switch -c datos/descarga-pdfs`.
- Prefijos: `datos/`, `rag/`, `eval/`, `app/`, `web/`, `infra/`.
- Commits pequeños que empiezan por la parte: `Datos: descarga del reglamento de World Triathlon`.
- PR hacia `test` → **lo revisa otro compañero** antes de aceptarlo (así los tres conocemos todo el código).
- Al final: PR `test` → `master` y `quarto publish gh-pages` desde `master`.

---

## 10. Pendiente de decidir

1. ~~Tema~~ → ✅ asistente de competición para triatletas: reglamento y antidopaje + medicamentos (20/11).
2. **Fecha de entrega real.**
3. **¿"Sin wifi" es una exigencia firme?** Si el profesor quiere verlo funcionar sin internet, la demo de la exposición se hace en local con Ollama y la app en la nube es la versión pública. Para la nube hay que elegir el LLM:
   - Una API con capa gratuita (se guarda la clave como *secret* en Streamlit Cloud, nunca en el repo).
   - Un modelo pequeño en Hugging Face Spaces (más lento y más configuración).
4. **Quién es P1, P2 y P3.**
5. **¿Vamos a por la fase E?** Mi consejo: primero todo lo obligatorio (hito 4) y luego el extra.

---

## 11. Si usáis una IA (Antigravity, Claude, ChatGPT…)

Las reglas y las decisiones ya tomadas para la IA están en [AGENTS.md](AGENTS.md). Si vuestro agente no lo lee solo, pegadle esto al empezar:

> Estoy en un proyecto de clase (RAG con LangChain + Chroma + Ollama + Streamlit). Somos novatos en Python y cada uno tiene que **defender su código en una exposición**. Lee `AGENTS.md` y `GUIA_PROYECTO.md`. **Guíame, no me lo escribas**: explícame los pasos, revisa mi código, encuentra errores y propón correcciones pequeñas. Código completo solo si te lo pido expresamente. Respeta lo que une cada parte (apartado 4) y no añadas librerías sin preguntar. Responde en español.
