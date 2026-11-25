#!/bin/sh
# Arranque del contenedor en Cloud Run.
# Cloud Run indica el puerto en $PORT y exige escuchar en 0.0.0.0.
exec streamlit run app.py --server.port "$PORT" --server.address 0.0.0.0 --server.headless true
