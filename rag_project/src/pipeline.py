"""Fase A: pipeline de datos (P1).

Descarga los PDFs (reglamentos y lista WADA) y los medicamentos de CIMA,
saca el texto, lo limpia y lo deja en data/processed/corpus.jsonl
sin ningún paso manual.

Ejecutar desde rag_project/:  python src/pipeline.py
"""
import json
from pathlib import Path

CARPETA = Path(__file__).resolve().parent.parent  # rag_project/
RAW = CARPETA / "data" / "raw"
PROCESSED = CARPETA / "data" / "processed"
CORPUS = PROCESSED / "corpus.jsonl"

# Los PDFs. Rellenad las URL vigentes (ver GUIA_PROYECTO.md, apartado 2).
PDFS = [
    # {"nombre": "reglamento_world_triathlon", "url": "https://..."},
    # {"nombre": "reglamento_fetri", "url": "https://..."},
    # {"nombre": "lista_prohibida_wada", "url": "https://..."},
]

# CIMA: medicamentos españoles que llevan cada principio activo.
CIMA_URL = "https://cima.aemps.es/cima/rest/medicamentos"
PRINCIPIOS_ACTIVOS = [
    # Unos 20-30 que importen en el deporte: broncodilatadores, corticoides,
    # descongestionantes, analgésicos, estimulantes... Justificad la lista en 01-datos.
    # "salbutamol", "pseudoefedrina", ...
]


def descargar_pdf(pdf):
    """Guarda el PDF en data/raw/ y devuelve la ruta. Si ya está, no lo baja otra vez."""
    # 1. ruta = RAW / (nombre + ".pdf")
    # 2. Si ruta.exists(): devolverla
    # 3. requests.get(url, timeout=60) → raise_for_status() → ruta.write_bytes(...)
    pass


def extraer_paginas(ruta):
    """Devuelve una lista de (numero_de_pagina, texto), una por página del PDF."""
    # pypdf.PdfReader(ruta).pages → page.extract_text()
    pass


def descargar_cima(principio_activo):
    """Devuelve la lista de medicamentos (dicts del JSON) que llevan ese principio activo."""
    # requests.get(CIMA_URL, params={"practiv1": principio_activo}, timeout=60).json()["resultados"]
    # Ojo: la respuesta va por páginas (totalFilas, pagina, tamanioPagina); si hay más, pedid la siguiente.
    # Guardad también el JSON en data/raw/ para no repetir la descarga.
    pass


def texto_medicamento(medicamento, principio_activo):
    """Convierte un medicamento en una frase para el corpus."""
    # Ej.: "VENTOLIN 100 microgramos/inhalación... Principio activo: salbutamol.
    #       Vía: inhalatoria. Con receta."  (campos nombre, viasAdministracion, receta)
    pass


def limpiar(texto):
    """Quita cabeceras y pies repetidos, guiones de fin de línea y espacios de sobra."""
    pass


def main():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    # Escribir en CORPUS una línea JSON por página y por medicamento (es lo que lee indexar.py):
    # 1. Cada PDF: descargar_pdf → extraer_paginas → limpiar →
    #      {"fuente": nombre, "url": url, "pagina": 3, "texto": "..."}
    #    Saltar las páginas que queden vacías.
    # 2. Cada principio activo: descargar_cima → por cada medicamento →
    #      {"fuente": "cima", "url": ..., "pagina": None, "principio_activo": "salbutamol", "texto": texto_medicamento(...)}
    # Al final, imprimir cuántas líneas hay por fuente.
    pass


if __name__ == "__main__":
    main()
