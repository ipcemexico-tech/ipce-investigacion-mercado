"""Carga de configuración desde variables de entorno.

Los tokens de API (Anexo técnico A.3) nunca se escriben en el código fuente;
deben existir como variables de entorno antes de ejecutar cualquier cliente.
"""
from __future__ import annotations

import os


class MissingTokenError(RuntimeError):
    pass


def get_required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise MissingTokenError(
            f"Falta la variable de entorno '{name}'. Definela antes de ejecutar "
            "(ver .env.example / Anexo técnico A.3)."
        )
    return value


def inegi_indicadores_token() -> str:
    return get_required_env("INEGI_INDICADORES_TOKEN")


def inegi_denue_token() -> str:
    return get_required_env("INEGI_DENUE_TOKEN")


def respaldo_inpc_activo() -> bool:
    """Interruptor del respaldo del INPC (boletín PDF oficial de INEGI).
    Determinista, sin IA y SIN COSTO — por eso está ACTIVO por defecto.
    Ver docs/como_activar_respaldo_ia.md."""
    return os.environ.get("RESPALDO_INPC_ACTIVO", "true").strip().lower() == "true"


def respaldo_denue_ia_activo() -> bool:
    """Interruptor del respaldo de DENUE por IA (Claude + búsqueda web).
    Genera un costo real por uso — por eso está APAGADO por defecto. Con
    'false' el sistema se comporta exactamente igual que sin esta
    función. Ver docs/como_activar_respaldo_ia.md."""
    return os.environ.get("RESPALDO_DENUE_IA_ACTIVO", "false").strip().lower() == "true"


def actualizar_celdas_dashboard_activo() -> bool:
    """Interruptor de la actualización automática de celdas visibles del
    Dashboard (Macro, Resumen, Sector_Competencia), además de Auto_Log.
    Apagado por defecto hasta confirmar, con una corrida manual real, que
    escribe donde debe — ver ipce_market_research/dashboard_updater.py."""
    return os.environ.get("ACTUALIZAR_CELDAS_DASHBOARD", "false").strip().lower() == "true"
