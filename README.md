# IPCE — Investigación de Mercado (automatización)

Sistema de actualización automática del Dashboard_IPCE.xlsx / Informe_IPCE.docx,
según el Anexo técnico ("Especificación para automatización en Claude Code")
del Informe_IPCE.docx, carpeta de Drive "Investigación de Mercado IPCE".

## Estado

Ver `docs/tarea_programada_diseno.md` para el diseño de la tarea programada
(pendiente de decisión, nada activado todavía) y
`docs/bitacora_pendiente_2026-07-20.md` para hallazgos de la primera
corrida de diagnóstico que faltan por registrar en Drive.

## Estructura

- `ipce_market_research/clients/denue.py` — cliente DENUE (INEGI), método Cuantificar.
- `ipce_market_research/clients/inegi_indicadores.py` — cliente Banco de Indicadores (INEGI).
- `ipce_market_research/config.py` — carga de tokens desde variables de entorno.

## Configuración

Copia `.env.example` a `.env` (o define las variables en el entorno) con:

```
INEGI_INDICADORES_TOKEN=...
INEGI_DENUE_TOKEN=...
```

Los tokens nunca se escriben en el código ni se suben al repositorio
(Anexo técnico A.3).

## Uso manual

```bash
pip install -r requirements.txt
python3 -m ipce_market_research.clients.denue
python3 -m ipce_market_research.clients.inegi_indicadores
```
