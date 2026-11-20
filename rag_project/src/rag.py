"""Recuperar + generar (P3, con P2 en recuperar).

La app y la evaluación solo usan responder_sin_rag y responder_con_rag.
llamar_llm es el único sitio que sabe qué LLM usamos: cambiar de Ollama
a una API para la versión en la nube se hace solo ahí.

Prueba rápida desde rag_project/:  python src/rag.py
"""
from pathlib import Path

CARPETA = Path(__file__).resolve().parent.parent
CHROMA = CARPETA / "chroma"
COLECCION = "trozos_800"  # la que gane el experimento de chunking
K = 4                     # cuántos trozos se pasan al LLM

PROMPT_RAG = """Responde a la pregunta usando SOLO la información del contexto.
Si la respuesta no está en el contexto, di que no la sabes.
Después de cada dato, cita la fuente entre corchetes, por ejemplo [reglamento_world_triathlon, p. 12].

Contexto:
{contexto}

Pregunta: {pregunta}
"""


def cargar_base(coleccion=COLECCION):
    """Abre la colección de Chroma con el mismo modelo de embeddings que indexar.py."""
    pass


def recuperar(base, pregunta, k=K):
    """Devuelve los trozos más parecidos a la pregunta (Document con su metadata).

    En dos pasos, para las preguntas de medicamentos (GUIA_PROYECTO.md, apartado 3):
    la WADA habla de "salbutamol", no de "Ventolin".
    """
    # 1. trozos = base.similarity_search(pregunta, k=k)
    # 2. Si algún trozo es de CIMA, sacar su metadata["principio_activo"]
    #    y volver a buscar con ese nombre (filtrando a las fuentes que no son CIMA).
    # 3. Devolver los trozos de las dos búsquedas, sin repetidos.
    pass


def llamar_llm(prompt):
    """Manda el prompt al LLM y devuelve el texto de la respuesta."""
    # En local: langchain_ollama.ChatOllama(model=..., temperature=0)
    pass


def responder_sin_rag(pregunta):
    """El mismo LLM, sin contexto: es la línea base de la comparativa."""
    pass


def responder_con_rag(base, pregunta):
    """Devuelve (respuesta, trozos) para poder enseñar las fuentes en la app."""
    # recuperar → unir los trozos con su fuente y página → PROMPT_RAG.format(...) → llamar_llm
    pass


if __name__ == "__main__":
    base = cargar_base()
    for pregunta in [
        "¿A partir de qué temperatura del agua se prohíbe el neopreno?",
        "Tengo asma y uso Ventolin inhalado, ¿puedo usarlo el día de la carrera?",
    ]:
        print("\nPREGUNTA:", pregunta)
        print("SIN RAG:", responder_sin_rag(pregunta))
        respuesta, trozos = responder_con_rag(base, pregunta)
        print("CON RAG:", respuesta)
        for t in trozos:
            print("  -", t.metadata)
