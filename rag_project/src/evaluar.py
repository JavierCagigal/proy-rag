"""Fase C: comparativa sin RAG / con RAG y experimento de chunking (P2).

Lee evaluacion/preguntas.csv y guarda en resultados/:
  - comparativa.csv: respuesta sin RAG, respuesta con RAG y fuentes recuperadas.
    El veredicto (correcta / parcial / inventada) lo ponemos a mano después,
    en las columnas veredicto_sin_rag y veredicto_con_rag.
  - chunking.csv: por cada tamaño de trozo y pregunta, si la respuesta esperada
    aparece en los trozos recuperados.

Ejecutar desde rag_project/:  python src/evaluar.py
"""
from pathlib import Path

# from rag import cargar_base, recuperar, responder_con_rag, responder_sin_rag

CARPETA = Path(__file__).resolve().parent.parent
PREGUNTAS = CARPETA / "evaluacion" / "preguntas.csv"
RESULTADOS = CARPETA / "resultados"


def comparar():
    # pd.read_csv(PREGUNTAS) → por cada fila: responder_sin_rag y responder_con_rag
    # → DataFrame → to_csv(RESULTADOS / "comparativa.csv", index=False)
    pass


def experimento_chunking():
    # Por cada colección (trozos_300, trozos_800, trozos_1500) y cada pregunta:
    # recuperar → ¿algún trozo es de la fuente correcta? ¿contiene el dato clave?
    # → RESULTADOS / "chunking.csv"
    pass


if __name__ == "__main__":
    experimento_chunking()
    comparar()
