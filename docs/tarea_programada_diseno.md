# Diseño de la tarea programada (Anexo A.5) — borrador, nada activado

Estado: **propuesta para revisar mañana con el usuario**. No se ha creado
ningún cron ni trigger. Nada de esto corre solo todavía.

## Cadencia pedida (Anexo A.5)

| Dato | Frecuencia |
| --- | --- |
| INPC / inflación | Mensual |
| DENUE (competidores) | Trimestral |
| ISO Survey, ENAPROCE, ENIGH, Censos Económicos | Anual / cuando se publique nueva edición |
| Archivos subidos por el usuario (00_Fuentes_Subidas/) | Cada corrida programada |

## Hallazgo importante (2026-07-20): `CronCreate` no sirve para esta cadencia

La herramienta de cron disponible en este entorno de Claude Code
(`CronCreate`) tiene dos límites que la descartan para A.5 tal cual:

1. **Las tareas viven solo en memoria de la sesión actual.** Si esta
   sesión termina (inactividad, cierre), la tarea programada desaparece
   con ella. No queda nada persistente en disco.
2. **Expiración automática a los 7 días**, incluso si la sesión siguiera
   viva. Una cadencia "trimestral" o incluso "mensual" no puede sostenerse
   con este mecanismo.

Anoche, al preguntar, planteé "sesión programada de Claude Code" como la
opción recomendada por su capacidad de razonar sobre archivos ambiguos
(Anexo A.4). Sigue siendo cierto que razona mejor, pero **no es duradera**
— hay que decidir mañana entre:

- **Opción A — GitHub Actions con cron real (duradero).** Corre
  independiente de cualquier sesión de Claude Code. Puede ejecutar los
  clientes de `ipce_market_research/clients/` para INPC y DENUE sin
  problema. Limitación: es código determinista, no puede "leer y decidir"
  sobre archivos ambiguos subidos por el usuario (A.4) de forma tan
  flexible como un agente. Requiere que el usuario cree los Secrets del
  repo (`INEGI_INDICADORES_TOKEN`, `INEGI_DENUE_TOKEN`) manualmente en
  GitHub — no tengo permiso para crearlos yo.
- **Opción B — Recrear la tarea de Claude Code cada 7 días.** Alguien
  (el usuario, o un recordatorio) tendría que volver a invocar `CronCreate`
  semana a semana para mantenerla viva. Poco realista para una cadencia
  mensual/trimestral desatendida.
- **Opción C — Híbrido.** GitHub Actions dispara la actualización de datos
  duros (INPC, DENUE) de forma duradera; la parte de razonamiento sobre
  archivos subidos por el usuario (A.4) se revisa en sesiones puntuales de
  Claude Code, no de forma continua/desatendida.

**Recomendación para discutir mañana:** Opción A o C. La automatización
100% desatendida y duradera necesita algo fuera de una sesión de Claude
Code (GitHub Actions u otro programador externo).

## Otra brecha encontrada: no hay forma de actualizar archivos existentes en Drive

Las herramientas de Google Drive disponibles (`create_file`, `copy_file`,
`read_file_content`, `download_file_content`, `search_files`,
`get_file_metadata`, `get_file_permissions`, `list_recent_files`) **no
incluyen actualizar el contenido de un archivo existente ni eliminarlo**.
Esto afecta directamente al Anexo A.4 (actualizar Dashboard/Informe/
Bitácora) y A.2 (mover archivos a la carpeta correcta): con este set de
herramientas, cualquier "actualización" terminaría creando un archivo
duplicado en vez de modificar el original.

Opciones a decidir mañana:

- Dar acceso a la API de Google Drive/Sheets con permisos de escritura
  completos (más allá del conector actual), por ejemplo vía una cuenta de
  servicio para el workflow de GitHub Actions.
- Que el agente prepare los cambios (texto/filas nuevas) y el usuario los
  pegue manualmente en el Dashboard/Bitácora/Informe.
- Buscar si existe otro conector de Drive con permisos de edición en
  sitio.

## Qué sí quedó listo esta noche (sin activar nada)

- `ipce_market_research/clients/denue.py` y `inegi_indicadores.py`:
  clientes que leen los tokens solo desde variables de entorno.
- Diagnóstico en vivo documentado en los propios módulos (ver comentarios
  de cabecera) sobre el estado real de ambas APIs a 2026-07-20.
