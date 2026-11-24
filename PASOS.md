# Pasos: qué se ha construido, qué es cada cosa y por qué

Diario del proyecto, en orden. Cada apartado dice qué se añadió, para qué sirve y por qué se hizo así. Sirve para estudiar antes de la exposición y para que cualquier compañero (o su IA) sepa por qué el código es como es. Las reglas y decisiones generales están en [AGENTS.md](AGENTS.md) y el plan completo en [GUIA_PROYECTO.md](GUIA_PROYECTO.md).

Cómo se trabaja desde el 20/11: **Javier escribe todo el código con ayuda de Claude** y la exposición sigue repartida como estaba (P1 Miguel, P2 Javier, P3 Alejandro). Cada uno tiene que leer y entender la parte que defiende; para eso está este archivo.

---

## Cómo ejecutar todo

Desde `rag_project/`, con el `.venv` activado y Ollama abierto:

```bash
python src/pipeline.py            # A: descarga y limpia → data/processed/corpus.jsonl   (~20 s)
python src/indexar.py             # B: trozos + embeddings → chroma/ (3 colecciones)    (~1 min)
python src/rag.py                 # prueba rápida con 2 preguntas
python src/evaluar.py chunking    # C: experimento de tamaños de trozo, sin LLM        (~1 min)
python src/evaluar.py             # C: experimento + comparativa sin RAG / con RAG       (~10 min)
```

Lo que se descarga (`data/raw/`) y la base vectorial (`chroma/`) **no se suben a git**: se regeneran con estos comandos. `corpus.jsonl`, `preguntas.csv` y `resultados/` sí se suben.

---

## 1. Las fuentes (20/11)

Buscadas en las webs oficiales con Chrome. Son las versiones vigentes hoy:

| Fuente | Versión | URL |
|---|---|---|
| Reglamento de World Triathlon | Competition Rules 2026 (212 págs., inglés) | https://cms.triathlon.org/download-file/world-triathlon-competition-rules-2026 |
| Reglamento de la FETRI | Reglamento de Competiciones 2026, Circular 4/26 (138 págs., español) | https://triatlon.org/wp-content/uploads/2026/07/Circular.4.26-Competiciones-Reglamento-de-Competiciones.pdf |
| Lista de prohibidas de la WADA | 2026 Prohibited List (26 págs., inglés) | https://www.wada-ama.org/sites/default/files/2025-09/2026list_en_final_clean_september_2025.pdf |
| CIMA (AEMPS) | API REST, sin clave | https://cima.aemps.es/cima/rest/medicamentos |

- **WADA**: la lista de 2026 es la vigente hasta el 31/12/2026. Si al entregar ya está la de 2027, basta con cambiar la URL y volver a ejecutar: es el argumento de "un RAG se actualiza sin reentrenar".
- **WADA pide un navegador**: si la petición no lleva cabecera `User-Agent` de navegador, la web responde 202 vacío en vez del PDF. Por eso `pipeline.py` manda `CABECERAS`.
- **Licencia**: son documentos públicos oficiales. Los PDF no se suben al repo (se descargan); el texto extraído en `corpus.jsonl` se usa con fines educativos y citando siempre la fuente.

---

## 2. `src/pipeline.py`: fase A, de internet al corpus (20/11)

**Qué hace**: descarga los 3 PDF y los medicamentos de CIMA, saca el texto, lo limpia y escribe `data/processed/corpus.jsonl` con una línea por página de PDF y una por medicamento. Sin ningún paso manual, como pide el profesor.

