"""Actualiza celdas visibles del Dashboard_IPCE (Macro, Resumen,
Sector_Competencia) cuando una corrida de INPC/DENUE trae un dato nuevo —
además de la fila que scripts/run_snapshot.py ya agrega a Auto_Log, que se
mantiene sin cambios como bitácora completa de cada corrida.

Diseño conservador (mismo espíritu que sheets_writer.py): antes de escribir
en una celda visible, se lee su valor ACTUAL y se compara su tipo (número o
texto) contra el tipo esperado para esa celda específica. Si no coincide —
por ejemplo, si alguien puso ahí una fórmula, la vació, o le cambió el
formato a mano — esa celda se deja intacta y el intento se registra como
'advertencia' en vez de forzar el valor. Cada celda se evalúa de forma
independiente, así un problema en una no cancela las demás de la misma
corrida.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ipce_market_research.sheets_writer import DASHBOARD_SPREADSHEET_ID, _get_service


@dataclass(frozen=True)
class CeldaObjetivo:
    hoja: str
    celda: str
    tipo_esperado: str  # "numero" o "texto"
    calcular_valor: Callable[[dict], object]  # datos -> valor a escribir


def _tipo_de(valor) -> str:
    if isinstance(valor, bool):
        return "otro"
    if isinstance(valor, (int, float)):
        return "numero"
    if isinstance(valor, str):
        return "texto"
    return "otro"


def _leer_valor_actual(service, hoja: str, celda: str):
    resp = (
        service.spreadsheets()
        .values()
        .get(
            spreadsheetId=DASHBOARD_SPREADSHEET_ID,
            range=f"{hoja}!{celda}",
            valueRenderOption="UNFORMATTED_VALUE",
        )
        .execute()
    )
    valores = resp.get("values")
    if not valores or not valores[0]:
        return None
    return valores[0][0]


def actualizar_celdas(service, objetivos: list[CeldaObjetivo], datos: dict) -> list[dict]:
    """Intenta actualizar cada celda objetivo, una por una. Devuelve una
    lista de resultados (uno por celda) con status 'ok', 'advertencia' o
    'error' — para poder registrarlos en Auto_Log sin que un problema en
    una celda cancele el intento de las demás."""
    resultados = []
    for obj in objetivos:
        ref = f"{obj.hoja}!{obj.celda}"

        try:
            valor_nuevo = obj.calcular_valor(datos)
        except Exception as exc:  # noqa: BLE001
            resultados.append(
                {"celda": ref, "status": "error", "valor": "", "detalle": f"No se pudo calcular el valor: {exc}"}
            )
            continue

        try:
            actual = _leer_valor_actual(service, obj.hoja, obj.celda)
        except Exception as exc:  # noqa: BLE001
            resultados.append(
                {"celda": ref, "status": "error", "valor": "", "detalle": f"No se pudo leer la celda actual: {exc}"}
            )
            continue

        tipo_actual = _tipo_de(actual)
        if tipo_actual != obj.tipo_esperado:
            resultados.append(
                {
                    "celda": ref,
                    "status": "advertencia",
                    "valor": "",
                    "detalle": (
                        f"Formato inesperado — se esperaba tipo '{obj.tipo_esperado}' pero la celda tiene "
                        f"'{tipo_actual}' (valor actual: {actual!r}). No se escribió, para no corromper el "
                        "Dashboard."
                    ),
                }
            )
            continue

        try:
            service.spreadsheets().values().update(
                spreadsheetId=DASHBOARD_SPREADSHEET_ID,
                range=ref,
                valueInputOption="USER_ENTERED",
                body={"values": [[valor_nuevo]]},
            ).execute()
            resultados.append({"celda": ref, "status": "ok", "valor": str(valor_nuevo), "detalle": f"antes: {actual!r}"})
        except Exception as exc:  # noqa: BLE001
            resultados.append({"celda": ref, "status": "error", "valor": "", "detalle": f"Falló la escritura: {exc}"})

    return resultados


def actualizar_dashboard_y_registrar(objetivos: list[CeldaObjetivo], datos: dict, contexto: str) -> list[dict]:
    """Punto de entrada usado por scripts/run_snapshot.py: obtiene su
    propio servicio de Sheets, actualiza las celdas visibles y registra
    cada resultado como una fila adicional en Auto_Log (que se sigue
    llenando exactamente igual que antes, sin cambios)."""
    from ipce_market_research import sheets_writer

    service = _get_service()
    resultados = actualizar_celdas(service, objetivos, datos)
    for r in resultados:
        sheets_writer.append_log_row(
            fuente=f"Dashboard visible: {r['celda']} ({contexto})",
            status=r["status"],
            valor=r["valor"],
            detalle=r["detalle"],
        )
    return resultados
