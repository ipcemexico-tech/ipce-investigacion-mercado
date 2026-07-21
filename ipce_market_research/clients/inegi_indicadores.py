"""Cliente para la API del Banco de Indicadores de INEGI (INPC, macro).

Documentado en el Anexo técnico A.3 del Informe_IPCE.docx.

Notas de diagnóstico en vivo:

2026-07-20: probado contra varias combinaciones de indicador/área/fuente,
todas con ErrorCode:100 "No se encontraron resultados". No distinguía si
era el token, el indicador o el área.

2026-07-21 (mañana): confirmado con el ejemplo oficial de la documentación
de INEGI que el token es válido (probado con el indicador de demostración
oficial, Población total = 1002000001, área 00 → devuelve datos reales) y
que el área nacional correcta para ESE indicador es '00'. Los indicadores
216064 y 628194 citados por fuentes de terceros no existían en el catálogo
(CL_INDICATOR también los rechazaba).

2026-07-21 (tarde): el usuario pidió consultar directamente el buscador
oficial de INEGI en vez de adivinar. Se localizó el endpoint interno real
que usa el buscador del sitio (no requiere token):
POST https://www.inegi.org.mx/app/api/buscadorcore/v1/busquedaBIE/
body: {"busqueda": "<texto>", "paginaInicio":1, "paginaFin":100,
"filtrobusqueda":"CBUSQUEDA", "filtrotema":"NULL", "orderby":"RANKING",
"orderbyAscDesc":"DESC", "metodoBusqueda":1, "busquedaCiencia":""}

Con eso se confirmaron, con título y ranking reales de INEGI, dos IDs
para "INPC > Mensual > Índice > Índice general":
- 910392 — serie vigente, "Actualización de Canasta y Ponderadores 2024"
  (la misma metodología que ya cita el Informe_IPCE). Es el que se debe
  usar.
- 628194 — serie anterior (pre-2024), la que se había supuesto antes.

Sin embargo NINGUNO de los dos responde en la API pública con token
(INDICATOR/<id>/es/<área>/...), probando área '00' y '0', y fuente 'BISE'
y 'BIE': siempre ErrorCode:100 "No se encontraron resultados". Se probó
también con un tercer indicador de un dominio totalmente distinto (Tasa
de participación laboral, 451778, también verificado como real vía el
mismo buscador) y falló igual — mientras que el indicador de demostración
oficial (Población total, 1002000001) sí funciona con área '00'.

Conclusión: esto ya no parece ser un problema de "adivinar el ID o el
área" — parece una limitación real de la API pública con token, que no
está sirviendo datos para indicadores de las familias más recientes
(posiblemente relacionado con la reorganización del catálogo BIE que
INEGI hizo a partir de diciembre 2025). Pendiente: escalar con soporte de
INEGI, o reintentar más adelante por si es un problema temporal de
sincronización de catálogos.
"""
from __future__ import annotations

import requests

from ipce_market_research.config import inegi_indicadores_token

BASE_URL = "https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR"

# Indicador INPC general mensual (Índice general), vigente — confirmado por
# el buscador oficial de INEGI (título, ranking y fecha de publicación
# reales), pero la API pública con token no lo sirve todavía (ver notas
# arriba). No es un ID inventado ni adivinado.
INPC_GENERAL = "910392"

# Área geográfica nacional ('Estados Unidos Mexicanos') — confirmado en vivo
# para el indicador de demostración (1002000001), pero NO funcionó para
# INPC_GENERAL ni para otros indicadores recientes probados.
AREA_NACIONAL = "00"

# Indicador de demostración oficial de INEGI (Población total) — confirmado en vivo,
# útil para probar que el token/pipeline funcionan sin depender del ID de INPC.
POBLACION_TOTAL_DEMO = "1002000001"


def consultar_indicador(
    indicador_id: str,
    area_geografica: str = AREA_NACIONAL,
    idioma: str = "es",
    recientes: str = "true",
    fuente: str = "BISE",
    timeout: int = 30,
) -> dict:
    """Consulta un indicador del Banco de Indicadores y devuelve el JSON crudo."""
    token = inegi_indicadores_token()
    url = (
        f"{BASE_URL}/{indicador_id}/{idioma}/{area_geografica}/{recientes}/"
        f"{fuente}/2.0/{token}?type=json"
    )
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    data = consultar_indicador(INPC_GENERAL)
    print(data)