| Función | Qué hace | Por qué así |
|---|---|---|
| `descargar_pdf` | Baja el PDF a `data/raw/` si no está ya | Caché: no se repite la descarga en cada ejecución. Comprueba que empieza por `%PDF` para no guardar una página de error como si fuera el PDF |
| `extraer_paginas` | Texto de cada página con `pypdf` | Guardamos el número de página para poder **citarlo** |
| `lineas_repetidas` | Líneas que salen en más de la mitad de las páginas | Son cabeceras y pies ("World Triathlon Competition Rules 2026"…); repetidas en cada trozo solo meten ruido |
| `es_ruido` + `limpiar` | Quita esas líneas, las del **índice** ("5.5. DRAFTING ……… 47") y los números de página sueltos ("35/212"); une palabras partidas con guion y normaliza espacios | Las líneas del índice se parecen mucho a las preguntas pero no contienen la respuesta: robaban sitio en la búsqueda |
| `es_indice` | Descarta las páginas de **índice alfabético** (más de la mitad de las líneas son "Formoterol, 9, 12") | Las 5 últimas páginas de la WADA nombran todas las sustancias, así que ganaban todas las búsquedas sin decir nada útil. El LLM llegaba a citarlas |
| `descargar_cima` | Medicamentos de un principio activo, **recorriendo todas las páginas** de la API | La API va por páginas (`totalFilas`, `pagina`, `tamanioPagina`); el paracetamol, por ejemplo, tiene 421 |
| `texto_medicamento` | Frase corta: nombre, principio activo, forma, vía, receta | Es lo que se indexa. La **vía** importa: el salbutamol inhalado está permitido y en jarabe no |
| `url_medicamento` | Enlace a la ficha técnica | Para citar y comprobar |
| `main` | Junta todo, **comprueba el formato** de cada línea y escribe el jsonl | El formato es lo que une con `indexar.py` (AGENTS.md); si se rompe, falla aquí y no más tarde |

**Decisiones**:
- **24 principios activos** agrupados por motivo: broncodilatadores beta-2 (asma), glucocorticoides, estimulantes y descongestionantes (antigripales), diurético, betabloqueante, analgésicos (tramadol prohibido, codeína no), hormonas, y tres **permitidos** (ibuprofeno, paracetamol, cetirizina) para comprobar que el RAG también sabe decir "no da positivo".
- **Descartados**: `hidroclorotiazida` (181 combinaciones para la tensión, solo ruido), `efedrina` y `morfina` (CIMA busca por subcadena: "efedrina" ya devuelve la pseudoefedrina).
- **Solo comercializados y de marca** (`comerc` y no `generico`): de 1.069 resultados quedan 637 medicamentos. Los genéricos se llaman como su principio activo ("PARACETAMOL CINFA"), así que no hace falta CIMA para saber qué llevan; las marcas ("Frenadol", "Adolonta") son justo lo que el LLM no sabe.
- **`principio_activo` sale del campo `vtm`** de CIMA, que trae la combinación completa ("paracetamol + clorfenamina + dextrometorfano + pseudoefedrina"). Un medicamento con dos principios activos sale en dos búsquedas: se guarda una sola vez.
- **Avisos de pypdf silenciados**: el PDF de World Triathlon tiene referencias internas rotas; se lee bien, pero pypdf avisaba decenas de veces.

**Resultado**: 995 líneas (204 páginas de World Triathlon, 134 de la FETRI, 20 de la WADA y 637 medicamentos), 1,1 MB, en unos 20 segundos.

---

## 3. `evaluacion/preguntas.csv`: las 10 preguntas (20/11)

Escritas leyendo los PDF; cada una tiene una respuesta exacta y comprobable. Columnas:

- `id`, `pregunta`, `respuesta_esperada`.
- `fuente`: dónde está la respuesta. `+` significa "hacen falta las dos" (CIMA **y** la WADA) y `|` "vale cualquiera" (World Triathlon **o** la FETRI, que copia su reglamento en español).
- `dato_clave`: una expresión regular con el dato exacto ("1600 micrograms", "1500 m 22 ºC"). La usa el experimento de chunking para saber si el trozo recuperado contiene la cifra o la ha cortado.

| # | Tipo | Qué prueba |
|---|---|---|
| 1-3 | Reglamento (World Triathlon o FETRI) | Penalización por drafting, neopreno en grupos de edad, casco en transición |
| 4 | Reglamento FETRI | Sanciones por drafting en media distancia |
| 5-6 | CIMA + WADA | Ventolin inhalado (límite de dosis) frente a Ventolin jarabe (prohibido) |
| 7 | CIMA + WADA | Frenadol Descongestivo → pseudoefedrina |
| 8 | CIMA + WADA | Adolonta → tramadol |
| 9 | CIMA + WADA | Sumial → propranolol: **no** prohibido en triatlón (pregunta trampa) |
| 10 | Control | No está en el corpus: con RAG tiene que decir que no lo sabe |

