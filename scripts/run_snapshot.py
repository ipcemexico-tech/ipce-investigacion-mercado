"""Ejecuta una consulta programada (INPC o DENUE) y guarda un snapshot
versionado en el repo bajo data/<fuente>/.

Diseñado para correr desde GitHub Actions (Anexo técnico A.5), pero
funciona igual en local. Nunca falla "duro" por un error de la API externa
— deja constancia del error en el snapshot y en el log, para que la
corrida programada no se vea como un pipeline roto cuando el problema es
de la fuente externa, no del workflow.

Respaldo por IA (Opción 1, ver docs/como_activar_respaldo_ia.md): si la API
oficial falla Y config.respaldo_ia_activo() es True, intenta un respaldo:
- INPC: lee el boletín mensual oficial en PDF (determinista, sin costo).
- DENUE: investiga con la API de Claude + búsqueda web (con costo real).
Con RESPALDO_IA_ACTIVO=false (el default), ninguno de los dos se ejecuta —
el comportamiento es idéntico al de antes de que existiera esta función.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ipce_market_research import config  # noqa: E402
from ipce_market_research.clients import denue, inegi_indicadores  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _log_to_sheet(fuente: str, payload: dict, valor: str) -> None:
    """Registra el resultado en la pestaña Auto_Log del Dashboard. Nunca
    rompe la corrida si falla (dependencias no instaladas, credenciales no
    configuradas, permisos, etc.) — solo lo advierte en el log. La
    importación es local a esta función a propósito: si el stack de
    google-auth no está disponible, el resto del script (INPC/DENUE) debe
    seguir funcionando igual."""
    try:
        from ipce_market_research import sheets_writer

        sheets_writer.append_log_row(
            fuente=fuente,
            status=payload["status"],
            valor=valor,
            detalle=payload.get("error", ""),
        )
    except Exception as exc:  # noqa: BLE001
        print(f"::warning::No se pudo escribir en Auto_Log del Dashboard: {exc}")


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

        if config.respaldo_ia_activo():
            print("RESPALDO_IA_ACTIVO=true — intentando respaldo por investigación web...")
            try:
                from ipce_market_research import respaldo_denue

                resultado = respaldo_denue.investigar_denue_541610()
                payload["respaldo"] = {
                    "fuente": "respaldo_investigacion_web",
                    "metodo": "Claude API + búsqueda web",
                    **resultado,
                }
                print(f"::warning::Usando dato de RESPALDO (no oficial): {resultado.get('valor')}")
            except Exception as exc_respaldo:  # noqa: BLE001
                payload["respaldo"] = {
                    "fuente": "respaldo_investigacion_web",
                    "status": "error",
                    "error": str(exc_respaldo),
                }
                print(f"::warning::Respaldo por IA también falló: {exc_respaldo}")

    path = _write_snapshot("denue", payload)
    print(f"Snapshot guardado en {path}")

    if "respaldo" in payload and payload["respaldo"].get("valor"):
        _log_to_sheet("DENUE — respaldo_investigacion_web (SCIAN 541610)", payload, str(payload["respaldo"]["valor"]))
    else:
        _log_to_sheet(
            "DENUE Cuantificar (SCIAN 541610)", payload, str(payload.get("conteo_establecimientos", ""))
        )


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

    if payload["status"] == "error" and config.respaldo_ia_activo():
        print("RESPALDO_IA_ACTIVO=true — intentando respaldo con el boletín oficial (sin costo)...")
        try:
            from ipce_market_research import respaldo_inpc

            resultado = respaldo_inpc.obtener_inpc_desde_boletin()
            payload["respaldo"] = {
                "fuente": "respaldo_investigacion_web",
                "metodo": "Boletín mensual oficial INEGI (PDF, sin IA)",
                **resultado,
            }
            print(f"::warning::Usando dato de RESPALDO (no vía API): {resultado.get('nivel_inpc')}")
        except Exception as exc_respaldo:  # noqa: BLE001
            payload["respaldo"] = {
                "fuente": "respaldo_investigacion_web",
                "status": "error",
                "error": str(exc_respaldo),
            }
            print(f"::warning::Respaldo del boletín también falló: {exc_respaldo}")

    path = _write_snapshot("inpc", payload)
    print(f"Snapshot guardado en {path}")

    if "respaldo" in payload and payload["respaldo"].get("nivel_inpc"):
        _log_to_sheet(
            "INPC — respaldo_investigacion_web (boletín oficial)", payload, str(payload["respaldo"]["nivel_inpc"])
        )
    else:
        _log_to_sheet("INEGI Indicadores (INPC general)", payload, "")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=["inpc", "denue"], required=True)
    args = parser.parse_args()
    if args.target == "denue":
        run_denue()
    else:
        run_inpc()
