"""Cliente para la API del Banco de Indicadores de INEGI (INPC, macro).

Documentado en el Anexo técnico A.3 del Informe_IPCE.docx.
"""
from __future__ import annotations

import requests

from ipce_market_research.config import inegi_indicadores_token

BASE_URL = "https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR"

# Indicador INPC general (Índice Nacional de Precios al Consumidor), serie mensual.
INPC_GENERAL = "628194"


def consultar_indicador(
    indicador_id: str,
    area_geografica: str = "0700",
    idioma: str = "es",
    recientes: str = "true",
    timeout: int = 30,
) -> dict:
    """Consulta un indicador del Banco de Indicadores y devuelve el JSON crudo."""
    token = inegi_indicadores_token()
    url = (
        f"{BASE_URL}/{indicador_id}/{idioma}/{area_geografica}/{recientes}/"
        f"BISE/2.0/{token}?type=json"
    )
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    data = consultar_indicador(INPC_GENERAL)
    print(data)
