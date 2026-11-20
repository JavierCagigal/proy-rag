"""Fase A: pipeline de datos (P1).

Descarga los PDFs (reglamentos y lista WADA) y los medicamentos de CIMA,
saca el texto, lo limpia y lo deja en data/processed/corpus.jsonl
sin ningún paso manual.

Ejecutar desde rag_project/:  python src/pipeline.py
"""
import json
import logging
import re
from collections import Counter
from pathlib import Path

import requests
from pypdf import PdfReader

CARPETA = Path(__file__).resolve().parent.parent  # rag_project/
RAW = CARPETA / "data" / "raw"
PROCESSED = CARPETA / "data" / "processed"
CORPUS = PROCESSED / "corpus.jsonl"

# El PDF de World Triathlon tiene referencias internas rotas; pypdf lo lee bien, pero avisa por cada una.
logging.getLogger("pypdf").setLevel(logging.ERROR)

# La web de la WADA no sirve el PDF si la petición no parece de un navegador.
CABECERAS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}

# Versiones vigentes, comprobadas el 20/11/2026 en las webs oficiales.
PDFS = [
    {"nombre": "reglamento_world_triathlon",
     "url": "https://cms.triathlon.org/download-file/world-triathlon-competition-rules-2026"},
    {"nombre": "reglamento_fetri",
     "url": "https://triatlon.org/wp-content/uploads/2026/07/Circular.4.26-Competiciones-Reglamento-de-Competiciones.pdf"},
    {"nombre": "lista_prohibida_wada",
     "url": "https://www.wada-ama.org/sites/default/files/2025-09/2026list_en_final_clean_september_2025.pdf"},
]

# CIMA: medicamentos españoles que llevan cada principio activo.
CIMA_URL = "https://cima.aemps.es/cima/rest/medicamentos"
PRINCIPIOS_ACTIVOS = [
    # Broncodilatadores beta-2 (asma): permitidos inhalados con límites, prohibidos por otras vías.
    "salbutamol", "formoterol", "salmeterol", "terbutalina",
    # Glucocorticoides: prohibidos en competición por vía oral, inyectada o rectal.
    "prednisona", "dexametasona", "budesonida", "fluticasona", "betametasona", "metilprednisolona",
    # Estimulantes y descongestionantes (antigripales).
    "pseudoefedrina", "fenilefrina", "metilfenidato", "modafinilo", "cafeina",
    # Diurético (enmascarante) y betabloqueante (solo prohibido en algunos deportes).
    "furosemida", "propranolol",
    # Analgésicos: el tramadol está prohibido en competición; la codeína, no.
    "tramadol", "codeina",
    # Hormonas y moduladores.
    "testosterona", "anastrozol",
    # Permitidos, para comprobar que el RAG también sabe decir "no da positivo".
    "ibuprofeno", "paracetamol", "cetirizina",
]


def descargar_pdf(pdf):
    """Guarda el PDF en data/raw/ y devuelve la ruta. Si ya está, no lo baja otra vez."""
    ruta = RAW / (pdf["nombre"] + ".pdf")
    if ruta.exists():
        return ruta
    respuesta = requests.get(pdf["url"], headers=CABECERAS, timeout=60)
    respuesta.raise_for_status()
    if not respuesta.content.startswith(b"%PDF"):
        raise ValueError(f"{pdf['url']} no ha devuelto un PDF")
    ruta.write_bytes(respuesta.content)
    return ruta


def extraer_paginas(ruta):
    """Devuelve una lista de (numero_de_pagina, texto), una por página del PDF."""
    lector = PdfReader(ruta)
    return [(numero, pagina.extract_text() or "") for numero, pagina in enumerate(lector.pages, start=1)]


def lineas_repetidas(paginas):
    """Líneas que salen en más de la mitad de las páginas: cabeceras y pies de página."""
    contador = Counter()
    for _, texto in paginas:
        contador.update({linea.strip() for linea in texto.splitlines() if linea.strip()})
    return {linea for linea, veces in contador.items() if veces > len(paginas) / 2}


def es_ruido(linea, repetidas):
    """Cabecera/pie repetido, línea de índice ("5.5. DRAFTING ....... 47") o número de página suelto ("35/212")."""
    linea = linea.strip()
    return (linea in repetidas
            or re.search(r"\.{5,}", linea) is not None
            or re.fullmatch(r"\d+(\s*/\s*\d+)?", linea) is not None)


