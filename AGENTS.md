# Contexto para agentes de IA

Léelo antes de hacer nada en este repo. Aquí están las reglas y las decisiones ya tomadas (y su porqué), para no volver a discutirlas. El detalle técnico y el plan están en [GUIA_PROYECTO.md](GUIA_PROYECTO.md).

## El proyecto

- **Trabajo 2 de clase: un sistema RAG.** Grupo 3: Alejandro, Miguel y Javier.
- **Tema**: asistente de competición para triatletas. Responde sobre reglamento y antidopaje, y sobre medicamentos ("¿me da positivo?").
- **Repo**: https://github.com/JavierCagigal/proy-rag. El código va en `rag_project/` y la web de Quarto (raíz + páginas `.qmd` en `rag_project/`) se publica en GitHub Pages.
- **Fases que pide el profesor**:
  - A: pipeline de datos automático.
  - B: framework + base vectorial + chunking justificado.
  - C: de 5 a 10 preguntas de nicho, respondidas sin RAG y con RAG.
  - D: app desplegada públicamente.
  - E (opcional): híbrido, reranking o filtros.
- **Exposición**: cada uno defiende su parte, y se evalúa el dominio técnico individual.

## Reglas para la IA

1. **Código: lo escribe Javier con la IA (desde el 20/11).** La exposición sigue repartida (cada uno defiende su parte), así que todo lo que se añade se explica en [PASOS.md](PASOS.md): qué es, para qué sirve y por qué está así. Código sencillo, comentarios que expliquen el porqué y nada que no se sepa defender.
2. **Todo en español**: respuestas, comentarios, nombres de variables y commits.
3. **Git**: `master` y `test` están protegidas y todo entra por PR. Ramas cortas desde `test` con prefijo `datos/`, `rag/`, `eval/`, `app/`, `web/` o `infra/`. Commits que empiecen por la parte (por ejemplo, `Datos: descarga del reglamento`). Al final del proyecto, PR de `test` a `master` y publicar desde `master`.
4. **No subir** `data/raw/`, `chroma/`, `.venv/` ni `.env`, y nunca poner claves en el código.
5. **Preguntar antes de**: añadir dependencias, cambiar lo que une cada parte (ver abajo), forzar un push, borrar ramas o archivos y publicar la web.
6. Los `.py` de `rag_project/src/` y `app.py` son **esqueletos**: cada función tiene su explicación y los pasos en comentarios. Respeta los nombres y las firmas.

## Decisiones tomadas

