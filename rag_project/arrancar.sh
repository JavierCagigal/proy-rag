#!/bin/sh
# Arranque del contenedor en Cloud Run: primero Ollama, después la app.

ollama serve &

# Esperar a que Ollama responda; si la app arranca antes, la primera pregunta fallaría.
until ollama list > /dev/null 2>&1; do sleep 1; done

# Cargar qwen en memoria ya, para que la primera pregunta no tarde el doble.
ollama run qwen2.5:3b "" > /dev/null 2>&1 &

# Cloud Run indica el puerto en $PORT y exige escuchar en 0.0.0.0.
exec streamlit run app.py --server.port "$PORT" --server.address 0.0.0.0 --server.headless true