def limpiar(texto, repetidas=frozenset()):
    """Quita el ruido, une palabras partidas con guion y normaliza espacios."""
    lineas = [l for l in texto.splitlines() if not es_ruido(l, repetidas)]
    texto = "\n".join(lineas)
    texto = re.sub(r"(\w)-\n(\w)", r"\1\2", texto)   # "competi-\nción" -> "competición"
    texto = re.sub(r"[ \t]+", " ", texto)             # varios espacios -> uno
    texto = re.sub(r"\n{3,}", "\n\n", texto)          # deja como mucho una línea en blanco
    return texto.strip()


def descargar_cima(principio_activo):
    """Devuelve la lista de medicamentos (dicts del JSON) que llevan ese principio activo."""
    ruta = RAW / "cima" / f"{principio_activo}.json"
    if ruta.exists():
        return json.loads(ruta.read_text(encoding="utf-8"))
    medicamentos, pagina = [], 1
    while True:  # la API va por páginas (totalFilas, pagina, tamanioPagina)
        respuesta = requests.get(CIMA_URL, params={"practiv1": principio_activo, "pagina": pagina},
                                 headers=CABECERAS, timeout=60)
        respuesta.raise_for_status()
        datos = respuesta.json()
        medicamentos += datos.get("resultados", [])
        if pagina * datos["tamanioPagina"] >= datos["totalFilas"]:
            break
        pagina += 1
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(medicamentos, ensure_ascii=False), encoding="utf-8")
    return medicamentos


def texto_medicamento(medicamento, principio_activo):
    """Convierte un medicamento en una frase para el corpus."""
    vias = ", ".join(v["nombre"].lower() for v in medicamento.get("viasAdministracion", []))
    forma = medicamento.get("formaFarmaceutica", {}).get("nombre", "").lower()
    receta = "Con receta" if medicamento.get("receta") else "Sin receta"
    return (f"{medicamento['nombre']}. Medicamento español. Principio activo: {principio_activo}. "
            f"Forma: {forma}. Vía de administración: {vias}. {receta}.")


def url_medicamento(medicamento):
    """La ficha técnica en HTML si la hay; si no, el detalle en la API."""
    for doc in medicamento.get("docs", []):
        if doc.get("tipo") == 1 and doc.get("urlHtml"):
            return doc["urlHtml"]
    return f"https://cima.aemps.es/cima/rest/medicamento?nregistro={medicamento['nregistro']}"


def lineas_pdfs():
    for pdf in PDFS:
        paginas = extraer_paginas(descargar_pdf(pdf))
        repetidas = lineas_repetidas(paginas)
        guardadas = 0
        for numero, texto in paginas:
            texto = limpiar(texto, repetidas)
            if len(texto) < 50:  # portadas, páginas en blanco o solo con un título
                continue
            guardadas += 1
            yield {"fuente": pdf["nombre"], "url": pdf["url"], "pagina": numero, "texto": texto}
        print(f"  {pdf['nombre']}: {guardadas} de {len(paginas)} páginas")


def lineas_cima():
    vistos = set()  # un medicamento con dos principios activos sale en dos búsquedas
    for buscado in PRINCIPIOS_ACTIVOS:
        for m in descargar_cima(buscado):
            # Solo los que se venden y tienen marca: los genéricos ya llevan el principio activo en el nombre.
            if not m.get("comerc") or m.get("generico") or m["nregistro"] in vistos:
                continue
            vistos.add(m["nregistro"])
            # vtm es el principio activo completo, también en combinaciones ("salbutamol + bromuro ipratropio").
            principio = ((m.get("vtm") or {}).get("nombre") or buscado).strip()
            yield {"fuente": "cima", "url": url_medicamento(m), "pagina": None,
                   "principio_activo": principio, "texto": texto_medicamento(m, principio)}
    print(f"  cima: {len(vistos)} medicamentos")


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    print("Generando el corpus:")
    lineas = list(lineas_pdfs()) + list(lineas_cima())

    # Comprobación del formato que esperan indexar.py y rag.py (AGENTS.md).
    for linea in lineas:
        assert {"fuente", "url", "pagina", "texto"} <= linea.keys(), linea
        assert linea["fuente"] != "cima" or linea.get("principio_activo"), linea

    with CORPUS.open("w", encoding="utf-8") as f:
        for linea in lineas:
            f.write(json.dumps(linea, ensure_ascii=False) + "\n")
    print(f"{len(lineas)} líneas en {CORPUS.relative_to(CARPETA)}")


if __name__ == "__main__":
    main()
