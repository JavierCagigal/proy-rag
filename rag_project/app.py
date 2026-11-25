"""Fase D: interfaz (P3).

Local, desde rag_project/:  streamlit run app.py
"""
import sys
from pathlib import Path

import streamlit as st

# rag.py importa indexar.py como módulo hermano, así que src/ tiene que estar en el path.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from rag import cargar_base, cita, modelo_en_uso, responder_con_rag, responder_sin_rag  # noqa: E402

EJEMPLOS = [
    "¿A partir de qué temperatura del agua se prohíbe el neopreno en grupos de edad?",
    "Tengo asma y uso Ventolin inhalado. ¿Cuánto puedo tomar el día de la carrera?",
    "Me han recetado Adolonta para el dolor. ¿Lo puedo tomar el día de la competición?",
    "¿Cuánto tiempo de penalización hay por drafting en una prueba sprint?",
]

st.set_page_config(page_title="Asistente del triatleta", page_icon="🏊")
st.title("Asistente de competición para triatletas")
st.caption("Reglamento de World Triathlon y de la FETRI, lista de prohibidas de la WADA 2026 "
           f"y medicamentos españoles de CIMA: ¿me da positivo? · Modelo: {modelo_en_uso()}")


@st.cache_resource
def base():
    """Abre Chroma y carga el modelo de embeddings una sola vez, no en cada pregunta."""
    return cargar_base()


with st.sidebar:
    st.subheader("Prueba con")
    for ejemplo in EJEMPLOS:
        if st.button(ejemplo, use_container_width=True):
            st.session_state["pregunta"] = ejemplo
    comparar = st.checkbox("Comparar con el LLM sin RAG")

pregunta = st.text_input("Tu pregunta", key="pregunta", placeholder="¿Me da positivo el Frenadol?")

if pregunta:
    if comparar:
        col_sin, col_con = st.columns(2)
        with col_sin:
            st.subheader("Sin RAG")
            with st.spinner("Pensando sin apuntes..."):
                st.write(responder_sin_rag(pregunta))
        destino = col_con
    else:
        destino = st.container()

    with destino:
        if comparar:
            st.subheader("Con RAG")
        with st.spinner("Buscando en el reglamento, la WADA y CIMA..."):
            respuesta, trozos = responder_con_rag(base(), pregunta)
        st.write(respuesta)

    with st.expander(f"Fuentes ({len(trozos)} trozos recuperados)"):
        for t in trozos:
            st.markdown(f"**{cita(t)}** · [enlace]({t.metadata['url']})")
            st.text(t.page_content)
