"""Respaldo por IA (Opción 1, componente pagado) para el conteo de
establecimientos DENUE cuando el método Cuantificar de INEGI no responde.

No existe un boletín público periódico equivalente a DENUE para esta cifra
específica (conteo de establecimientos por clase SCIAN) — a diferencia del
INPC, aquí no hay atajo determinista gratis. Este módulo usa la API de
Claude con la herramienta de búsqueda web para investigar el dato más
reciente disponible en fuentes públicas, dejando siempre explícito que es
una investigación, no una lectura directa de la API oficial.

Solo se ejecuta si RESPALDO_DENUE_IA_ACTIVO=true (ver
config.respaldo_denue_ia_activo) — requiere ANTHROPIC_API_KEY y genera
costo real por uso.
"""
from __future__ import annotations

import os
import re

PROMPT_TEMPLATE = """\
Eres un asistente de investigación de datos económicos oficiales de México.

Busca en la web (prioriza fuentes oficiales: inegi.org.mx, el propio DENUE, \
boletines de INEGI; en su defecto, fuentes periodísticas o de cámaras \
empresariales confiables) el dato más reciente y específico que puedas \
encontrar sobre:

{pregunta}

Si no encuentras un dato oficial y actualizado, dilo explícitamente — nunca \
inventes ni extrapoles una cifra tú mismo.

Responde ÚNICAMENTE con estas líneas, sin texto adicional antes ni después:
VALOR: <la cifra encontrada, o 'no disponible'>
FECHA_DATO: <a qué fecha corresponde el dato, o 'no disponible'>
FUENTE_URL: <la URL de la fuente principal, o 'no disponible'>
CONFIANZA: <alta|media|baja>
NOTA: <una frase breve de contexto o limitación>
"""

DENUE_PREGUNTA = (
    "el número de establecimientos activos en México registrados bajo la "
    "clase SCIAN 541610 ('Servicios de consultoría en administración') en "
    "el Directorio Estadístico Nacional de Unidades Económicas (DENUE)"
)

LINEA_RE = re.compile(
    r"VALOR:\s*(?P<valor>.+?)\s*\n"
    r"FECHA_DATO:\s*(?P<fecha>.+?)\s*\n"
    r"FUENTE_URL:\s*(?P<fuente>.+?)\s*\n"
    r"CONFIANZA:\s*(?P<confianza>.+?)\s*\n"
    r"NOTA:\s*(?P<nota>.+)",
    re.IGNORECASE,
)


class RespaldoIANoDisponible(RuntimeError):
    pass


def investigar(pregunta: str, timeout: int = 120) -> dict:
    """Consulta la API de Claude con búsqueda web para un dato específico.
    Genera costo real por uso — solo se debe llamar cuando
    config.respaldo_denue_ia_activo() es True."""
    try:
        import anthropic
    except ImportError as exc:
        raise RespaldoIANoDisponible(
            "El paquete 'anthropic' no está instalado (agregar a requirements.txt)."
        ) from exc

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RespaldoIANoDisponible("Falta la variable de entorno ANTHROPIC_API_KEY.")

    client = anthropic.Anthropic()
    response = client.with_options(timeout=timeout).messages.create(
        model="claude-opus-4-8",
        max_tokens=1024,
        tools=[{"type": "web_search_20260209", "name": "web_search", "max_uses": 5}],
        messages=[{"role": "user", "content": PROMPT_TEMPLATE.format(pregunta=pregunta)}],
    )

    texto = "\n".join(block.text for block in response.content if block.type == "text")
    m = LINEA_RE.search(texto)
    if not m:
        return {
            "valor": None,
            "fecha_dato": None,
            "fuente_url": None,
            "confianza": None,
            "nota": "Respuesta del modelo no siguió el formato esperado.",
            "respuesta_cruda": texto,
        }
    d = m.groupdict()
    return {
        "valor": d["valor"],
        "fecha_dato": d["fecha"],
        "fuente_url": d["fuente"],
        "confianza": d["confianza"],
        "nota": d["nota"],
    }


def investigar_denue_541610() -> dict:
    return investigar(DENUE_PREGUNTA)
