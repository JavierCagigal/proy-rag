# Fase D: la app y el LLM en un solo contenedor para Google Cloud Run.
# Ollama (qwen2.5:3b) + Streamlit + la base de Chroma, todo dentro de la imagen:
# el mismo modelo que en la evaluación y sin API keys.
#
# Se construye en Cloud Build con: gcloud run deploy ... --source rag_project  (ver PASOS.md, apartado 8)

# El binario de Ollama se copia de su imagen oficial, en la misma versión que en el Mac de Javier.
FROM ollama/ollama:0.40.16 AS ollama

# Debian 13: glibc reciente, compatible con el binario de Ollama.
FROM python:3.12-slim-trixie
COPY --from=ollama /usr/bin/ollama /usr/bin/ollama
# ponytail: se copian también las librerías de GPU que Cloud Run no usa (imagen de ~6 GB, arranque en frío
# más lento). Si molesta, copiar solo libggml-base y libggml-cpu-* de /usr/lib/ollama.
COPY --from=ollama /usr/lib/ollama /usr/lib/ollama

WORKDIR /app

# torch para CPU: la versión normal trae CUDA (varios GB) y Cloud Run no tiene GPU.
RUN pip install --no-cache-dir torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir \
    langchain==1.5.2 langchain-chroma==1.1.0 langchain-huggingface==1.2.3 \
    langchain-ollama==1.1.0 langchain-text-splitters==1.1.3 \
    sentence-transformers==6.3.0 streamlit==1.67.0 pandas==3.1.1

# El modelo se descarga al construir la imagen, no en cada arranque.
RUN ollama serve & sleep 5 && ollama pull qwen2.5:3b

COPY src/ src/
COPY app.py .
COPY data/processed/corpus.jsonl data/processed/corpus.jsonl

# Solo la colección que usa la app (trozos_800). Así también queda descargado el modelo de embeddings.
RUN python -c "import sys; sys.path.insert(0, 'src'); import indexar as i; \
i.indexar(i.trocear(i.cargar_corpus(), 800, i.SOLAPE), 'trozos_800', i.crear_embeddings())"

COPY arrancar.sh .
ENV PORT=8080
CMD ["sh", "arrancar.sh"]