La pregunta 1 decía "según el reglamento de World Triathlon"; se quitó para no obligar a una fuente concreta, porque la FETRI tiene la misma tabla.

---

## 4. `src/indexar.py`: fase B, trozos + embeddings + Chroma (20/11)

**Qué hace**: lee el corpus, lo parte en trozos de 300, 800 y 1.500 caracteres (solape 100), calcula el embedding de cada trozo y lo guarda en Chroma, una colección por tamaño (`trozos_300`, `trozos_800`, `trozos_1500`).

| Función | Qué hace | Por qué así |
|---|---|---|
| `crear_embeddings` | El modelo `multilingual-e5-small` con prefijos `passage: ` (trozos) y `query: ` (preguntas) | e5 se entrenó así y recupera peor sin ellos. `rag.py` usa **esta misma función**: si los vectores salieran de modelos distintos, no serían comparables |
| `cargar_corpus` | Cada línea → `Document` (texto + metadata) | Chroma **no admite metadata `None`**, así que la página vacía de CIMA se quita |
| `trocear` | `RecursiveCharacterTextSplitter` | Corta por párrafos, luego líneas, luego palabras: intenta no partir frases. Los trozos heredan la metadata (fuente, página) |
| `indexar` | Borra la colección y la vuelve a crear | Si no, al ejecutar dos veces se duplicarían todos los trozos |

- `normalize_embeddings=True` + `hnsw:space = cosine`: Chroma mide la **similitud del coseno**, la que explicamos en la exposición.
- **Resultado**: 4.408 / 1.811 / 1.309 trozos; ~1 minuto en CPU; 42 MB en `chroma/` (no se sube).
- 1.500 caracteres son unos 400 tokens: por debajo del máximo de 512 de e5. Un trozo más grande se cortaría sin avisar.

---

## 5. `src/rag.py`: recuperar y generar (20/11)

| Función | Qué hace |
|---|---|
| `cargar_base` | Abre la colección de Chroma con el mismo modelo de embeddings |
| `recuperar` | Busca los trozos (ver abajo) y quita repetidos |
| `cita` | La etiqueta `[fuente, p. N]` que va delante de cada trozo y que el LLM copia al citar |
| `llamar_llm` | Llama a Ollama (`qwen2.5:3b`). **Único sitio** que sabe qué LLM se usa |
| `responder_sin_rag` | Solo la pregunta: la línea base |
| `responder_con_rag` | Recupera → monta el prompt → LLM. Devuelve `(respuesta, trozos)` |

### Cómo busca `recuperar()`

1. **Búsqueda general**: los 4 trozos más parecidos a la pregunta. Si no es una pregunta de medicamentos, se devuelven estos y ya está.
2. **¿Nombra un medicamento?** Búsqueda solo en CIMA; se añaden los trozos con relevancia **≥ 0,85**. Umbral medido: las preguntas de medicamentos dan ≥ 0,857 y las demás ≤ 0,836. Hace falta porque en la búsqueda general ganaban los trozos largos de la FETRI (en español, como la pregunta) y "Sumial" no salía.
3. Si es de medicamentos, el contexto es **CIMA (2 trozos) + WADA**: los trozos del reglamento solo metían ruido, y las demás presentaciones del mismo medicamento se repetían ("VENTOLIN 100 microgramos", "VENTOLIN 5 mg/ml"…).
4. **Expansión de la consulta**: por cada principio activo de esos trozos de CIMA, se busca en la WADA:
   - por significado, con el nombre del principio activo (4 trozos);
   - por **palabra exacta** con `$contains` de Chroma (2 trozos). "Tramadol" está dentro de una lista larga de narcóticos y el embedding de esa lista no se parece al de una sola palabra.

### Ajustes que salieron de las pruebas

