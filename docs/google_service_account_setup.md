# Crear una cuenta de servicio de Google Cloud para escribir en el Dashboard

Objetivo: que GitHub Actions pueda escribir celdas directamente en el
Dashboard_IPCE (una vez convertido a Google Sheets nativo), usando una
identidad de máquina (cuenta de servicio) en vez de tu usuario personal.

No necesitas tarjeta de crédito ni activar facturación para esto — las
APIs que vamos a usar (Sheets, Drive) tienen cuota gratuita más que
suficiente para este uso.

## Paso 1 — Crear un proyecto en Google Cloud

1. Entra a https://console.cloud.google.com/ e inicia sesión con la misma
   cuenta de Google donde está el Drive de IPCE (ipcemexico@gmail.com).
2. Si es la primera vez, puede que te pida aceptar términos de servicio —
   acepta.
3. Arriba a la izquierda, junto al logo "Google Cloud", hay un menú
   desplegable (dice "Select a project" o el nombre de un proyecto
   existente). Haz clic ahí.
4. En la ventana que aparece, clic en **"NEW PROJECT"** (arriba a la
   derecha de esa ventana).
5. Llena:
   - **Project name**: `IPCE Investigacion Mercado`
   - **Organization**: déjalo como está (probablemente "No organization").
   - **Location**: déjalo como está.
6. Clic en **"CREATE"**.
7. Espera unos segundos (aparece una notificación de campana arriba a la
   derecha cuando termina). Luego abre otra vez el menú desplegable de
   proyectos (paso 3) y selecciona **"IPCE Investigacion Mercado"** para
   asegurarte de que quede activo.

## Paso 2 — Activar la API de Google Sheets

1. Con el proyecto ya seleccionado, usa la barra de búsqueda de arriba
   (el buscador con lupa, en la barra superior de la consola) y escribe
   `Google Sheets API`.
2. Haz clic en el resultado **"Google Sheets API"**.
3. Clic en el botón azul **"ENABLE"** (Habilitar).
4. Repite lo mismo buscando `Google Drive API` y haz clic en **"ENABLE"**
   también (la necesitamos para que la cuenta de servicio pueda ubicar el
   archivo).

## Paso 3 — Crear la cuenta de servicio

1. En la barra de búsqueda superior, escribe `Service Accounts` y entra
   al resultado **"Service Accounts"** (o menú ☰ de la izquierda →
   **"IAM & Admin"** → **"Service Accounts"**).
2. Clic en **"+ CREATE SERVICE ACCOUNT"** (arriba).
3. Paso "Service account details":
   - **Service account name**: `ipce-sheets-writer`
   - **Service account ID**: se llena solo, déjalo.
   - **Description**: `Escribe en el Dashboard IPCE desde GitHub Actions`
   - Clic en **"CREATE AND CONTINUE"**.
4. Paso "Grant this service account access to project" (roles): **no
   agregues ningún rol aquí** — el acceso se lo vamos a dar directamente
   sobre el archivo de Sheets en el Paso 5, no a nivel de todo el
   proyecto. Clic en **"CONTINUE"**.
5. Paso "Grant users access": déjalo vacío. Clic en **"DONE"**.

## Paso 4 — Generar la llave (credencial) de la cuenta de servicio

1. En la lista de "Service Accounts", haz clic sobre
   `ipce-sheets-writer@...` (el que acabas de crear).
2. Ve a la pestaña **"KEYS"** (arriba, junto a "DETAILS", "PERMISSIONS").
3. Clic en **"ADD KEY"** → **"Create new key"**.
4. Tipo de llave: deja seleccionado **"JSON"**.
5. Clic en **"CREATE"**.
6. Se descarga automáticamente un archivo `.json` a tu computadora (algo
   como `ipce-investigacion-mercado-xxxxx.json`). **Este archivo es como
   una contraseña** — no lo compartas, no lo subas a ningún repositorio,
   no me lo pegues a mí en el chat. Solo lo vamos a usar en el Paso 6.

## Paso 5 — Compartir el Dashboard (Google Sheet) con la cuenta de servicio

1. En la misma página de "DETAILS" de la cuenta de servicio, copia el
   correo que aparece arriba, algo como:
   `ipce-sheets-writer@ipce-investigacion-mercado-xxxxxx.iam.gserviceaccount.com`
2. Abre el Dashboard_IPCE en Google Drive (una vez que lo hayamos
   convertido a Google Sheets nativo — avísame si aún no y lo hago yo).
3. Clic en el botón **"Share"** / **"Compartir"** (arriba a la derecha).
4. Pega el correo de la cuenta de servicio en el campo "Add people".
5. Asegúrate de que el permiso diga **"Editor"**.
6. Destilda la casilla **"Notify people"** (es una cuenta de máquina, no
   una persona; no hace falta notificarle).
7. Clic en **"Share"** / **"Send"**.

## Paso 6 — Guardar la llave como Secret en GitHub

1. Abre el archivo `.json` que descargaste en el Paso 4 con un editor de
   texto (Bloc de notas, TextEdit, VSCode, lo que tengas). Selecciona y
   copia **todo** el contenido (es un bloque de texto que empieza con
   `{` y termina con `}`).
2. Ve al repositorio en GitHub → **Settings** → **Secrets and variables**
   → **Actions** → **New repository secret**.
3. **Name**: `GOOGLE_SERVICE_ACCOUNT_JSON`
4. **Value**: pega todo el contenido del archivo `.json`.
5. Clic en **"Add secret"**.
6. Por seguridad, borra el archivo `.json` de tu carpeta de Descargas una
   vez que lo hayas guardado como Secret (ya no lo necesitas ahí).

## Cuando termines

Dime "listo" y yo:
1. Convierto Dashboard_IPCE.xlsx a Google Sheets nativo (dejando el
   .xlsx original intacto como respaldo).
2. Agrego al workflow de GitHub Actions el paso que usa
   `GOOGLE_SERVICE_ACCOUNT_JSON` para escribir los valores nuevos
   directamente en las celdas correspondientes del Dashboard.
