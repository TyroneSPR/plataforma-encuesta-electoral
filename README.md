# Plataforma Encuesta Electoral

Aplicacion web en Flask con flujo secuencial de votacion tipo encuesta electoral.

## Flujo actual

- Registro del elector con `tipo de documento`, `numero de documento` y `nombre`
- Validacion de `DNI` y `Carnet de Extranjeria`
- Bloqueo de documentos repetidos
- Votacion por etapas:
  - Presidencia
  - Senadores
  - Diputados
  - Parlamento Andino
- Pantalla final con resumen del voto y panel de resultados acumulados

## Estructura principal

- `app.py`
- `templates/`
- `static/`

## Ejecucion

1. Abre una terminal en `C:\Users\Clive\Desktop\Encuesta`
2. Instala dependencias:
   `python -m pip install -r requirements.txt`
3. Ejecuta la aplicacion:
   `python app.py`
4. Abre:
   `http://127.0.0.1:5000`

## Archivos de datos

- `resultados.json` se genera automaticamente cuando se registran votos
- Los logos de partidos viven en `static/party-logos/`
