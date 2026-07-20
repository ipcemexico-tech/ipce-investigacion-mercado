"""Cliente para la API DENUE (INEGI) — Directorio Estadístico Nacional de
Unidades Económicas.

Documentado en el Anexo técnico A.3 del Informe_IPCE.docx. Usa el método
'Cuantificar' para obtener el conteo de establecimientos por clase SCIAN,
sin descargar el listado completo.
"""
from __future__ import annotations

import requests

from ipce_market_research.config import inegi_denue_token

BASE_URL = "https://www.inegi.org.mx/app/api/denue/v1/consulta/Cuantificar"


def cuantificar_establecimientos(
    scian: str,
    entidad: str = "0",
    municipio: str = "0",
    timeout: int = 30,
) -> int:
    """Devuelve el número de establecimientos activos para una clase SCIAN.

    Parameters
    ----------
    scian: clase SCIAN a 6 dígitos, p. ej. '541610'.
    entidad: clave de entidad federativa (2 dígitos) o '0' para nacional.
    municipio: clave de municipio o '0' para todos.
    """
    token = inegi_denue_token()
    url = f"{BASE_URL}/{scian}/{entidad}/{municipio}/{token}"
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return int(response.text.strip())


if __name__ == "__main__":
    conteo = cuantificar_establecimientos("541610")
    print(f"Establecimientos SCIAN 541610 (nacional): {conteo}")
