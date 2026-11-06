"""Fase D: interfaz (P3).

Local, desde rag_project/:  streamlit run app.py
"""
import streamlit as st

# from src.rag import cargar_base, responder_con_rag, responder_sin_rag

st.title("Asistente de triatlón")  # cambiadlo cuando cerremos el tema

# 1. base = cargar_base() con @st.cache_resource, para no abrir Chroma en cada pregunta.
# 2. pregunta = st.text_input(...) y una casilla "Comparar con el LLM sin RAG".
# 3. Si hay pregunta: responder_con_rag → st.write(respuesta)
#    y las fuentes en st.expander("Fuentes"): fuente, página y el texto del trozo.
# 4. Si la casilla está marcada: dos columnas (st.columns(2)) sin RAG / con RAG.
# Mientras rag.py no esté listo, usad una respuesta falsa para montar la interfaz.
