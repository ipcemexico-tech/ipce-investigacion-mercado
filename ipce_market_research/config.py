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
