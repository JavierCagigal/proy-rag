"""Fase B: chunking + embeddings + base vectorial (P2).

Lee data/processed/corpus.jsonl, lo trocea y guarda los trozos con sus
embeddings en ChromaDB (carpeta chroma/, no se sube a git: se regenera).

Ejecutar desde rag_project/:  python src/indexar.py
"""
import json
import time
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

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


def crear_embeddings():
    """El modelo de embeddings, con los prefijos que espera e5. rag.py usa este mismo."""
    # normalize_embeddings: vectores de longitud 1, así la distancia coseno es directa.
    return HuggingFaceEmbeddings(
        model_name=MODELO_EMBEDDINGS,
        encode_kwargs={"prompt": "passage: ", "normalize_embeddings": True},
        query_encode_kwargs={"prompt": "query: ", "normalize_embeddings": True},
    )


def cargar_corpus():
    """Devuelve una lista de Document(page_content=texto, metadata={fuente, url, pagina})."""
    documentos = []
    with CORPUS.open(encoding="utf-8") as f:
        for linea in f:
            datos = json.loads(linea)
            texto = datos.pop("texto")
            # Chroma no admite metadata con valor None (la página de los medicamentos de CIMA).
            metadata = {clave: valor for clave, valor in datos.items() if valor is not None}
            documentos.append(Document(page_content=texto, metadata=metadata))
    return documentos


def trocear(documentos, tamano, solape):
    """Parte los documentos con RecursiveCharacterTextSplitter. Los trozos heredan la metadata."""
    # Corta primero por párrafos, luego por líneas, luego por espacios: intenta no partir frases.
    divisor = RecursiveCharacterTextSplitter(chunk_size=tamano, chunk_overlap=solape)
    return divisor.split_documents(documentos)


def indexar(trozos, coleccion, embeddings):
    """Crea (o recrea) la colección en Chroma con persist_directory=CHROMA."""
    # Una colección por tamaño, p. ej. "trozos_800", para poder compararlas en evaluar.py
    base = Chroma(collection_name=coleccion, embedding_function=embeddings,
                  persist_directory=str(CHROMA))
    base.delete_collection()  # si no, al volver a ejecutar se duplicarían los trozos
    return Chroma.from_documents(trozos, embeddings, collection_name=coleccion,
                                 persist_directory=str(CHROMA),
                                 collection_metadata={"hnsw:space": "cosine"})


def main():
    documentos = cargar_corpus()
    embeddings = crear_embeddings()
    print(f"{len(documentos)} documentos en el corpus")
    for tamano in TAMANOS:
        inicio = time.time()
        trozos = trocear(documentos, tamano, SOLAPE)
        indexar(trozos, f"trozos_{tamano}", embeddings)
        print(f"  trozos_{tamano}: {len(trozos)} trozos ({time.time() - inicio:.0f} s)")


if __name__ == "__main__":
    main()
