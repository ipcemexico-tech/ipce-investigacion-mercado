"""Cliente para la API del Banco de Indicadores de INEGI (INPC, macro).

Documentado en el Anexo técnico A.3 del Informe_IPCE.docx.

Nota (2026-07-20): probado en vivo contra varias combinaciones de
indicador/área/fuente (incluido el indicador de demostración oficial de
INEGI, Población total = 1002000001, área 0700, con BIE y BISE, recientes
true/false). Todas devolvieron ErrorCode:100 "No se encontraron
resultados" — una respuesta bien formada, no un error de red ni de
autenticación (el mismo resultado se obtuvo con un token inválido de
prueba, así que ese error no distingue token válido de inválido). No se
pudo confirmar en vivo el indicador_id/área correctos para INPC; pendiente
de validar con el usuario o la documentación de su cuenta de INEGI.
"""
from __future__ import annotations

import requests

from ipce_market_research.config import inegi_indicadores_token

BASE_URL = "https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR"

# Indicador INPC general (Índice Nacional de Precios al Consumidor) — sin confirmar en vivo.
INPC_GENERAL = "628194"

# Área geográfica nacional ('Estados Unidos Mexicanos') — sin confirmar en vivo.
AREA_NACIONAL = "0700"


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
