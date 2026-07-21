"""Agrega gráficos nativos (embebidos, conectados a los datos) al
Dashboard_IPCE en Google Sheets: Sector_Competencia, Gasto_Capacitacion
(x2), Salarios, Certificaciones y un velocímetro en Resumen.

Requiere GOOGLE_SERVICE_ACCOUNT_JSON (mismo mecanismo que sheets_writer.py)
y permiso de escritura sobre el Dashboard. Se ejecuta una sola vez, de
forma manual — no forma parte de la corrida programada de INPC/DENUE.

Por qué las celdas de datos no se grafican directamente: los valores como
"42.6%" o "$17,010–$18,302" están guardados como texto (para que se lean
bien en la tabla), no como números — un gráfico nativo necesita números.
Este script agrega columnas numéricas auxiliares, claramente etiquetadas
como "para gráfico, no editar a mano", junto a cada tabla, y los gráficos
apuntan a esas columnas. Cuando el valor de origen cambie, hay que
actualizar también la columna numérica auxiliar para que el gráfico
refleje el cambio (no se recalculan solas desde el texto).

Cada gráfico se crea con su propia llamada a la API (no todas en un solo
batchUpdate) para que un problema en un gráfico no impida crear los demás
— esto importa especialmente para el velocímetro de Resumen, cuyo esquema
(GaugeChartSpec) no se pudo verificar en vivo contra la documentación de
Google antes de escribir este script (acceso de red bloqueado).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ipce_market_research.sheets_writer import DASHBOARD_SPREADSHEET_ID, _get_service  # noqa: E402


def _sheet_ids(service) -> dict:
    meta = service.spreadsheets().get(spreadsheetId=DASHBOARD_SPREADSHEET_ID).execute()
    return {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta["sheets"]}


def _values_update(service, rango: str, valores: list) -> None:
    service.spreadsheets().values().update(
        spreadsheetId=DASHBOARD_SPREADSHEET_ID,
        range=rango,
        valueInputOption="USER_ENTERED",
        body={"values": valores},
    ).execute()


def _grid_range(sheet_id: int, start_row: int, end_row: int, start_col: int, end_col: int) -> dict:
    """Filas/columnas 1-indexadas inclusivas (como se ven en la hoja);
    se convierten aquí al formato 0-indexado semiabierto que pide la API."""
    return {
        "sheetId": sheet_id,
        "startRowIndex": start_row - 1,
        "endRowIndex": end_row,
        "startColumnIndex": start_col - 1,
        "endColumnIndex": end_col,
    }


def _chart_data(sheet_id: int, start_row: int, end_row: int, col: int) -> dict:
    return {"sourceRange": {"sources": [_grid_range(sheet_id, start_row, end_row, col, col)]}}


def _add_chart(service, chart_spec: dict, sheet_id: int, anchor_row: int, anchor_col: int, nombre: str) -> None:
    request = {
        "requests": [
            {
                "addChart": {
                    "chart": {
                        "spec": chart_spec,
                        "position": {
                            "overlayPosition": {
                                "anchorCell": {
                                    "sheetId": sheet_id,
                                    "rowIndex": anchor_row - 1,
                                    "columnIndex": anchor_col - 1,
                                },
                                "widthPixels": 480,
                                "heightPixels": 320,
                            }
                        },
                    }
                }
            }
        ]
    }
    try:
        service.spreadsheets().batchUpdate(spreadsheetId=DASHBOARD_SPREADSHEET_ID, body=request).execute()
        print(f"OK — gráfico creado: {nombre}")
    except Exception as exc:  # noqa: BLE001 — un gráfico no debe tumbar los demás
        print(f"::warning::Falló el gráfico '{nombre}': {exc}")


def _column_chart_spec(
    titulo: str,
    sheet_id: int,
    domain_col: int,
    domain_row_ini: int,
    domain_row_fin: int,
    series_defs: list[tuple[int, int, int]],
    header_count: int,
) -> dict:
    """series_defs: lista de (columna, fila_inicio, fila_fin), alineada
    fila a fila con el dominio. header_count=1 si la primera fila de cada
    rango (dominio y series) es un encabezado; 0 si son puros datos."""
    return {
        "title": titulo,
        "basicChart": {
            "chartType": "COLUMN",
            "legendPosition": "BOTTOM_LEGEND",
            "headerCount": header_count,
            "domains": [{"domain": _chart_data(sheet_id, domain_row_ini, domain_row_fin, domain_col)}],
            "series": [
                {"series": _chart_data(sheet_id, fila_ini, fila_fin, col), "targetAxis": "LEFT_AXIS"}
                for col, fila_ini, fila_fin in series_defs
            ],
        },
    }


def main() -> None:
    service = _get_service()
    ids = _sheet_ids(service)

    # ---------- 1) Sector_Competencia: Top 3 estados ----------
    sid = ids["Sector_Competencia"]
    _values_update(
        service,
        "Sector_Competencia!F24:G27",
        [
            ["% Producción bruta (valor, para gráfico)", "% Personal ocupado (valor, para gráfico)"],
            [0.426, 0.358],
            [0.094, 0.105],
            [0.075, 0.082],
        ],
    )
    spec = _column_chart_spec(
        "Top 3 estados — % Producción bruta y % Personal ocupado (consultoría, Censo 2019)",
        sid,
        domain_col=1, domain_row_ini=24, domain_row_fin=27,
        series_defs=[(6, 24, 27), (7, 24, 27)],  # F, G — incluyen fila de encabezado
        header_count=1,
    )
    _add_chart(service, spec, sid, anchor_row=36, anchor_col=1, nombre="Sector_Competencia — Top 3 estados")

    # ---------- 2a) Gasto_Capacitacion: IMCO decil 1 vs decil 10 ----------
    sid = ids["Gasto_Capacitacion"]
    _values_update(
        service,
        "Gasto_Capacitacion!E7:F9",
        [
            ["Categoría (gráfico)", "% gasto en educación (valor)"],
            ["Decil 1 (bajos ingresos)", 0.13],
            ["Decil 10 (altos ingresos)", 0.21],
        ],
    )
    spec = _column_chart_spec(
        "% del gasto del hogar destinado a educación, por decil de ingreso (IMCO sobre ENIGH)",
        sid,
        domain_col=5, domain_row_ini=7, domain_row_fin=9,  # E
        series_defs=[(6, 7, 9)],  # F
        header_count=1,
    )
    _add_chart(service, spec, sid, anchor_row=29, anchor_col=1, nombre="Gasto_Capacitacion — IMCO por decil")

    # ---------- 2b) Gasto_Capacitacion: AMAI, proxy de gasto en alimentos ----------
    # A/B (alto) no tiene dato publicado por AMAI para esta columna — se omite
    # del rango en vez de graficarlo como cero.
    _values_update(
        service,
        "Gasto_Capacitacion!F21:F26",
        [[0.32], [0.36], [0.38], [0.42], [0.46], [0.52]],
    )
    spec = _column_chart_spec(
        "% del gasto en alimentos por nivel socioeconómico (AMAI) — proxy INVERSO de capacidad "
        "económica: a menor % en alimentos, mayor disponibilidad para otros gastos como educación. "
        "Excluye A/B: AMAI no publicó ese dato en texto.",
        sid,
        domain_col=1, domain_row_ini=21, domain_row_fin=26,  # A: C+ .. E
        series_defs=[(6, 21, 26)],  # F, sin fila de encabezado
        header_count=0,
    )
    _add_chart(service, spec, sid, anchor_row=29, anchor_col=8, nombre="Gasto_Capacitacion — AMAI (proxy alimentos)")

    # ---------- 3) Salarios ----------
    sid = ids["Salarios"]
    _values_update(
        service,
        "Salarios!E11:F17",
        [
            ["Puesto (corto, gráfico)", "Sueldo mensual (valor, promedio si es rango)"],
            ["Quality Manager", 25669],
            ["Ing. de Procesos", 17656],
            ["Gerente de Calidad", 17571],
            ["Ing. Industrial", 14531],
            ["Analista de Procesos", 13841],
            ["Auditor de Calidad", 11564],
        ],
    )
    spec = _column_chart_spec(
        "Sueldos mensuales — puestos de calidad/procesos (MXN; promedio cuando la fuente da un rango)",
        sid,
        domain_col=5, domain_row_ini=11, domain_row_fin=17,  # E
        series_defs=[(6, 11, 17)],  # F
        header_count=1,
    )
    _add_chart(service, spec, sid, anchor_row=20, anchor_col=1, nombre="Salarios — puestos de calidad/procesos")

    # ---------- 4) Certificaciones ----------
    sid = ids["Certificaciones"]
    _values_update(
        service,
        "Certificaciones!F22:G29",
        [
            ["Certificación (gráfico)", "Costo (valor, MXN, promedio si es rango)"],
            ["EC0217.01 (CONOCER)", 7575],
            ["Auditor Líder ISO 9001", 26900],
            ["Gestión de Riesgos ISO 31000", 6699],
            ["CBPA (ABPMP)", 7400],
            ["CBPP (ABPMP)", 9250],
            ["TOGAF Parte 1+2", 9700],
            ["Lean Six Sigma Black Belt", 25900],
        ],
    )
    spec = _column_chart_spec(
        "Costos de certificación — CONOCER vs. internacionales (MXN; promedio cuando la fuente da un "
        "rango; excluye EC0264/EC1189 y CMMI por precio no confirmado)",
        sid,
        domain_col=6, domain_row_ini=22, domain_row_fin=29,  # F
        series_defs=[(7, 22, 29)],  # G
        header_count=1,
    )
    _add_chart(service, spec, sid, anchor_row=41, anchor_col=1, nombre="Certificaciones — CONOCER vs. internacionales")

    # ---------- 5) Resumen: velocímetro tamaño de mercado vs. IPCE ----------
    # B24 pasa de texto de relleno ("completar B23") a una fórmula real:
    # con B23 sin llenar (texto "[COMPLETAR]"), da 0 de forma segura; en
    # cuanto el usuario ponga un número en B23, el velocímetro se actualiza solo.
    sid_resumen = ids["Resumen"]
    _values_update(
        service,
        "Resumen!B24",
        [["=IF(ISNUMBER(B23), B23/B22*100, 0)"]],
    )
    gauge_spec = {
        "title": "Participación de mercado estimada de IPCE (%) — escala 0-5%, ajustar el máximo "
        "cuando se conozca el ingreso real de IPCE",
        "gaugeChart": {
            "dataRange": _chart_data(sid_resumen, 24, 24, 2),  # B24
            "min": 0,
            "max": 5,
        },
    }
    _add_chart(service, gauge_spec, sid_resumen, anchor_row=27, anchor_col=1, nombre="Resumen — velocímetro de mercado")


if __name__ == "__main__":
    main()
