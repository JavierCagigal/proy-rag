"""Fase C: comparativa sin RAG / con RAG y experimento de chunking (P2).

Lee evaluacion/preguntas.csv y guarda en resultados/:
  - comparativa.csv: respuesta sin RAG, respuesta con RAG y fuentes recuperadas.
    El veredicto (correcta / parcial / inventada / no sabe) lo ponemos a mano después,
    en las columnas veredicto_sin_rag y veredicto_con_rag.
  - chunking.csv: por cada tamaño de trozo y pregunta, si los trozos recuperados
    incluyen las páginas donde está la respuesta (acierto) y el dato exacto (dato).

Ejecutar desde rag_project/:  python src/evaluar.py            (las dos cosas)
                              python src/evaluar.py chunking   (solo el experimento, sin LLM)
"""
import re
import sys
import time
from pathlib import Path

import pandas as pd

from indexar import TAMANOS
from rag import cargar_base, cita, recuperar, responder_con_rag, responder_sin_rag

CARPETA = Path(__file__).resolve().parent.parent
PREGUNTAS = CARPETA / "evaluacion" / "preguntas.csv"
RESULTADOS = CARPETA / "resultados"


def fuentes_esperadas(texto):
    """Dónde está la respuesta, como lista de alternativas (separadas por "|").

    'cima + lista_prohibida_wada p.9' -> [{('cima', None), ('lista_prohibida_wada', 9)}]
    'reglamento_world_triathlon p.34 | reglamento_fetri p.28' -> [{(..., 34)}, {(..., 28)}]
    """
    alternativas = []
    for alternativa in texto.split("|"):
        esperadas = set()
        for parte in alternativa.split("+"):
            m = re.match(r"\s*(\w+)(?:\s+p\.(\d+))?", parte)
            if m and m.group(1) != "ninguna":
                esperadas.add((m.group(1), int(m.group(2)) if m.group(2) else None))
        if esperadas:
            alternativas.append(esperadas)
    return alternativas


def acierta(trozos, alternativas):
    """True si los trozos incluyen todas las fuentes (y páginas) de alguna de las alternativas."""
    recuperadas = {(t.metadata["fuente"], t.metadata.get("pagina")) for t in trozos}
    recuperadas |= {(fuente, None) for fuente, _ in recuperadas}  # "cima" va sin página
    return any(esperadas <= recuperadas for esperadas in alternativas)


def experimento_chunking():
    preguntas = pd.read_csv(PREGUNTAS)
    filas = []
    for tamano in TAMANOS:
        base = cargar_base(f"trozos_{tamano}")
        for _, p in preguntas.iterrows():
            esperadas = fuentes_esperadas(p["fuente"])
            if not esperadas:  # la pregunta de control no tiene respuesta en el corpus
                continue
            trozos = recuperar(base, p["pregunta"])
            texto = "\n".join(t.page_content for t in trozos)
            filas.append({"tamano": tamano, "id": p["id"], "acierto": acierta(trozos, esperadas),
                          # Más estricto: ¿está el dato exacto, o el trozo lo ha cortado?
                          "dato": re.search(p["dato_clave"], texto) is not None,
                          "n_trozos": len(trozos), "caracteres_contexto": sum(len(t.page_content) for t in trozos),
                          "recuperadas": " ".join(cita(t) for t in trozos)})
    tabla = pd.DataFrame(filas)
    RESULTADOS.mkdir(exist_ok=True)
    tabla.to_csv(RESULTADOS / "chunking.csv", index=False)
    resumen = tabla.groupby("tamano").agg(pagina_correcta=("acierto", "sum"), dato_exacto=("dato", "sum"),
                                          preguntas=("acierto", "size"),
                                          contexto_medio=("caracteres_contexto", "mean"))
    print(resumen.round(0).to_string())
    return tabla


def comparar():
    preguntas = pd.read_csv(PREGUNTAS)
    base = cargar_base()
    filas = []
    for _, p in preguntas.iterrows():
        inicio = time.time()
        sin_rag = responder_sin_rag(p["pregunta"])
        con_rag, trozos = responder_con_rag(base, p["pregunta"])
        filas.append({"id": p["id"], "pregunta": p["pregunta"], "respuesta_esperada": p["respuesta_esperada"],
                      "respuesta_sin_rag": sin_rag, "respuesta_con_rag": con_rag,
                      "fuentes_recuperadas": " ".join(cita(t) for t in trozos),
                      "veredicto_sin_rag": "", "veredicto_con_rag": ""})
        print(f"  pregunta {p['id']} ({time.time() - inicio:.0f} s)")
    RESULTADOS.mkdir(exist_ok=True)
    pd.DataFrame(filas).to_csv(RESULTADOS / "comparativa.csv", index=False)


if __name__ == "__main__":
    experimento_chunking()
    if "chunking" not in sys.argv:
        comparar()