- **Primera prueba (Hito 1)**: la del neopreno salió bien con cita; la de Ventolin, mal ("No sabes"). El segundo paso traía la página correcta de la WADA, pero no el trozo con el límite.
- Se probó buscar con "pregunta + principio activo": **empeoraba** (la pregunta en español atraía a la FETRI). Se dejó solo el principio activo, filtrando a la WADA.
- **Prompt**: ahora explica qué son los trozos `[cima]` y `[lista_prohibida_wada]`, dice los pasos para una pregunta de medicamentos (principio activo → WADA → prohibido, cuándo, vía, dosis), pide cifras exactas con cita y cambia "di que no la sabes" por "solo si el contexto no tiene la respuesta, di *No lo sé con mis fuentes*". Con el prompt anterior qwen contestaba "No la sabes" incluso con el trozo correcto delante (Adolonta, Sumial).
- **Menos trozos**: al quitar los índices de la WADA, el reglamento en las preguntas de medicamentos y las presentaciones repetidas, el contexto medio bajó de 4.113 a 3.117 caracteres con los mismos aciertos.
- **`num_ctx=8192`**: por defecto Ollama solo lee los primeros miles de tokens y **corta el contexto sin avisar**. Con varios trozos de 800 caracteres se pasaba.
- **`temperature=0`**: respuestas repetibles para la comparativa.

---

## 6. `src/evaluar.py`: fase C, cómo se demuestra (20/11)

### Experimento de chunking

Para cada tamaño y pregunta, mide dos cosas sobre los trozos recuperados (sin LLM):
- `acierto`: ¿está la página correcta?
- `dato`: ¿está el dato exacto (`dato_clave`)? Es la medida que decide.

| Tamaño | Página correcta | Dato exacto | Texto que recibe el LLM (media) |
|---|---|---|---|
| 300 | 9 / 9 | 4 / 9 | 1.411 caracteres |
| **800** | 9 / 9 | **8 / 9** | 3.117 caracteres |
| 1500 | 9 / 9 | 8 / 9 | 5.527 caracteres |

**Elegido: 800.** Con 300 se encuentra la página, pero el trozo corta las tablas (penalizaciones, neopreno) y la cifra se queda fuera. 1.500 acierta lo mismo que 800 con un 77 % más de texto, y eso es más ruido para un modelo pequeño y más lento.

Antes de llegar aquí el experimento destapó dos problemas, ya resueltos (apartado 5): la pregunta en español atraía a la FETRI y la búsqueda de medicamentos no llegaba a la WADA.

**Limitación medida (pregunta 7)**: "pseudoefedrina" en español no encuentra la nota de la WADA "Pseudoephedrine: … greater than 150 micrograms per millilitre"; buscando en inglés sí la encuentra. El modelo `e5-small` pierde precisión entre idiomas con palabras sueltas. Mejoras posibles: un modelo de embeddings mayor (`multilingual-e5-base`, `bge-m3`) o traducir el principio activo antes de buscar. Va a conclusiones.

### Comparativa sin RAG / con RAG

`python src/evaluar.py` → `resultados/comparativa.csv`: la misma pregunta al mismo modelo, sin contexto y con los trozos. Los veredictos (`correcta`, `parcial`, `inventada`, `no sabe`) se ponen a mano.

Veredictos **propuestos por Claude** (columna `nota` con el porqué de cada uno). Hay que revisarlos entre todos antes de darlos por buenos:

| | Sin RAG | Con RAG |
|---|---|---|
| Correcta | 0 | 2 |
| Parcial | 0 | 4 |
| Inventada | 9 | 2 |
| No sabe | 1 | 2 |

Lo que se ve:
- **Sin RAG, qwen se lo inventa casi todo y con mucha seguridad**: neopreno prohibido "a 28 ºC", Adolonta "es adenosina", Frenadol "lleva desmopánico", ganadores de Ironman que no existen.
- **Con RAG ya no inventa datos externos**: todo lo que dice sale de los trozos, y en la pregunta de control dice que no lo sabe.
- **Pero el modelo de 3B lee mal el contexto**. La recuperación trae el dato exacto en 8 de 9 preguntas, y aun así confunde cifras del mismo trozo: en la 5 da el límite del formoterol en vez del salbutamol, y en la 1 la sanción de "otras infracciones" en vez de la de drafting. Con 3 GB libres en el disco no cabe un modelo local mayor (qwen2.5:7b ocupa unos 4,7 GB). La mejora natural es usar un modelo mayor por API, que hace falta igualmente para la app en la nube.

