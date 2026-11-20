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

1. **Guía, no generes.** Somos novatos en Python y cada uno defiende su código. Explica los pasos, revisa el código, localiza errores y propón correcciones pequeñas. Escribe bloques completos solo si se piden expresamente. La infraestructura (repo, ramas, entorno, Quarto, publicación) sí la puede hacer la IA.
2. **Todo en español**: respuestas, comentarios, nombres de variables y commits.
3. **Git**: `master` y `test` están protegidas y todo entra por PR. Ramas cortas desde `test` con prefijo `datos/`, `rag/`, `eval/`, `app/`, `web/` o `infra/`. Commits que empiecen por la parte (por ejemplo, `Datos: descarga del reglamento`). Al final del proyecto, PR de `test` a `master` y publicar desde `master`.
4. **No subir** `data/raw/`, `chroma/`, `.venv/` ni `.env`, y nunca poner claves en el código.
5. **Preguntar antes de**: añadir dependencias, cambiar lo que une cada parte (ver abajo), forzar un push, borrar ramas o archivos y publicar la web.
6. Los `.py` de `rag_project/src/` y `app.py` son **esqueletos**: cada función tiene su explicación y los pasos en comentarios. Respeta los nombres y las firmas.

## Decisiones tomadas

| Fecha | Decisión | Por qué |
|---|---|---|
| 06/11 | Repo nuevo y público `proy-rag`, montado igual que el del Trabajo 1 (`proy-redesneuronales`): `master` + `test` protegidas y PR obligatorio | Mismo flujo que ya conocemos |
| 06/11 | Código en `rag_project/` + web de Quarto con 4 páginas: 01-datos, 02-arquitectura, 03-evaluacion, 04-app-y-conclusiones | Lo pide la entrega |
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
| 20/11 | Interfaz en **Streamlit** | Un solo archivo, y Streamlit Cloud despliega desde el repo |

## Lo que une cada parte (no se cambia sin avisar al resto)

- `pipeline.py` → `data/processed/corpus.jsonl`, con una línea por página de PDF y una por medicamento:
  - `{"fuente", "url", "pagina", "texto"}`
  - y en CIMA, además, `"principio_activo"` (con `"pagina": null`).
- `indexar.py` → colecciones de Chroma `trozos_300`, `trozos_800` y `trozos_1500` en `rag_project/chroma/`.
- `rag.py` → `cargar_base()`, `recuperar(base, pregunta)`, `responder_sin_rag(pregunta)` y `responder_con_rag(base, pregunta) → (respuesta, trozos)`.
  - La app y `evaluar.py` solo usan estas funciones.
  - `llamar_llm()` es el único sitio que sabe qué LLM se usa.

## API de CIMA (comprobada el 20/11)

- `https://cima.aemps.es/cima/rest/medicamentos?nombre=ventolin` → 5 presentaciones. Cada una trae `nombre`, `viasAdministracion` y `receta`; `pactivos` llega vacío en este listado.
- `https://cima.aemps.es/cima/rest/medicamentos?practiv1=salbutamol` → 20 medicamentos.
- `https://cima.aemps.es/cima/rest/medicamento?nregistro=...` → el detalle, con `principiosActivos`.
- Va por páginas: `totalFilas`, `pagina` y `tamanioPagina`.

## Reparto

- **P1, datos**: `pipeline.py` y la página 01.
- **P2, recuperación y evaluación**: `indexar.py`, `recuperar()`, `evaluar.py` y las páginas 02 y 03.
- **P3, generación, app y web**: el resto de `rag.py`, `app.py`, el despliegue, Quarto y la página 04.
- **Todos**: preguntas de evaluación, veredictos y conclusiones.
- Todavía no se ha decidido quién es P1, P2 y P3.

## Estado (20/11)

- En `test`: la guía, los esqueletos y el tema (PR #1 y #2). `master` solo tiene el README inicial.
- Todavía no hay código escrito, ni datos, ni preguntas (`preguntas.csv` solo tiene la cabecera).
- En el Mac de Javier: `.venv` creado con Python 3.14 y todo `requirements.txt` instalado. Ollama instalado, todavía sin modelo (falta `ollama pull qwen2.5:3b`).

## Pendiente

- Fecha de entrega real (sin confirmar).
- Quién es P1, P2 y P3.
- Escribir las preguntas de evaluación, antes de buscar fuentes.
- URLs vigentes de los 3 PDFs.
- Qué LLM usar en la nube para la app publicada, porque Streamlit Cloud no ejecuta Ollama.
- Si el profesor exige que funcione sin wifi.
- Invitar a Alejandro y Miguel como colaboradores del repo.
