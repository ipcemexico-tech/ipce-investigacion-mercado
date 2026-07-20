# Filas pendientes para Bitacora_Cambios.xlsx (2026-07-20)

No pude escribirlas directamente en el archivo de Drive porque no hay
herramienta de "actualizar archivo existente" (ver
`docs/tarea_programada_diseno.md`). Pégalas tú, o dime cuando tengamos
forma de escribir en Drive y lo hago yo.

| Fecha | Fuente / Archivo | Tipo de fuente | Sección actualizada | Huella (hash) | Tipo de cambio | Resumen | Valor anterior | Valor nuevo | Notas |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-07-20 | INEGI DENUE — método Cuantificar | API oficial | 3.3 Competidores — DENUE (Informe) / hoja Sector_Competencia (Dashboard) | N/A | Conflicto | El método Cuantificar de DENUE devuelve una respuesta HTTP malformada ("HTTP/1.1 000", cuerpo prometido pero no entregado) en todo el clúster de INEGI, verificado con 3 reintentos espaciados en dos nodos de backend distintos (pro36, pro37) y con token real e inválido (mismo resultado). No es un problema de red ni de este sistema. | Estimación 6,800–7,500 (extrapolación, sin cambios) | Sin cambio — sigue como estimación, NO se reemplaza por una cifra inventada | Reintentar en próxima corrida. Método alternativo `Buscar` probado sin éxito (ver notas técnicas en `denue.py`). |
| 2026-07-20 | INEGI Banco de Indicadores | API oficial | 2. Panorama macroeconómico (Informe) / hoja Macro (Dashboard) | N/A | Conflicto | La API respondió correctamente (JSON bien formado) pero con "ErrorCode:100 — No se encontraron resultados" para todas las combinaciones de indicador/área/fuente probadas, incluido el indicador de demostración oficial de INEGI. No se pudo confirmar si la causa es el ID de indicador, el código de área, o el token. | Valores actuales del informe (INPC 3.37%, sin cambios) | Sin cambio | Pendiente validar indicador_id correcto para INPC con el usuario o la documentación de su cuenta INEGI. |