El primer intento (prompt corto, todos los trozos) dio aún menos: 2 correctas, 3 parciales, 2 inventadas y 3 "no sabe".

---

## 7. `app.py`: fase D, la interfaz (20/11)

- `@st.cache_resource` abre Chroma y carga el modelo de embeddings **una sola vez**, no en cada pregunta.
- Caja de texto, 4 preguntas de ejemplo en la barra lateral y una casilla "Comparar con el LLM sin RAG" que pone las dos respuestas en dos columnas.
- Debajo, un desplegable con las **fuentes**: cada trozo con su cita y el enlace al documento o a la ficha de CIMA.
- `sys.path.insert(0, "src")`: `rag.py` importa `indexar.py` como módulo hermano, así que la carpeta `src/` tiene que estar en el path. Por eso el editor marca el `import` en rojo, aunque funciona.
- Probada con `streamlit.testing.v1.AppTest`: arranca sin errores. En local usa el Ollama del Mac; en la nube, Gemini (apartado 8).

## 8. Despliegue en Google Cloud Run con Gemini (24/11)

**Decisión**: la app pública va en **Google Cloud Run** (lo usan otros compañeros) y el LLM es **Gemini por API**, con el modelo `gemini-3.5-flash-lite`. El 21/11 se probó a meter Ollama con qwen dentro del contenedor, pero se descartó: imagen de ~6 GB, respuestas de 10-30 s en CPU y 4 CPU + 8 GB de coste. Con Gemini la imagen es pequeña, responde en pocos segundos y un modelo mayor lee mejor el contexto.

**Por qué `gemini-3.5-flash-lite`** (consultado el 24/11 en la documentación de Google): está en el plan gratuito, Google lo presenta como el más rápido y barato para tareas simples, y todavía respeta `temperature=0` (en Gemini 3.6 y posteriores ese parámetro se ignora, y las respuestas no se podrían repetir).

### Cómo elige el modelo `llamar_llm()`

- Si existe la variable de entorno `GEMINI_API_KEY` → Gemini. Es lo que pasa en Cloud Run.
- Si no → Ollama con `qwen2.5:3b`. Es lo que pasa en el Mac: la evaluación y las pruebas siguen igual.
- `modelo_en_uso()` dice cuál se está usando; la app lo enseña debajo del título.
- La llamada a Gemini es un `POST` con `requests` (ya lo usábamos en `pipeline.py`), así que **no hay dependencias nuevas**. La clave va en la cabecera `x-goog-api-key` y no en la URL, para que no salga en registros ni en mensajes de error.
- Probado: sin clave contesta qwen; con una clave falsa Google responde "API key not valid", que confirma que la URL y la cabecera son las correctas. Falta probarlo con la clave de verdad.

**Ojo con la comparativa**: `comparativa.csv` está hecha con qwen (el mismo modelo con y sin RAG, como se decidió). La app pública usa Gemini, que es otro modelo. Si da tiempo, se puede repetir la comparativa con Gemini exportando la clave antes de `python src/evaluar.py`.

### Archivos

| Archivo | Qué hace |
|---|---|
| `rag_project/Dockerfile` | Imagen con Python 3.12, las librerías con las mismas versiones que el `.venv` y la colección `trozos_800` **ya indexada** (también deja dentro el modelo de embeddings). Así cada arranque no tiene que descargar ni indexar nada |
| `rag_project/arrancar.sh` | Arranca Streamlit en el puerto que da Cloud Run (`$PORT`) |
| `rag_project/.gcloudignore` | Lo que no se sube a Cloud Build (PDF, `chroma/`, resultados, páginas de la web) |

- **`torch` para CPU**: la versión normal trae CUDA (varios GB) y Cloud Run no tiene GPU.
- **`corpus.jsonl` ya está en el repo**: el contenedor no descarga los PDF ni llama a CIMA, solo indexa.

### Lo que tiene que hacer Javier (una vez)

La cuenta, la facturación, la clave y el inicio de sesión no los puede hacer la IA:

