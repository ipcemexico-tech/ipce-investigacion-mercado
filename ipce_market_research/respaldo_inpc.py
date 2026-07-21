"""Respaldo determinista (sin IA, sin costo) para el INPC: lee el boletín
mensual oficial que INEGI publica en PDF cuando la API de Indicadores no
responde.

Verificado contra un boletín real (2026-07-21): el texto del boletín
mensual sigue siempre el mismo patrón narrativo, por ejemplo:

    "En mayo de 2026, el INPC presentó un nivel de 145.527: disminuyó
    0.21 % respecto al mes anterior. Con este resultado, la inflación
    general anual se ubicó en 3.94 por ciento."

y se distingue del boletín quincenal (que no queremos) porque este último
dice 'Próxima publicación quincenal' en vez de 'Próxima publicación
mensual'.

La URL exacta del boletín del mes actual no sigue un patrón 100% predecible
(sufijos '1q'/'2q' no corresponden de forma obvia a quincena vs. mes), así
que se prueban varias URLs candidatas para los últimos meses y se usa la
primera que (a) descarga y (b) contiene el patrón del boletín mensual.
"""
from __future__ import annotations

import re
from datetime import date

import requests

BASE_URL = "https://www.inegi.org.mx/contenidos/saladeprensa/boletines/{anio}/inpc/inpc_{sufijo}{anio}_{mes:02d}.pdf"

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]

PATRON_NIVEL = re.compile(
    r"En\s+(\w+)\s+de\s+(\d{4}),\s+el\s+INPC\s+present[oó]\s+un\s+nivel\s+de\s+([\d.,]+)\s*:?\s*"
    r"(aument[oó]|disminuy[oó])\s+([\d.]+)\s*%\s+respecto\s+al\s+mes\s+anterior"
    r".*?inflaci[oó]n\s+general\s+anual\s+se\s+ubic[oó]\s+en\s+([\d.]+)\s*por\s+ciento",
    re.IGNORECASE | re.DOTALL,
)


class BoletinNoEncontrado(RuntimeError):
    pass


def _candidatas(hoy: date):
    anio, mes = hoy.year, hoy.month
    for _ in range(4):
        for sufijo in ("2q", "1q", "3q"):
            yield BASE_URL.format(anio=anio, sufijo=sufijo, mes=mes)
        mes -= 1
        if mes == 0:
            mes = 12
            anio -= 1


def _extraer_texto_pdf(contenido: bytes) -> str:
    import io

    import pdfplumber

    with pdfplumber.open(io.BytesIO(contenido)) as pdf:
        return pdf.pages[0].extract_text() or ""


def obtener_inpc_desde_boletin(timeout: int = 30) -> dict:
    """Descarga el boletín mensual más reciente disponible y extrae el
    nivel del INPC general, la variación mensual y la anual.

    No usa IA ni ninguna credencial — es puramente determinista y gratis.
    """
    for url in _candidatas(date.today()):
        try:
            resp = requests.get(url, timeout=timeout)
        except requests.RequestException:
            continue
        if resp.status_code != 200:
            continue
        try:
            texto = _extraer_texto_pdf(resp.content)
        except Exception:  # noqa: BLE001 — PDF corrupto o no es el boletín esperado
            continue
        if "Próxima publicación mensual" not in texto:
            continue
        m = PATRON_NIVEL.search(texto)
        if not m:
            continue
        mes_nombre, anio, nivel, direccion, variacion_mensual, variacion_anual = m.groups()
        signo = "-" if direccion.lower().startswith("disminuy") else "+"
        return {
            "fuente_url": url,
            "periodo": f"{mes_nombre} {anio}",
            "nivel_inpc": nivel,
            "variacion_mensual_pct": f"{signo}{variacion_mensual}",
            "variacion_anual_pct": variacion_anual,
        }
    raise BoletinNoEncontrado(
        "No se encontró un boletín mensual de INPC reconocible entre las URLs candidatas probadas."
    )


if __name__ == "__main__":
    print(obtener_inpc_desde_boletin())
