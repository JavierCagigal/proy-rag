# Fase D: la app para Google Cloud Run.
# Streamlit + la base de Chroma ya indexada; el LLM es Gemini por API (clave en GEMINI_API_KEY,
# que Cloud Run saca de Secret Manager: nunca va en la imagen ni en el repo).
#
# Se construye en Cloud Build con: gcloud run deploy ... --source rag_project  (ver PASOS.md, apartado 8)
FROM python:3.12-slim

WORKDIR /app

# torch para CPU: la versión normal trae CUDA (varios GB) y Cloud Run no tiene GPU.
RUN pip install --no-cache-dir torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu
# Las mismas versiones que el .venv del Mac de Javier.
RUN pip install --no-cache-dir \
    langchain==1.5.2 langchain-chroma==1.1.0 langchain-huggingface==1.2.3 \
    langchain-ollama==1.1.0 langchain-text-splitters==1.1.3 \
    sentence-transformers==6.3.0 streamlit==1.67.0 pandas==3.1.1 requests

COPY src/ src/
COPY app.py .
COPY data/processed/corpus.jsonl data/processed/corpus.jsonl

# Solo la colección que usa la app (trozos_800). Así también queda descargado el modelo de embeddings
# dentro de la imagen y cada arranque no tiene que bajarlo.
RUN python -c "import sys; sys.path.insert(0, 'src'); import indexar as i; \
i.indexar(i.trocear(i.cargar_corpus(), 800, i.SOLAPE), 'trozos_800', i.crear_embeddings())"

COPY arrancar.sh .
ENV PORT=8080
CMD ["sh", "arrancar.sh"]
