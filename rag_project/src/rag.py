"""Recuperar + generar (P3, con P2 en recuperar).

La app y la evaluación solo usan responder_sin_rag y responder_con_rag.
llamar_llm es el único sitio que sabe qué LLM usamos: cambiar de Ollama
a una API para la versión en la nube se hace solo ahí.

Prueba rápida desde rag_project/:  python src/rag.py
"""
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama

from indexar import CHROMA, crear_embeddings

COLECCION = "trozos_800"  # la que gane el experimento de chunking
K = 4                     # cuántos trozos se pasan al LLM
MODELO_LLM = "qwen2.5:3b"
# Medido con preguntas.csv (trozos_800): las preguntas de medicamentos tienen un trozo de CIMA
# con relevancia >= 0,857; las demás, <= 0,836.
UMBRAL_CIMA = 0.85
SOLO_CIMA = {"fuente": "cima"}
SOLO_WADA = {"fuente": "lista_prohibida_wada"}

PROMPT_RAG = """Responde en español a la pregunta usando SOLO la información del contexto.
El contexto puede estar en inglés. Los trozos [cima] dicen qué principio activo lleva cada medicamento español.
Si la respuesta no está en el contexto, di que no la sabes.
Después de cada dato, cita la fuente entre corchetes, por ejemplo [reglamento_world_triathlon, p. 12].

Contexto:
{contexto}

Pregunta: {pregunta}
"""


def cargar_base(coleccion=COLECCION):
    """Abre la colección de Chroma con el mismo modelo de embeddings que indexar.py."""
    return Chroma(collection_name=coleccion, embedding_function=crear_embeddings(),
                  persist_directory=str(CHROMA))


def recuperar(base, pregunta, k=K):
    """Devuelve los trozos más parecidos a la pregunta (Document con su metadata).

    En dos pasos, para las preguntas de medicamentos (GUIA_PROYECTO.md, apartado 3):
    la WADA habla de "salbutamol", no de "Ventolin".
    """
    trozos = base.similarity_search(pregunta, k=k)

    # Paso 1b: ¿la pregunta nombra un medicamento? Se busca solo en CIMA y se añaden los muy parecidos.
    # Hace falta porque los trozos de los reglamentos (largos y en español) suelen ganar en la búsqueda general.
    for trozo, puntuacion in base.similarity_search_with_relevance_scores(pregunta, k=2, filter=SOLO_CIMA):
        if puntuacion >= UMBRAL_CIMA:
            trozos.append(trozo)

    # Paso 2: por cada principio activo que haya salido de CIMA, buscar qué dice la WADA.
    principios = {t.metadata["principio_activo"] for t in trozos if t.metadata["fuente"] == "cima"}
    for principio in principios:
        trozos += base.similarity_search(principio, k=k, filter=SOLO_WADA)
        # Además, por palabra exacta: "Tramadol" está dentro de una lista larga de narcóticos
        # y el embedding de esa lista no se parece al de una sola palabra.
        for nombre in principio.split(" + "):
            trozos += base.similarity_search(nombre, k=2, filter=SOLO_WADA,
                                             where_document={"$contains": nombre.capitalize()})

    # Sin repetidos, conservando el orden (el mismo trozo puede salir en las dos búsquedas).
    vistos, unicos = set(), []
    for t in trozos:
        if t.page_content not in vistos:
            vistos.add(t.page_content)
            unicos.append(t)
    return unicos


def cita(trozo):
    """La etiqueta que ve el LLM delante de cada trozo y que tiene que copiar al citar."""
    m = trozo.metadata
    return f"[{m['fuente']}, p. {m['pagina']}]" if "pagina" in m else f"[{m['fuente']}]"


def llamar_llm(prompt):
    """Manda el prompt al LLM y devuelve el texto de la respuesta."""
    # temperature=0: responde casi siempre lo mismo, y la comparativa se puede repetir.
    # num_ctx: por defecto Ollama solo lee unos 2.000-4.000 tokens y cortaría el contexto sin avisar.
    return ChatOllama(model=MODELO_LLM, temperature=0, num_ctx=8192).invoke(prompt).content


def responder_sin_rag(pregunta):
    """El mismo LLM, sin contexto: es la línea base de la comparativa."""
    return llamar_llm(pregunta)


def responder_con_rag(base, pregunta):
    """Devuelve (respuesta, trozos) para poder enseñar las fuentes en la app."""
    trozos = recuperar(base, pregunta)
    contexto = "\n\n".join(f"{cita(t)}\n{t.page_content}" for t in trozos)
    return llamar_llm(PROMPT_RAG.format(contexto=contexto, pregunta=pregunta)), trozos


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
            print("  -", cita(t), t.page_content[:80].replace("\n", " "))
