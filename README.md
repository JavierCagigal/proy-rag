# proy-rag

Sistema RAG sobre deporte de resistencia (Trabajo 2, Grupo 3: Alejandro, Miguel y Javier). El código está en `rag_project/` y el informe es una web hecha con Quarto.

Cómo está planteado y quién hace qué: [GUIA_PROYECTO.md](GUIA_PROYECTO.md).

## Instalación (la primera vez)

Programas: [Python 3.11 o superior](https://www.python.org/downloads/), [Git](https://git-scm.com/downloads), [Quarto](https://quarto.org/docs/get-started/), [Ollama](https://ollama.com/download) y un editor (Antigravity o VS Code).

```bash
git clone https://github.com/JavierCagigal/proy-rag.git
cd proy-rag
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
ollama pull qwen2.5:3b           # el LLM local (unos 2 GB)
```

Abre la carpeta `proy-rag` en el editor y elige el intérprete de `.venv`.

## Ejecutar (desde `rag_project/`)

```bash
python src/pipeline.py    # A: descarga y limpia → data/processed/corpus.jsonl
python src/indexar.py     # B: trocea e indexa → chroma/
python src/rag.py         # prueba una pregunta sin RAG y con RAG
python src/evaluar.py     # C: → resultados/comparativa.csv y chunking.csv
streamlit run app.py      # D: la interfaz
```

Web: `quarto preview` desde la raíz del repo.

## Forma de trabajar

- `master` y `test` están protegidas: todo entra por pull request.
- Una rama corta por tarea desde `test` (`datos/`, `rag/`, `eval/`, `app/`, `web/`, `infra/`) → PR hacia `test` → lo revisa otro compañero.
- Al final, PR de `test` a `master` y se publica la web desde `master`.
- `data/raw/` y `chroma/` no se suben: se regeneran con los scripts.
