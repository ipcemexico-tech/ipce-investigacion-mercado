"""Cliente para la API del Banco de Indicadores de INEGI (INPC, macro).

Documentado en el Anexo técnico A.3 del Informe_IPCE.docx.

Notas de diagnóstico en vivo:

2026-07-20: probado contra varias combinaciones de indicador/área/fuente,
todas con ErrorCode:100 "No se encontraron resultados". No distinguía si
era el token, el indicador o el área.

2026-07-21: confirmado con el ejemplo oficial de la documentación de INEGI
(https://www.inegi.org.mx/servicios/api_indicadores.html) que:
- El token SÍ es válido (probado con el indicador de demostración oficial,
  Población total = 1002000001, área 00 → devuelve datos reales).
- El área geográfica nacional correcta es '00' (dos dígitos) — anoche se
  probó '0700' y '00000', ninguno es correcto.
- El indicador 216064 (citado en fuentes de terceros, p. ej. el paquete R
  'inegiR', como INPC general) YA NO existe en el catálogo actual de INEGI
  (CL_INDICATOR/216064 también da "sin resultados") — probablemente
  renumerado en una actualización del Banco de Indicadores. El indicador
  628194 (usado como valor por defecto hasta ahora) tampoco es válido.

Pendiente: obtener el indicador_id vigente para INPC general desde el
buscador visual de INEGI (https://www.inegi.org.mx/app/indicadores/,
buscar "Índice Nacional de Precios al Consumidor" y tomar el ID de la
URL/resultado) — más rápido para un humano que seguir adivinando IDs
contra la API.
"""
from __future__ import annotations

import requests

from ipce_market_research.config import inegi_indicadores_token

BASE_URL = "https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR"

# Indicador INPC general — SIN CONFIRMAR. 216064 y 628194 fallaron en pruebas
# en vivo (2026-07-20/21). Reemplazar en cuanto se tenga el ID vigente.
INPC_GENERAL = None

# Área geográfica nacional ('Estados Unidos Mexicanos') — confirmado en vivo.
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
    if not INPC_GENERAL:
        raise SystemExit(
            "Falta confirmar INPC_GENERAL (ver notas del módulo). "
            "Prueba temporal: consultar_indicador(POBLACION_TOTAL_DEMO)."
        )
    data = consultar_indicador(INPC_GENERAL)
    print(data)
