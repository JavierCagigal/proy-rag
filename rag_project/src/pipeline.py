"""Fase A: pipeline de datos (P1).

Descarga las fuentes, saca el texto, lo limpia y lo deja en
data/processed/corpus.jsonl sin ningún paso manual.

Ejecutar desde rag_project/:  python src/pipeline.py
"""
import json
from pathlib import Path

CARPETA = Path(__file__).resolve().parent.parent  # rag_project/
RAW = CARPETA / "data" / "raw"
PROCESSED = CARPETA / "data" / "processed"
CORPUS = PROCESSED / "corpus.jsonl"

# Una entrada por fuente. Rellenad las URL reales (ver GUIA_PROYECTO.md, apartado 2).
FUENTES = [
    # {"nombre": "reglamento_world_triathlon", "tipo": "pdf", "url": "https://..."},
    # {"nombre": "lista_prohibida_wada_2026", "tipo": "pdf", "url": "https://..."},
    # {"nombre": "issn_cafeina", "tipo": "api", "url": "https://www.ebi.ac.uk/europepmc/webservices/rest/..."},
]


def descargar(fuente):
    """Guarda la fuente en data/raw/ y devuelve la ruta. Si ya está, no la baja otra vez."""
    # 1. ruta = RAW / (nombre + extensión según el tipo)
    # 2. Si ruta.exists(): devolverla
    # 3. requests.get(url, timeout=60) → raise_for_status() → ruta.write_bytes(...)
    pass


def extraer_paginas(ruta, fuente):
    """Devuelve una lista de (numero_de_pagina, texto). Un PDF da una por página."""
    # PDF: pypdf.PdfReader(ruta).pages → page.extract_text()
    # HTML: BeautifulSoup(...).get_text()  /  API: el campo de texto del JSON
    pass


def limpiar(texto):
    """Quita cabeceras y pies repetidos, guiones de fin de línea y espacios de sobra."""
    pass


def main():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    # Por cada fuente: descargar → extraer_paginas → limpiar.
    # Escribir una línea JSON por página en CORPUS (este formato es el que lee indexar.py):
    #   {"fuente": "...", "url": "...", "pagina": 3, "texto": "..."}
    # Saltar las páginas que queden vacías. Al final, imprimir cuántas páginas hay por fuente.
    pass


if __name__ == "__main__":
    main()
