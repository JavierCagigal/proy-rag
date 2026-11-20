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

**Resultado**: 1.000 líneas (204 páginas de World Triathlon, 134 de la FETRI, 25 de la WADA y 637 medicamentos), 1,1 MB, en unos 20 segundos.

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

1. **Búsqueda general**: los 4 trozos más parecidos a la pregunta.
2. **¿Nombra un medicamento?** Búsqueda solo en CIMA; se añaden los trozos con relevancia **≥ 0,85**. Umbral medido: las preguntas de medicamentos dan ≥ 0,857 y las demás ≤ 0,836. Hace falta porque en la búsqueda general ganaban los trozos largos de la FETRI (en español, como la pregunta) y "Sumial" no salía.
3. **Expansión de la consulta**: por cada principio activo de esos trozos de CIMA, se busca en la WADA:
   - por significado, con el nombre del principio activo (4 trozos);
   - por **palabra exacta** con `$contains` de Chroma (2 trozos). "Tramadol" está dentro de una lista larga de narcóticos y el embedding de esa lista no se parece al de una sola palabra.

### Ajustes que salieron de las pruebas

- **Primera prueba (Hito 1)**: la del neopreno salió bien con cita; la de Ventolin, mal ("No sabes"). El segundo paso traía la página correcta de la WADA, pero no el trozo con el límite.
- Se probó buscar con "pregunta + principio activo": **empeoraba** (la pregunta en español atraía a la FETRI). Se dejó solo el principio activo, filtrando a la WADA.
- **Prompt**: se añadió "Responde en español", "el contexto puede estar en inglés" y qué son los trozos `[cima]`. El modelo es pequeño y se perdía con el inglés.
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
| 300 | 9 / 9 | 4 / 9 | 1.881 caracteres |
| **800** | 9 / 9 | **8 / 9** | 4.113 caracteres |
| 1500 | 9 / 9 | 8 / 9 | 6.861 caracteres |

**Elegido: 800.** Con 300 se encuentra la página, pero el trozo corta las tablas (penalizaciones, neopreno) y la cifra se queda fuera. 1.500 acierta lo mismo que 800 con un 67 % más de texto, y eso es más ruido para un modelo pequeño y más lento.

Antes de llegar aquí el experimento destapó dos problemas, ya resueltos (apartado 5): la pregunta en español atraía a la FETRI y la búsqueda de medicamentos no llegaba a la WADA.

**Limitación medida (pregunta 7)**: "pseudoefedrina" en español no encuentra la nota de la WADA "Pseudoephedrine: … greater than 150 micrograms per millilitre"; buscando en inglés sí la encuentra. El modelo `e5-small` pierde precisión entre idiomas con palabras sueltas. Mejoras posibles: un modelo de embeddings mayor (`multilingual-e5-base`, `bge-m3`) o traducir el principio activo antes de buscar. Va a conclusiones.

### Comparativa sin RAG / con RAG

`python src/evaluar.py` → `resultados/comparativa.csv`: la misma pregunta al mismo modelo, sin contexto y con los trozos. Los veredictos (`correcta`, `parcial`, `inventada`, `no sabe`) se ponen a mano.

<!-- RESULTADOS_COMPARATIVA -->

---

## Pendiente

- Veredictos de la comparativa (revisarlos entre todos).
- `app.py` (fase D) y el LLM para la nube.
- Web de Quarto: las 5 páginas.
- Fase E (opcional): búsqueda híbrida BM25. Ya usamos `$contains` como búsqueda exacta mínima.