1. Crear la clave de Gemini en https://aistudio.google.com → *Get API key*. No la pegues en el chat ni en el código.
2. Crear un proyecto en https://console.cloud.google.com y **activar la facturación** (Cloud Run la exige aunque se quede en el nivel gratuito). Recomendado: una **alerta de presupuesto** de pocos euros en *Facturación → Presupuestos*.
3. Instalar la CLI e iniciar sesión:
   ```bash
   brew install --cask google-cloud-sdk
   gcloud auth login
   gcloud config set project ID_DEL_PROYECTO
   gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com
   ```
4. Guardar la clave en **Secret Manager** (te la pide por teclado; no queda en el historial):
   ```bash
   read -s CLAVE && printf '%s' "$CLAVE" | gcloud secrets create gemini-api-key --data-file=- && unset CLAVE
   ```

### Desplegar (cada vez que cambie la app)

Desde la raíz del repo:

```bash
gcloud run deploy asistente-triatlon --source rag_project --region europe-west1 \
  --cpu 2 --memory 4Gi --max-instances 1 --timeout 3600 --session-affinity \
  --set-secrets GEMINI_API_KEY=gemini-api-key:latest --allow-unauthenticated
```

- `--source rag_project`: Cloud Build construye la imagen con el `Dockerfile`; no hace falta Docker en el Mac.
- `--cpu 2 --memory 4Gi`: el LLM ya no corre aquí, pero cargar torch y el modelo de embeddings con 1 CPU pasaba del minuto en la primera pregunta.
- `--max-instances 1`: como mucho una copia funcionando, para que el coste no se dispare.
- `--timeout 3600 --session-affinity`: Streamlit mantiene una conexión abierta (websocket) con cada visitante.
- `--set-secrets`: Cloud Run lee la clave de Secret Manager y la pone en `GEMINI_API_KEY`. Si dice que la cuenta de servicio no tiene permiso, darle el rol *Secret Manager Secret Accessor* (el propio error dice cuál es la cuenta).
- `--allow-unauthenticated`: la app es pública, como pide la fase D.

Al terminar imprime la URL (`https://asistente-triatlon-….run.app`). Si la construcción falla por tiempo: `gcloud config set builds/timeout 1800` y repetir.

**Coste (sin comprobar, mirar la página de precios)**: Cloud Run tiene un nivel gratuito mensual y con 1 CPU y 2 GB da para bastantes horas de uso; Gemini 3.5 Flash-Lite es gratis en el plan gratuito, con límites de peticiones por minuto.

### Desplegada el 24/11

- **URL**: https://asistente-triatlon-921790710609.europe-west1.run.app
- Proyecto `asistente-triatlon`, región `europe-west1`, revisión con 2 CPU, 4 GB, CPU solo durante peticiones, como mucho 1 instancia.
- La clave está en Secret Manager (`gemini-api-key`); la cuenta de servicio de Cloud Run (`…-compute@developer.gserviceaccount.com`) tiene permiso para leer **solo ese secreto**.
- **Primer problema y su diagnóstico**: con 1 CPU la primera pregunta se quedaba "pensando" más de un minuto. Para verlo con datos se ejecutó la misma imagen como trabajo de Cloud Run midiendo cada paso: importar 5 s, crear los embeddings 26 s (casi todo, consultando Hugging Face por internet aunque el modelo ya estaba en la imagen), cargar la base 4 s, `recuperar()` 1 s. Arreglo: `HF_HUB_OFFLINE=1` (ya en el `Dockerfile`) y 2 CPU.
- **Probada en el navegador**:
  - *Adolonta*: "El principio activo de Adolonta es el tramadol [cima]. … narcóticos (S7) [lista_prohibida_wada, p. 17]. Está prohibido en competición." Correcta; con qwen era parcial.
  - *Ventolin inhalado*: 1600 µg en 24 h sin pasar de 600 µg en 8 h, y el umbral de 1000 ng/mL, citando la p. 9. Correcta; con qwen era inventada (daba el límite del formoterol).
- La primera pregunta después de un rato sin uso tarda alrededor de un minuto (arranque en frío); las siguientes, pocos segundos.
- Para cambiar solo la configuración sin reconstruir la imagen: `gcloud run services update asistente-triatlon --region europe-west1 ...`.
