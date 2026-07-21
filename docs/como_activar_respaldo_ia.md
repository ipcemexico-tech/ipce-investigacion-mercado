# Cómo activar el respaldo por IA (Opción 1)

Este documento existe para que puedas activar el respaldo sin depender de
esta conversación ni de que alguien recuerde el contexto. Todo lo necesario
está aquí.

## Qué hace, exactamente

Cuando la API oficial de INEGI falla:

- **INPC**: el sistema lee el boletín mensual oficial de INEGI en PDF y
  extrae el dato de ahí. Es determinista (no usa IA) y **no genera costo**.
- **DENUE**: no existe un boletín público equivalente para el conteo de
  establecimientos por SCIAN, así que el sistema usa la API de Claude con
  búsqueda web para investigar el dato más reciente disponible. **Esto sí
  genera un costo real** (unos centavos de dólar por corrida, ya que solo
  se dispara cuando falla la API oficial — no en cada corrida).

En ambos casos, el resultado del respaldo se guarda en la Bitácora/Auto_Log
con la etiqueta `fuente=respaldo_investigacion_web`, nunca como si fuera un
dato verificado por la API oficial.

## Estado actual: apagado

Ahora mismo `RESPALDO_IA_ACTIVO` está en `"false"` en
`.github/workflows/actualizacion_ipce.yml`. Mientras esté así, el sistema
se comporta exactamente igual que si esta función no existiera — cero
costo, cero cambio de comportamiento.

## Paso a paso para activarlo

### 1. Consigue un API key de Anthropic (solo necesario para DENUE)

1. Entra a **console.anthropic.com** e inicia sesión (o crea una cuenta).
2. Ve a **Settings → API Keys** (o busca "API Keys" en el menú).
3. Clic en **"Create Key"**.
4. Ponle un nombre reconocible, por ejemplo `ipce-respaldo-denue`.
5. Copia el key (empieza con `sk-ant-...`). **Trátalo como una
   contraseña** — no lo compartas, no lo subas a ningún repo.
6. Asegúrate de tener saldo/facturación configurada en esa cuenta de
   Anthropic (Settings → Billing) — sin eso, las llamadas fallarán.

Si solo quieres el respaldo gratuito de INPC (boletín PDF) y no el de
DENUE, puedes saltarte este paso — ese respaldo no necesita ningún API key.

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
   RESPALDO_IA_ACTIVO: "false"
   ```
3. Cámbiala a:
   ```yaml
   RESPALDO_IA_ACTIVO: "true"
   ```
4. Guarda el cambio (puedes editarlo directo en la web de GitHub, con un
   commit, o pedirle a Claude Code que lo haga por ti — cualquiera de las
   dos formas funciona).

### 4. Pruébalo

En GitHub → pestaña **Actions** → **"Actualización IPCE (INPC / DENUE)"**
→ **"Run workflow"** → elige `inpc` o `denue` → **"Run workflow"**. Revisa
el log del paso "Consultar y guardar snapshot": si el respaldo se activó,
vas a ver una línea como `Usando dato de RESPALDO (no vía API): ...`.

## Cómo desactivarlo

Repite el paso 3 pero cambia `"true"` de vuelta a `"false"`. No hace falta
borrar el Secret de `ANTHROPIC_API_KEY` — con el interruptor en `false`,
nunca se usa y no genera costo.

## Nota sobre el costo de DENUE

El respaldo de DENUE solo se dispara cuando la API oficial de DENUE falla
(algo que, a la fecha de este documento, viene pasando siempre — ver el
reporte enviado a soporte de INEGI). Mientras esa API siga rota, cada
corrida trimestral programada del workflow gastaría una llamada a la API
de Claude. Si INEGI resuelve el problema de Cuantificar, el respaldo deja
de dispararse automáticamente (solo se usa cuando la fuente oficial
falla).
