"""Mapeo de qué celda visible del Dashboard corresponde a cada dato de
INPC/DENUE, y cómo calcular el valor a escribir a partir de los datos que
ya produce cada fuente en scripts/run_snapshot.py.

Las celdas de este mapeo se confirmaron leyendo el contenido real del
Dashboard_IPCE (2026-07-21), no son celdas adivinadas:

- Macro!B4 (número) = nivel del INPC; Macro!C4 (texto) = variación
  mensual; Macro!D4 (texto) = periodo. Macro!B5/D5 = inflación general
  anual + periodo.
- Resumen!B6/C6 = la misma inflación general anual (duplicada en esa
  hoja) + periodo.
- Sector_Competencia!B32/C32 = estimación de establecimientos SCIAN
  541610 (hoy un rango escrito a mano) + nota de fuente.

Cobertura deliberadamente incompleta por ahora: la API oficial de
Indicadores de INEGI para el INPC nunca ha devuelto una respuesta
exitosa real en este proyecto (siempre ErrorCode:100 — ver
clients/inegi_indicadores.py), así que no existe una forma confirmada de
interpretar su JSON. En vez de adivinar esa forma, las celdas de Macro/
Resumen solo se actualizan desde el respaldo del boletín PDF (formato ya
verificado contra un boletín real). Cuando la API oficial empiece a
devolver datos de verdad, se puede agregar su propio mapeo con el mismo
patrón, ya confirmado con datos reales en mano — no antes.

Para DENUE sí se cubren ambos caminos (API oficial y respaldo por IA),
porque el formato de ambos ya está confirmado: la API oficial de
Cuantificar simplemente devuelve un entero como texto plano, y el
respaldo por IA devuelve un dict con formato fijo (ver respaldo_denue.py).
"""
from __future__ import annotations

from ipce_market_research.dashboard_updater import CeldaObjetivo

MESES = {
    "enero": "Enero", "febrero": "Febrero", "marzo": "Marzo", "abril": "Abril",
    "mayo": "Mayo", "junio": "Junio", "julio": "Julio", "agosto": "Agosto",
    "septiembre": "Septiembre", "octubre": "Octubre", "noviembre": "Noviembre",
    "diciembre": "Diciembre",
}


def _formatear_periodo(periodo: str) -> str:
    """'junio 2026' -> 'Junio 2026' (mismo formato que ya usa el Dashboard)."""
    partes = periodo.strip().split()
    if len(partes) != 2:
        return periodo.strip()
    mes, anio = partes
    return f"{MESES.get(mes.lower(), mes.capitalize())} {anio}"


def _nivel(datos: dict) -> float:
    return float(datos["nivel_inpc"])


def _variacion_mensual(datos: dict) -> str:
    return f"{datos['variacion_mensual_pct']}% mensual"


def _variacion_anual(datos: dict) -> str:
    return f"{datos['variacion_anual_pct']}%"


def _periodo(datos: dict) -> str:
    return _formatear_periodo(datos["periodo"])


# INPC — solo desde el respaldo del boletín (ver docstring del módulo).
# datos esperado: {"nivel_inpc", "variacion_mensual_pct", "variacion_anual_pct", "periodo"}
# (exactamente lo que devuelve respaldo_inpc.obtener_inpc_desde_boletin()).
OBJETIVOS_INPC_RESPALDO_BOLETIN = [
    CeldaObjetivo("Macro", "B4", "numero", _nivel),
    CeldaObjetivo("Macro", "C4", "texto", _variacion_mensual),
    CeldaObjetivo("Macro", "D4", "texto", _periodo),
    CeldaObjetivo("Macro", "B5", "texto", _variacion_anual),
    CeldaObjetivo("Macro", "D5", "texto", _periodo),
    CeldaObjetivo("Resumen", "B6", "texto", _variacion_anual),
    CeldaObjetivo("Resumen", "C6", "texto", _periodo),
]


def _denue_valor_oficial(datos: dict) -> str:
    conteo = int(datos["conteo"])
    return f"{conteo:,}"


def _denue_nota_oficial(datos: dict) -> str:
    return f"DENUE Cuantificar (oficial), {datos['fecha']}"


def _denue_valor_respaldo(datos: dict) -> str:
    valor = str(datos["valor"]).strip()
    if not any(ch.isdigit() for ch in valor):
        raise ValueError(f"El valor de respaldo no contiene ningún dígito, no se puede usar: {valor!r}")
    return f"{valor} (respaldo IA, no oficial)"


def _denue_nota_respaldo(datos: dict) -> str:
    fecha = datos.get("fecha_dato") or "fecha no disponible"
    return f"Respaldo IA (investigación web) — NO oficial, dato a {fecha}"


# datos esperado: {"conteo": int, "fecha": str}
OBJETIVOS_DENUE_OFICIAL = [
    CeldaObjetivo("Sector_Competencia", "B32", "texto", _denue_valor_oficial),
    CeldaObjetivo("Sector_Competencia", "C32", "texto", _denue_nota_oficial),
]

# datos esperado: igual que respaldo_denue.investigar_denue_541610()
# ({"valor", "fecha_dato", "fuente_url", "confianza", "nota"}).
OBJETIVOS_DENUE_RESPALDO = [
    CeldaObjetivo("Sector_Competencia", "B32", "texto", _denue_valor_respaldo),
    CeldaObjetivo("Sector_Competencia", "C32", "texto", _denue_nota_respaldo),
]