| Fecha | Decisión | Por qué |
|---|---|---|
| 06/11 | Repo nuevo y público `proy-rag`, montado igual que el del Trabajo 1 (`proy-redesneuronales`): `master` + `test` protegidas y PR obligatorio | Mismo flujo que ya conocemos |
| 06/11 | Código en `rag_project/` + web de Quarto con 4 páginas: 01-datos, 02-arquitectura, 03-evaluacion, 04-app-y-conclusiones (el 20/11 pasan a 5, ver abajo) | Lo pide la entrega |
| 06/11 | Tema de deporte en vez del Nutri-Score del Trabajo 1 | Lo eligió el grupo |
| 20/11 | **Tema: ideas 1 + 2.** (1) Reglamento de World Triathlon y de la Federación Española de Triatlón + lista de prohibidas de la WADA, en PDF. (2) "¿Me da positivo?": API de CIMA (AEMPS) para pasar del nombre comercial al principio activo y a la vía de administración, y cruzarlo con la WADA | El RAG gana cuando la respuesta es concreta, actual y de nicho (cifras del reglamento, la lista de este año, nombres comerciales españoles). Mezcla PDF y API, como pide la fase A |
| 20/11 | Descartados: gimnasio en general, suplementos (ISSN), calendario de carreras por scraping y datos de Garmin | Gimnasio y suplementos: el LLM ya sabe bastante y la comparativa luce poco. Scraping: frágil. Garmin: son datos numéricos y para eso hace falta SQL, no un RAG |
| 06/11 | **LangChain + ChromaDB** | Integra cargadores, *splitters*, Chroma y Ollama. Chroma funciona en local, sin servidor |
| 06/11 | Embeddings **intfloat/multilingual-e5-small** | Multilingüe (preguntas en español, documentos en inglés), corre en CPU. Máximo 512 tokens por trozo. Necesita los prefijos `query: ` y `passage: ` |
| 06/11 | Chunking con `RecursiveCharacterTextSplitter`, comparando **300, 800 y 1500 caracteres** con solape de 100. Una colección por tamaño (`trozos_300`…) | El tamaño se elige midiendo, como los hiperparámetros del Trabajo 1 |
| 06/11 | LLM: **Ollama + `qwen2.5:3b`** en local | Gratis y sin internet. Al ser pequeño se inventa más sin RAG, así que la comparativa se ve mejor |
| 20/11 | **La comparativa usa el mismo modelo** con la misma pregunta, sin contexto y con los trozos recuperados | Solo cambia el contexto, así que la diferencia se debe al RAG |
| 20/11 | **Recuperación en dos pasos** para los medicamentos (expansión de la consulta): pregunta → trozo de CIMA → su `principio_activo` → segunda búsqueda en las fuentes que no son CIMA | La WADA dice "salbutamol", no "Ventolin": con una sola búsqueda no salen los dos trozos |
| 20/11 | CIMA: se descarga una lista de **20-30 principios activos relevantes**, no todo el catálogo. Un texto corto por medicamento | Suficiente para las preguntas y rápido de indexar |
| 20/11 | Fase E (si da tiempo): **BM25 + vectorial** | Los nombres de medicamentos y sustancias son palabras exactas, y ahí BM25 acierta más |
| 20/11 | Plan B: si no da tiempo, se entrega solo la idea 1 y la 2 se presenta como mejora futura | CIMA es la parte más difícil |
| 20/11 | Interfaz en **Streamlit** | Un solo archivo (se despliega en Cloud Run, ver 21/11) |
| 20/11 | **Reparto**: P1 Miguel, P2 Javier, P3 Alejandro. P1 lleva también las preguntas de evaluación y las conclusiones | La parte de datos es la más corta y P1 es quien más lee los PDFs; así abre y cierra el proyecto |
| 20/11 | La web pasa a **5 páginas**: la 04 se separa en `04-app.qmd` (P3) y `05-conclusiones.qmd` (P1) | Cada página tiene un solo responsable y no se pisan en git |
| 20/11 | **Javier escribe todo el código con la IA**; Miguel y Alejandro exponen su parte. Se lleva un diario en `PASOS.md` | Decisión del grupo. El diario es para que cada uno pueda defender lo que expone |
| 20/11 | Fuentes: World Triathlon Competition Rules 2026, FETRI Reglamento de Competiciones 2026 (Circular 4/26), WADA 2026 Prohibited List (inglés). Las URL están en `pipeline.py` | Las vigentes en las webs oficiales el 20/11. La WADA exige `User-Agent` de navegador |
| 20/11 | CIMA: **24 principios activos**, solo medicamentos comercializados y de marca (637) | Los genéricos ya llevan el principio activo en el nombre; las marcas son lo que el LLM no sabe |
| 20/11 | `preguntas.csv` lleva además la columna `dato_clave` (regex del dato exacto); en `fuente`, `+` = hacen falta las dos y `\|` = vale cualquiera | Mide si el trozo contiene la cifra y no solo la página; la FETRI copia el reglamento de World Triathlon |
| 20/11 | **Tamaño de trozo: 800** (dato exacto en 8/9 preguntas; 300 → 4/9; 1500 → 8/9 con un 77 % más de texto) | Medido con `evaluar.py chunking` |
| 20/11 | `recuperar()`: búsqueda general + búsqueda solo en CIMA con umbral 0,85; si es de medicamentos, contexto = CIMA (2) + WADA por significado y por palabra exacta (`$contains`). `pipeline.py` descarta las páginas de índice alfabético | Cada paso arregla un fallo medido; detalle en PASOS.md, apartados 2 y 5 |
| 20/11 | Resultado con qwen2.5:3b: sin RAG 0 correctas y 9 inventadas; con RAG 2 correctas, 4 parciales, 2 inventadas y 2 "no sabe" (veredictos propuestos, por revisar) | La recuperación acierta 8/9; el cuello de botella es leer el contexto con un modelo de 3B. Con 3 GB libres no cabe uno local mayor |
| 20/11 | Ollama con `num_ctx=8192` y `temperature=0` | Sin `num_ctx` Ollama corta el contexto sin avisar; temperatura 0 para que la comparativa se pueda repetir |
| 24/11 | **Despliegue en Google Cloud Run con Gemini** (`gemini-3.5-flash-lite`) por API: `llamar_llm()` usa Gemini si existe `GEMINI_API_KEY` y Ollama si no. La clave va en Secret Manager | El 21/11 se probó Ollama dentro del contenedor y se descartó (imagen de ~6 GB, 10-30 s por respuesta, más coste). Flash-Lite: plan gratuito, el más rápido y aún respeta `temperature=0`. Detalle en PASOS.md, apartado 8 |
| 24/11 | **Segunda comparativa con Gemini** (`comparativa_gemini.csv`): sin RAG 3 correctas y 4 inventadas; con RAG 7 correctas y 0 inventadas (veredictos por revisar). `llamar_llm()` reintenta ante 429/5xx y une todas las partes de la respuesta | Mismo modelo que la app publicada; demuestra que con un modelo mayor el RAG acierta mucho más. Los reintentos, porque el plan gratuito da 503 a menudo |
| 24/11 | **Guía de estudio** `GUIA_ESTUDIO.qmd` → PDF con Quarto + typst, separada por persona | Para que cada uno defienda su parte |

