"""Ejecuta una consulta programada (INPC o DENUE) y guarda un snapshot
versionado en el repo bajo data/<fuente>/.

Diseñado para correr desde GitHub Actions (Anexo técnico A.5), pero
funciona igual en local. Nunca falla "duro" por un error de la API externa
— deja constancia del error en el snapshot y en el log, para que la
corrida programada no se vea como un pipeline roto cuando el problema es
de la fuente externa, no del workflow.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ipce_market_research.clients import denue, inegi_indicadores  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _write_snapshot(fuente: str, payload: dict) -> Path:
    fecha = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_dir = DATA_DIR / fuente
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{fecha}.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def run_denue() -> None:
    payload = {
        "fuente": "INEGI DENUE — método Cuantificar",
        "scian": "541610",
        "fecha_consulta": datetime.now(timezone.utc).isoformat(),
    }
    try:
        conteo = denue.cuantificar_establecimientos("541610")
        payload["status"] = "ok"
        payload["conteo_establecimientos"] = conteo
    except Exception as exc:  # noqa: BLE001 — se registra cualquier falla de la fuente externa
        payload["status"] = "error"
        payload["error"] = str(exc)
        print(f"::warning::DENUE Cuantificar falló: {exc}")
    path = _write_snapshot("denue", payload)
    print(f"Snapshot guardado en {path}")


def run_inpc() -> None:
    payload = {
        "fuente": "INEGI Banco de Indicadores — INPC general",
        "fecha_consulta": datetime.now(timezone.utc).isoformat(),
    }
    if not inegi_indicadores.INPC_GENERAL:
        payload["status"] = "error"
        payload["error"] = (
            "INPC_GENERAL sin configurar en ipce_market_research/clients/inegi_indicadores.py "
            "— falta confirmar el indicador_id vigente con el buscador de INEGI."
        )
        print("::warning::INPC_GENERAL no está configurado; ver clients/inegi_indicadores.py")
    else:
        try:
            data = inegi_indicadores.consultar_indicador(inegi_indicadores.INPC_GENERAL)
            payload["status"] = "ok"
            payload["respuesta"] = data
        except Exception as exc:  # noqa: BLE001
            payload["status"] = "error"
            payload["error"] = str(exc)
            print(f"::warning::Consulta INPC falló: {exc}")
    path = _write_snapshot("inpc", payload)
    print(f"Snapshot guardado en {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=["inpc", "denue"], required=True)
    args = parser.parse_args()
    if args.target == "denue":
        run_denue()
    else:
        run_inpc()
