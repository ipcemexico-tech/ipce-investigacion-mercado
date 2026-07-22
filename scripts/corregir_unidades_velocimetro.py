"""Corrige el desajuste de unidades del velocímetro de mercado en
Resumen (B22:B24): B22 (producción bruta, tamaño de mercado) está en
MILLONES de pesos, pero B23 (ingresos de IPCE) se captura naturalmente
en pesos normales — la fórmula original no convertía, así que un valor
en pesos normales inflaba el resultado ~1,000,000x (reportado: 1325% en
vez de ~0.0013%).

Se ejecuta una sola vez, de forma manual — no forma parte de la corrida
programada de INPC/DENUE.

Diseño conservador (mismo patrón que agregar_graficos_dashboard.py):
antes de escribir en cada celda, se lee su contenido actual y solo se
sobrescribe si coincide con lo que se espera encontrar (el estado
"roto" original o ya el estado "corregido", para poder reintentar sin
duplicar esfuerzo) — si el usuario cambió algo distinto desde entonces,
esa celda puntual se salta con una advertencia en vez de forzarse.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ipce_market_research.sheets_writer import DASHBOARD_SPREADSHEET_ID, _get_service  # noqa: E402

HOJA = "Resumen"

FORMULA_VIEJA = "=IF(ISNUMBER(B23), B23/B22*100, 0)"
FORMULA_NUEVA = "=IF(ISNUMBER(B23), (B23/1000000)/B22*100, 0)"

A22_VIEJO = "Producción bruta anual SCIAN 541610 (tamaño de mercado, referencia)"
A22_NUEVO = "Producción bruta anual SCIAN 541610 (tamaño de mercado, referencia) — EN MILLONES DE PESOS"

C22_VIEJO = "INEGI-CNEC, millones de pesos, 2018"
C22_NUEVO = "INEGI-CNEC, EN MILLONES DE PESOS, 2018"

A23_VIEJO = "Ingresos anuales estimados de IPCE"
A23_NUEVO = "Ingresos anuales estimados de IPCE — EN PESOS NORMALES (NO millones)"

C23_VIEJO = "Dato interno — no disponible para Claude"
C23_NUEVO = (
    "Dato interno — no disponible para Claude. Captura el monto en PESOS normales "
    "(ej. 800000), la fórmula ya lo convierte a millones automáticamente."
)

# Valor de respaldo manual que el usuario puso en B23 (0.8 millones = 800,000
# pesos) para compensar a mano la fórmula rota. Solo se restaura a pesos
# normales si B23 sigue teniendo EXACTAMENTE este valor — si el usuario ya lo
# cambió por otra cosa, no se toca.
B23_MILLONES_WORKAROUND = 0.8
B23_PESOS_NORMALES = 800000


def _leer(service, celda: str, formula: bool = False):
    resp = (
        service.spreadsheets()
        .values()
        .get(
            spreadsheetId=DASHBOARD_SPREADSHEET_ID,
            range=f"{HOJA}!{celda}",
            valueRenderOption="FORMULA" if formula else "UNFORMATTED_VALUE",
        )
        .execute()
    )
    valores = resp.get("values")
    if not valores or not valores[0]:
        return None
    return valores[0][0]


def _escribir(service, celda: str, valor) -> None:
    service.spreadsheets().values().update(
        spreadsheetId=DASHBOARD_SPREADSHEET_ID,
        range=f"{HOJA}!{celda}",
        valueInputOption="USER_ENTERED",
        body={"values": [[valor]]},
    ).execute()


def _corregir_celda_texto(service, celda: str, viejo: str, nuevo: str, nombre: str) -> None:
    actual = _leer(service, celda)
    if actual == nuevo:
        print(f"Ya aplicado (se omite): {nombre} ({celda})")
        return
    if actual != viejo:
        print(f"::warning::{nombre} ({celda}) no tiene el texto esperado (actual: {actual!r}). No se tocó.")
        return
    _escribir(service, celda, nuevo)
    print(f"OK — {nombre} ({celda}) actualizado.")


def main() -> None:
    service = _get_service()

    _corregir_celda_texto(service, "A22", A22_VIEJO, A22_NUEVO, "Etiqueta de producción bruta (unidades)")
    _corregir_celda_texto(service, "C22", C22_VIEJO, C22_NUEVO, "Nota de producción bruta (unidades)")
    _corregir_celda_texto(service, "A23", A23_VIEJO, A23_NUEVO, "Etiqueta de ingresos IPCE (unidades)")
    _corregir_celda_texto(service, "C23", C23_VIEJO, C23_NUEVO, "Nota de ingresos IPCE (unidades)")

    # B23: restaurar a pesos normales solo si sigue en el valor de workaround conocido.
    b23_actual = _leer(service, "B23")
    if b23_actual == B23_PESOS_NORMALES:
        print(f"Ya aplicado (se omite): B23 ya está en pesos normales ({b23_actual}).")
    elif b23_actual == B23_MILLONES_WORKAROUND:
        _escribir(service, "B23", B23_PESOS_NORMALES)
        print(f"OK — B23 restaurado a pesos normales: {B23_PESOS_NORMALES}.")
    else:
        print(
            f"::warning::B23 no tiene el valor de workaround esperado ({B23_MILLONES_WORKAROUND}) "
            f"ni ya está en pesos normales (actual: {b23_actual!r}). No se tocó — si es tu ingreso real, "
            "vuelve a capturarlo en PESOS normales (no millones) ahora que la fórmula ya convierte sola."
        )

    # B24: fórmula del velocímetro, con la conversión de unidades ya incluida.
    b24_actual = _leer(service, "B24", formula=True)
    if b24_actual == FORMULA_NUEVA:
        print("Ya aplicado (se omite): la fórmula de B24 ya incluye la conversión de unidades.")
    elif b24_actual == FORMULA_VIEJA:
        _escribir(service, "B24", FORMULA_NUEVA)
        print("OK — fórmula de B24 corregida (ahora convierte B23 de pesos a millones antes de dividir).")
    else:
        print(
            f"::warning::B24 no tiene la fórmula esperada (actual: {b24_actual!r}). No se tocó, para no "
            "sobrescribir una fórmula que el usuario haya cambiado a mano."
        )


if __name__ == "__main__":
    main()
