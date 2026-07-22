# Respaldo cuando falla la API oficial de INEGI

Este documento existe para no depender de esta conversación ni de que
alguien recuerde el contexto. Todo lo necesario está aquí.

Hay DOS respaldos independientes, con DOS interruptores independientes —
uno gratis y activo por defecto, otro pagado y apagado por defecto.

## Qué hace cada uno

- **INPC** (`RESPALDO_INPC_ACTIVO`): el sistema lee el boletín mensual
  oficial de INEGI en PDF y extrae el dato de ahí. Es determinista (no
  usa IA), **no genera costo**, y por eso está **activo por defecto**.
- **DENUE** (`RESPALDO_DENUE_IA_ACTIVO`): no existe un boletín público
  equivalente para el conteo de establecimientos por SCIAN, así que el
  sistema usa la API de Claude con búsqueda web para investigar el dato
  más reciente disponible. **Esto sí genera un costo real** (unos
  centavos de dólar por corrida, ya que solo se dispara cuando falla la
  API oficial). Por eso está **apagado por defecto**.

En ambos casos, el resultado del respaldo se guarda en la
Bitácora/Auto_Log (y, si `ACTUALIZAR_CELDAS_DASHBOARD` está activo,
también en la celda visible correspondiente) con la etiqueta
`fuente=respaldo_investigacion_web` — nunca como si fuera un dato
verificado por la API oficial.

## Estado actual

En `.github/workflows/actualizacion_ipce.yml`:

```yaml
RESPALDO_INPC_ACTIVO: "true"      # gratis — activo
RESPALDO_DENUE_IA_ACTIVO: "false" # pagado — apagado
```

El respaldo de INPC ya funciona sin que tengas que hacer nada más. Lo
que sigue es solo para activar el de DENUE cuando quieras.

## Paso a paso para activar el respaldo de DENUE (pagado)

### 1. Consigue un API key de Anthropic

1. Entra a **console.anthropic.com** e inicia sesión (o crea una cuenta).
2. Ve a **Settings → API Keys** (o busca "API Keys" en el menú).
3. Clic en **"Create Key"**.
4. Ponle un nombre reconocible, por ejemplo `ipce-respaldo-denue`.
5. Copia el key (empieza con `sk-ant-...`). **Trátalo como una
   contraseña** — no lo compartas, no lo subas a ningún repo.
6. Asegúrate de tener saldo/facturación configurada en esa cuenta de
   Anthropic (Settings → Billing) — sin eso, las llamadas fallarán.

### 2. Guarda el key como Secret en GitHub

1. Repo en GitHub → **Settings → Secrets and variables → Actions → New
   repository secret**.
2. **Name**: `ANTHROPIC_API_KEY`
3. **Value**: pega el key que copiaste.
4. Clic en **"Add secret"**.

### 3. Activa el interruptor

1. En GitHub, abre `.github/workflows/actualizacion_ipce.yml`.
2. Busca la línea:
   ```yaml
   RESPALDO_DENUE_IA_ACTIVO: "false"
   ```
3. Cámbiala a:
   ```yaml
   RESPALDO_DENUE_IA_ACTIVO: "true"
   ```
4. Guarda el cambio (puedes editarlo directo en la web de GitHub, con un
   commit, o pedirle a Claude Code que lo haga por ti — cualquiera de las
   dos formas funciona).

### 4. Pruébalo

En GitHub → pestaña **Actions** → **"Actualización IPCE (INPC / DENUE)"**
→ **"Run workflow"** → **revisa que el campo "Qué consultar manualmente"
diga `denue`** (el diálogo de GitHub siempre vuelve al valor por
defecto cada vez que lo abres, no recuerda la corrida anterior) →
**"Run workflow"**. Revisa el log del paso "Consultar y guardar
snapshot": si el respaldo se activó, vas a ver una línea como `Usando
dato de RESPALDO (no oficial): ...`.

## Cómo desactivar el respaldo de DENUE

Repite el paso 3 pero cambia `"true"` de vuelta a `"false"`. No hace
falta borrar el Secret de `ANTHROPIC_API_KEY` — con el interruptor en
`false`, nunca se usa y no genera costo.

## Cómo desactivar también el respaldo de INPC (si algún día lo quieres apagar)

Cambia `RESPALDO_INPC_ACTIVO: "true"` a `"false"` en el mismo archivo.
No hay ninguna razón de costo para hacerlo — es gratis — pero la opción
existe por si algún día quieres que el sistema solo reporte el error sin
intentar el boletín.

## Nota sobre el costo de DENUE

El respaldo de DENUE solo se dispara cuando la API oficial de DENUE falla
(algo que, a la fecha de este documento, viene pasando siempre — ver el
reporte enviado a soporte de INEGI). Mientras esa API siga rota, cada
corrida trimestral programada del workflow gastaría una llamada a la API
de Claude si `RESPALDO_DENUE_IA_ACTIVO` está en `"true"`. Si INEGI
resuelve el problema de Cuantificar, el respaldo deja de dispararse
automáticamente (solo se usa cuando la fuente oficial falla).
