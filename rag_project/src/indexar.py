"""Fase B: chunking + embeddings + base vectorial (P2).

Lee data/processed/corpus.jsonl, lo trocea y guarda los trozos con sus
embeddings en ChromaDB (carpeta chroma/, no se sube a git: se regenera).

Ejecutar desde rag_project/:  python src/indexar.py
"""
import json
from pathlib import Path

CARPETA = Path(__file__).resolve().parent.parent
CORPUS = CARPETA / "data" / "processed" / "corpus.jsonl"
CHROMA = CARPETA / "chroma"

# Multilingüe: las preguntas van en español y muchos documentos en inglés.
# Lee como máximo 512 tokens por trozo; eso pone un techo al tamaño de trozo.
# Este modelo espera "query: " delante de las preguntas y "passage: " delante de los trozos.
MODELO_EMBEDDINGS = "intfloat/multilingual-e5-small"

# El experimento de chunking compara estos tamaños (en caracteres); el solape es ~10-15 %.
TAMANOS = [300, 800, 1500]
SOLAPE = 100


def cargar_corpus():
    """Devuelve una lista de Document(page_content=texto, metadata={fuente, url, pagina})."""
    pass


def trocear(documentos, tamano, solape):
    """Parte los documentos con RecursiveCharacterTextSplitter. Los trozos heredan la metadata."""
    pass


def indexar(trozos, coleccion):
    """Crea (o recrea) la colección en Chroma con persist_directory=CHROMA."""
    # Una colección por tamaño, p. ej. "trozos_800", para poder compararlas en evaluar.py
    pass


def main():
    # cargar_corpus() una vez → por cada tamaño: trocear → indexar
    # Imprimir cuántos trozos salen con cada tamaño (va a la web, 02-arquitectura).
    pass


if __name__ == "__main__":
    main()
