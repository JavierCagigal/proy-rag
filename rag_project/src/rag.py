"""Recuperar + generar (P3, con P2 en recuperar).

La app y la evaluación solo usan responder_sin_rag y responder_con_rag.
llamar_llm es el único sitio que sabe qué LLM usamos: cambiar de Ollama
a una API para la versión en la nube se hace solo ahí.

Prueba rápida desde rag_project/:  python src/rag.py
"""
import os
import time

import requests
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama

from indexar import CHROMA, crear_embeddings

COLECCION = "trozos_800"  # la que gane el experimento de chunking
K = 4                     # cuántos trozos se pasan al LLM
MODELO_LLM = "qwen2.5:3b"  # en local, con Ollama
# En la nube (Cloud Run): Gemini por API. El más rápido y barato, y aún respeta temperature=0.
MODELO_GEMINI = "gemini-3.5-flash-lite"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"
# Medido con preguntas.csv (trozos_800): las preguntas de medicamentos tienen un trozo de CIMA
# con relevancia >= 0,857; las demás, <= 0,836.
UMBRAL_CIMA = 0.85
SOLO_CIMA = {"fuente": "cima"}
SOLO_WADA = {"fuente": "lista_prohibida_wada"}

PROMPT_RAG = """Eres un asistente para triatletas. Responde en español usando SOLO el contexto de abajo (puede estar en inglés).
- Los trozos [cima] dicen qué principio activo lleva un medicamento español y por qué vía se toma.
- Los trozos [lista_prohibida_wada] dicen qué sustancias están prohibidas, si solo en competición y con qué límites.
- Si preguntan por un medicamento: di su principio activo, busca esa sustancia en la lista de la WADA y explica si está prohibida, cuándo, y si depende de la vía o de la dosis.
- Da las cifras exactas del contexto y cita la fuente entre corchetes después de cada dato, por ejemplo [reglamento_fetri, p. 28].
- Solo si el contexto no tiene la respuesta, di: "No lo sé con mis fuentes".

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
    generales = base.similarity_search(pregunta, k=k)

    # Paso 1b: ¿la pregunta nombra un medicamento? Se busca solo en CIMA y se añaden los muy parecidos.
    # Hace falta porque los trozos de los reglamentos (largos y en español) suelen ganar en la búsqueda general.
    cima = [t for t in generales if t.metadata["fuente"] == "cima"]
    cima += [t for t, puntuacion in base.similarity_search_with_relevance_scores(pregunta, k=2, filter=SOLO_CIMA)
             if puntuacion >= UMBRAL_CIMA]
    if not cima:
        return sin_repetidos(generales)

    # Es una pregunta de medicamentos: la respuesta está en CIMA + WADA. Los trozos del reglamento
    # solo meten ruido, y de CIMA bastan 2 (las demás presentaciones del mismo medicamento se repiten).
    cima = sin_repetidos(cima)[:2]
    wada = [t for t in generales if t.metadata["fuente"] == "lista_prohibida_wada"]

    # Paso 2 (expansión de la consulta): por cada principio activo, buscar qué dice la WADA.
    for principio in {t.metadata["principio_activo"] for t in cima}:
        wada += base.similarity_search(principio, k=k, filter=SOLO_WADA)
        # Además, por palabra exacta: "Tramadol" está dentro de una lista larga de narcóticos
        # y el embedding de esa lista no se parece al de una sola palabra.
        for nombre in principio.split(" + "):
            wada += base.similarity_search(nombre, k=2, filter=SOLO_WADA,
                                           where_document={"$contains": nombre.capitalize()})
    return sin_repetidos(cima + wada)


def sin_repetidos(trozos):
    """Quita los trozos repetidos conservando el orden (el mismo trozo puede salir en varias búsquedas)."""
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


def modelo_en_uso():
    """Gemini si hay clave en la variable de entorno GEMINI_API_KEY (la nube); si no, Ollama (local)."""
    return MODELO_GEMINI if os.environ.get("GEMINI_API_KEY") else MODELO_LLM


def llamar_llm(prompt):
    """Manda el prompt al LLM y devuelve el texto de la respuesta."""
    clave = os.environ.get("GEMINI_API_KEY")
    if clave:
        # Hasta 5 intentos: el plan gratuito a veces responde 429 (demasiadas peticiones) o 503 (saturado).
        # Se espera 2, 4, 8 y 16 segundos entre intentos.
        for intento in range(5):
            # La clave va en una cabecera, no en la URL, para que no aparezca en registros ni errores.
            respuesta = requests.post(
                GEMINI_URL.format(modelo=MODELO_GEMINI),
                headers={"x-goog-api-key": clave},
                json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0}},
                timeout=120,
            )
            if respuesta.status_code not in (429, 500, 503) or intento == 4:
                break
            time.sleep(2 ** (intento + 1))
        respuesta.raise_for_status()
        # Gemini puede partir la respuesta en varios trozos (parts): hay que unirlos todos.
        partes = respuesta.json()["candidates"][0]["content"]["parts"]
        return "".join(parte.get("text", "") for parte in partes)
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
