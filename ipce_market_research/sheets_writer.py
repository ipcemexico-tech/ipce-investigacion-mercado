"""Escribe en el Dashboard_IPCE (Google Sheets nativo) usando la cuenta de
servicio de Google Cloud (Anexo técnico A.4/A.5).

Diseño deliberadamente conservador: nunca escribe directamente en las
hojas que el usuario edita a mano (Resumen, Macro, Sector_Competencia,
etc.) — todavía no hay un mapeo confirmado de qué celda exacta corresponde
a qué dato, y escribir a ciegas arriesga corromper formato o fórmulas
existentes. En vez de eso, cada corrida agrega una fila a una pestaña
dedicada, 'Auto_Log' (se crea sola si no existe), con fecha, fuente,
status y valor. Trasladar esos valores a las celdas del dashboard humano
es, por ahora, una revisión manual — o un paso futuro una vez que se
confirme el mapeo de celdas con el usuario.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Dashboard_IPCE (Google Sheets nativo), carpeta raíz de Drive "Investigación de Mercado IPCE".
DASHBOARD_SPREADSHEET_ID = "1q3gtCNIzRlrwp1bE1FCnGgZmK2sP_wbEBd9bwqLgr4M"

AUTO_LOG_SHEET = "Auto_Log"
AUTO_LOG_HEADERS = ["Fecha (UTC)", "Fuente", "Status", "Valor", "Detalle"]


def _get_service():
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not raw:
        raise RuntimeError("Falta la variable de entorno GOOGLE_SERVICE_ACCOUNT_JSON.")
    info = json.loads(raw)
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)


def _ensure_auto_log_sheet(service) -> None:
    meta = service.spreadsheets().get(spreadsheetId=DASHBOARD_SPREADSHEET_ID).execute()
    titles = [s["properties"]["title"] for s in meta.get("sheets", [])]
    if AUTO_LOG_SHEET in titles:
        return
    service.spreadsheets().batchUpdate(
        spreadsheetId=DASHBOARD_SPREADSHEET_ID,
        body={"requests": [{"addSheet": {"properties": {"title": AUTO_LOG_SHEET}}}]},
    ).execute()
    service.spreadsheets().values().update(
        spreadsheetId=DASHBOARD_SPREADSHEET_ID,
        range=f"{AUTO_LOG_SHEET}!A1:E1",
        valueInputOption="RAW",
        body={"values": [AUTO_LOG_HEADERS]},
    ).execute()


def append_log_row(fuente: str, status: str, valor: str, detalle: str = "") -> None:
    """Agrega una fila a Auto_Log. No toca ninguna otra pestaña del dashboard."""
    service = _get_service()
    _ensure_auto_log_sheet(service)
    fila = [datetime.now(timezone.utc).isoformat(), fuente, status, valor, detalle]
    service.spreadsheets().values().append(
        spreadsheetId=DASHBOARD_SPREADSHEET_ID,
        range=f"{AUTO_LOG_SHEET}!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": [fila]},
    ).execute()