## Lo que une cada parte (no se cambia sin avisar al resto)

- `pipeline.py` → `data/processed/corpus.jsonl`, con una línea por página de PDF y una por medicamento:
  - `{"fuente", "url", "pagina", "texto"}`
  - y en CIMA, además, `"principio_activo"` (con `"pagina": null`).
- `indexar.py` → colecciones de Chroma `trozos_300`, `trozos_800` y `trozos_1500` en `rag_project/chroma/`.
- `rag.py` → `cargar_base()`, `recuperar(base, pregunta)`, `responder_sin_rag(pregunta)` y `responder_con_rag(base, pregunta) → (respuesta, trozos)`.
  - La app y `evaluar.py` solo usan estas funciones.
  - `llamar_llm()` es el único sitio que sabe qué LLM se usa (qwen en local, Gemini si hay `GEMINI_API_KEY`).

## API de CIMA (comprobada el 20/11)

- `https://cima.aemps.es/cima/rest/medicamentos?nombre=ventolin` → 5 presentaciones. Cada una trae `nombre`, `viasAdministracion` y `receta`; `pactivos` llega vacío en este listado.
- `https://cima.aemps.es/cima/rest/medicamentos?practiv1=salbutamol` → 20 medicamentos.
- `https://cima.aemps.es/cima/rest/medicamento?nregistro=...` → el detalle, con `principiosActivos`.
- Va por páginas: `totalFilas`, `pagina` y `tamanioPagina`.

## Reparto

- **P1, datos, preguntas y conclusiones (Miguel)**: `pipeline.py`, `preguntas.csv` (reúne y comprueba las preguntas de evaluación) y las páginas 01 y 05.
- **P2, recuperación y evaluación (Javier)**: `indexar.py`, `recuperar()`, `evaluar.py` y las páginas 02 y 03.
- **P3, generación, app y web (Alejandro)**: el resto de `rag.py`, `app.py`, el despliegue, Quarto y la página 04.
- **Todos**: proponer preguntas, veredictos (uno propone y otro revisa) e ideas para las conclusiones.

## Estado (20/11)

- En `test`: la guía, los esqueletos, el tema y este archivo (PR #1, #2 y #3). El PR #4 (reparto) está abierto.
- Rama `datos/pipeline` (encima del PR #4): fases A, B y C hechas y probadas en el Mac de Javier. `pipeline.py`, `indexar.py`, `rag.py`, `evaluar.py`, `app.py`, `preguntas.csv` (10 preguntas), `corpus.jsonl`, `resultados/chunking.csv` y `comparativa.csv`. El diario está en `PASOS.md`.
- En el Mac de Javier: `.venv` con Python 3.14 y todo `requirements.txt`. Ollama con `qwen2.5:3b` funcionando.
- **App desplegada (24/11)**: https://asistente-triatlon-921790710609.europe-west1.run.app (Cloud Run, proyecto `asistente-triatlon`, 2 CPU / 4 GB, Gemini con la clave en Secret Manager). Web completa en la rama `web/paginas` (PR #6).

## Pendiente

- Fecha de entrega real (sin confirmar).
- Veredictos de las dos comparativas (qwen y Gemini), revisados por el grupo.
- Publicar la web y subir la URL a Loop.
- Si el profesor exige que funcione sin wifi.
- Invitar a Alejandro y Miguel como colaboradores del repo.
