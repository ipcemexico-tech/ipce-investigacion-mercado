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
batchUpdate) para que un problema en un gráfico no impida crear los demás.
Además, antes de crear nada el script lee los gráficos que ya existen en el
spreadsheet y omite (no duplica) los que ya están creados — así se puede
reintentar el script tantas veces como haga falta sin generar copias.

Nota sobre el velocímetro de Resumen: Google Sheets NO tiene un tipo de
gráfico "gauge" real — "gaugeChart" no es un campo válido en la API
(confirmado con un error 400 real: "Unknown name 'gaugeChart'"). Por eso
se simula con una dona (pieChart con pieHole) de 2 rebanadas.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ipce_market_research.sheets_writer import DASHBOARD_SPREADSHEET_ID, _get_service  # noqa: E402


def _sheet_ids_y_graficos_existentes(service) -> tuple[dict, set]:
    """Devuelve (sheetId por título, títulos de gráficos ya existentes en
    todo el spreadsheet) — para poder reintentar el script sin duplicar
    los gráficos que ya se crearon en una corrida anterior."""
    meta = service.spreadsheets().get(spreadsheetId=DASHBOARD_SPREADSHEET_ID).execute()
    ids = {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta["sheets"]}
    titulos_existentes = {
        chart["spec"]["title"]
        for s in meta["sheets"]
        for chart in s.get("charts", [])
        if "title" in chart.get("spec", {})
    }
    return ids, titulos_existentes


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


def _add_chart(
    service, chart_spec: dict, sheet_id: int, anchor_row: int, anchor_col: int, nombre: str, titulos_existentes: set
) -> None:
    if chart_spec["title"] in titulos_existentes:
        print(f"Ya existe (se omite, no se duplica): {nombre}")
        return
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
        titulos_existentes.add(chart_spec["title"])
    except Exception as exc:  # noqa: BLE001 — un gráfico no debe tumbar los demás
        print(f"::warning::Falló el gráfico '{nombre}': {exc}")


def _donut_gauge_spec(titulo: str, sheet_id: int, domain_row_ini: int, domain_row_fin: int, domain_col: int,
                       series_col: int) -> dict:
    """Simula un velocímetro con una dona de 2 rebanadas (valor vs. resto
    de la escala) — Google Sheets no tiene un tipo de gráfico 'gauge' real."""
    return {
        "title": titulo,
        "pieChart": {
            "legendPosition": "RIGHT_LEGEND",
            "domain": _chart_data(sheet_id, domain_row_ini, domain_row_fin, domain_col),
            "series": _chart_data(sheet_id, domain_row_ini, domain_row_fin, series_col),
            "pieHole": 0.65,
        },
    }


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
    ids, titulos_existentes = _sheet_ids_y_graficos_existentes(service)

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
    _add_chart(service, spec, sid, anchor_row=36, anchor_col=1, nombre="Sector_Competencia — Top 3 estados",
               titulos_existentes=titulos_existentes)

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
    _add_chart(service, spec, sid, anchor_row=29, anchor_col=1, nombre="Gasto_Capacitacion — IMCO por decil",
               titulos_existentes=titulos_existentes)

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
    _add_chart(service, spec, sid, anchor_row=29, anchor_col=8, nombre="Gasto_Capacitacion — AMAI (proxy alimentos)",
               titulos_existentes=titulos_existentes)

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
    _add_chart(service, spec, sid, anchor_row=20, anchor_col=1, nombre="Salarios — puestos de calidad/procesos",
               titulos_existentes=titulos_existentes)

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
    _add_chart(service, spec, sid, anchor_row=41, anchor_col=1, nombre="Certificaciones — CONOCER vs. internacionales",
               titulos_existentes=titulos_existentes)

    # ---------- 5) Resumen: "velocímetro" (dona) tamaño de mercado vs. IPCE ----------
    # Google Sheets no tiene un tipo de gráfico "gauge" real (gaugeChart no
    # existe en la API — confirmado por error 400 en un intento anterior).
    # Se simula con una dona de 2 rebanadas: participación de IPCE dentro de
    # una escala 0-5%, y el resto de esa escala.
    #
    # B24 pasa de texto de relleno ("completar B23") a una fórmula real:
    # con B23 sin llenar (texto "[COMPLETAR]"), da 0 de forma segura; en
    # cuanto el usuario ponga un número en B23, la dona se actualiza sola.
    sid_resumen = ids["Resumen"]
    _values_update(
        service,
        "Resumen!B24",
        [["=IF(ISNUMBER(B23), B23/B22*100, 0)"]],
    )
    _values_update(
        service,
        "Resumen!I27:J28",
        [
            ["Participación IPCE (dentro de escala 0-5%)", "=MIN(B24,5)"],
            ["Resto de la escala (hasta 5%)", "=MAX(0,5-B24)"],
        ],
    )
    donut_spec = _donut_gauge_spec(
        "Participación de mercado estimada de IPCE (%) — dona simula velocímetro, escala 0-5%; "
        "ajustar el máximo en I27:J28 cuando se conozca el ingreso real de IPCE",
        sid_resumen,
        domain_row_ini=27, domain_row_fin=28, domain_col=9,  # I
        series_col=10,  # J
    )
    _add_chart(service, donut_spec, sid_resumen, anchor_row=27, anchor_col=1, nombre="Resumen — dona (velocímetro) de mercado",
               titulos_existentes=titulos_existentes)


if __name__ == "__main__":
    main()
