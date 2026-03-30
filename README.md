# Encuesta Electoral En Vivo

Aplicacion web local hecha con Flask para registrar participantes por nombre y correo, recibir un voto por persona y mostrar resultados en vivo mientras la encuesta sigue abierta.

La estructura principal ahora esta plana en la raiz del proyecto:

- `index.html`
- `dashboard.html`
- `styles.css`
- `app.js`
- `dashboard.js`
- `app.py`

## Que incluye

- Registro simple con `nombre + correo`
- Un voto por correo para cada cargo
- Resultados y porcentajes en vivo
- Dashboard separado para proyectar o monitorear
- Persistencia local en `SQLite`

## Como ejecutarlo

1. Abre una terminal en `C:\Users\Clive\Desktop\Encuesta`
2. Si hace falta, instala dependencias con `python -m pip install -r requirements.txt`
3. Ejecuta `python app.py`
4. Abre `http://127.0.0.1:5000`
5. Si quieres el tablero aparte, abre `http://127.0.0.1:5000/dashboard`

## Donde editar las opciones

Los cargos y candidatos estan en:

- `C:\Users\Clive\Desktop\Encuesta\election_data.json`

Ahora mismo deje listas de ejemplo para:

- Presidencia
- Senadores nacionales
- Senadores regionales
- Diputados
- Parlamento Andino

Si quieres, en el siguiente paso puedo reemplazar esas listas por los nombres reales de tu papeleta.

## Nota sobre el PDF

Revise el archivo `CEDULA DE VOTACION 2026  41X64.pdf` y el texto extraible solo confirma encabezados como:

- A nivel nacional
- A nivel regional
- Diputados a nivel regional
- Parlamento Andino

No aparecieron nombres de candidatos o listas en el texto del PDF, por eso las opciones del JSON quedaron como plantillas editables.
