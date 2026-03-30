import json
import re
from pathlib import Path

from flask import Flask, redirect, render_template, request, session, url_for

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "resultados.json"

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)
app.secret_key = "clave-segura-encuesta"

PARTIDOS = [
    {"id": 1, "nombre": "Alianza Electoral Venceremos", "sigla": "AEV"},
    {"id": 2, "nombre": "Partido Patriotico del Peru", "sigla": "PPP"},
    {"id": 3, "nombre": "Partido Civico Obras", "sigla": "PCO"},
    {"id": 4, "nombre": "Partido Democrata Verde", "sigla": "PDV"},
    {"id": 5, "nombre": "Partido del Buen Gobierno", "sigla": "PBG"},
    {"id": 6, "nombre": "Partido Politico Peru Accion", "sigla": "PPA"},
    {"id": 7, "nombre": "Partido Politico PRIN", "sigla": "PRIN"},
    {"id": 8, "nombre": "Partido Politico Progresemos", "sigla": "PRO"},
    {"id": 9, "nombre": "Partido Si Creo", "sigla": "SC"},
    {"id": 10, "nombre": "Pais para Todos", "sigla": "PPT"},
    {"id": 11, "nombre": "Frente de la Esperanza", "sigla": "FDE"},
    {"id": 12, "nombre": "Partido Politico Peru Libre", "sigla": "PPL"},
    {"id": 13, "nombre": "Primero la Gente", "sigla": "PLG"},
    {"id": 14, "nombre": "Juntos por el Peru", "sigla": "JPP"},
    {"id": 15, "nombre": "Podemos Peru", "sigla": "PP"},
    {"id": 16, "nombre": "Partido Democrata Federal", "sigla": "PDF"},
    {"id": 17, "nombre": "Fe en el Peru", "sigla": "FEP"},
    {"id": 18, "nombre": "Integridad Democratica", "sigla": "ID"},
    {"id": 19, "nombre": "Fuerza Popular", "sigla": "FP"},
    {"id": 20, "nombre": "Alianza para el Progreso", "sigla": "APP"},
    {"id": 21, "nombre": "Cooperacion Popular", "sigla": "CP"},
    {"id": 22, "nombre": "Ahora Nacion", "sigla": "AN"},
    {"id": 23, "nombre": "Libertad Popular", "sigla": "LP"},
    {"id": 24, "nombre": "Un Camino Diferente", "sigla": "UCD"},
    {"id": 25, "nombre": "Avanza Pais", "sigla": "AP"},
    {"id": 26, "nombre": "Peru Moderno", "sigla": "PM"},
    {"id": 27, "nombre": "Peru Primero", "sigla": "PP1"},
    {"id": 28, "nombre": "Salvemos al Peru", "sigla": "SAP"},
    {"id": 29, "nombre": "Somos Peru", "sigla": "SP"},
    {"id": 30, "nombre": "Partido Aprista Peruano", "sigla": "PAP"},
    {"id": 31, "nombre": "Renovacion Popular", "sigla": "RP"},
    {"id": 32, "nombre": "Partido Democrata Unido Peru", "sigla": "PDUP"},
    {"id": 33, "nombre": "Fuerza y Libertad", "sigla": "FYL"},
    {"id": 34, "nombre": "Trabajadores y Emprendedores", "sigla": "PTE"},
    {"id": 35, "nombre": "Unidad Nacional", "sigla": "UN"},
    {"id": 36, "nombre": "Partido Morado", "sigla": "PMD"},
]

ETAPAS = [
    {
        "slug": "presidente",
        "titulo": "Presidencia de la Republica",
        "descripcion": "Seleccione la organizacion politica de su preferencia para la formula presidencial.",
        "siguiente": "senadores",
        "boton": "Continuar a Senadores",
        "campo": "voto_presidente",
        "numero": 2,
    },
    {
        "slug": "senadores",
        "titulo": "Camara de Senadores",
        "descripcion": "Emita su voto para la representacion senatorial de alcance nacional.",
        "siguiente": "diputados",
        "boton": "Continuar a Diputados",
        "campo": "voto_senadores",
        "numero": 3,
    },
    {
        "slug": "diputados",
        "titulo": "Camara de Diputados",
        "descripcion": "Registre su preferencia para la representacion parlamentaria correspondiente.",
        "siguiente": "parlamento",
        "boton": "Continuar al Parlamento Andino",
        "campo": "voto_diputados",
        "numero": 4,
    },
    {
        "slug": "parlamento",
        "titulo": "Parlamento Andino",
        "descripcion": "Finalice la encuesta electoral con la seleccion para el Parlamento Andino.",
        "siguiente": "gracias",
        "boton": "Registrar voto",
        "campo": "voto_parlamento",
        "numero": 5,
    },
]

CARGOS = [
    ("voto_presidente", "Presidencia"),
    ("voto_senadores", "Senadores"),
    ("voto_diputados", "Diputados"),
    ("voto_parlamento", "Parlamento Andino"),
]


def leer_resultados():
    if not DATA_FILE.exists():
        return {"votantes": []}
    with DATA_FILE.open("r", encoding="utf-8") as archivo:
        return json.load(archivo)


def guardar_resultados(data):
    with DATA_FILE.open("w", encoding="utf-8") as archivo:
        json.dump(data, archivo, ensure_ascii=False, indent=2)


def documento_ya_registrado(tipo_documento, documento):
    data = leer_resultados()
    for votante in data.get("votantes", []):
        mismo_documento = votante.get("documento") == documento
        mismo_tipo = votante.get("tipo_documento") == tipo_documento
        if mismo_documento and (mismo_tipo or not votante.get("tipo_documento")):
            return True
    return False


def obtener_etapa(slug):
    for etapa in ETAPAS:
        if etapa["slug"] == slug:
            return etapa
    return None


def nombre_partido(partido_id):
    for partido in PARTIDOS:
        if str(partido["id"]) == str(partido_id):
            return partido["nombre"]
    return "No registrado"


def requiere_registro():
    return "votante" not in session


def registrar_voto():
    if session.get("voto_registrado"):
        return

    data = leer_resultados()
    votantes = data.get("votantes", [])
    documento = session["votante"]["documento"]

    registro = {
        "tipo_documento": session["votante"]["tipo_documento"],
        "documento": documento,
        "nombre": session["votante"]["nombre"],
        "voto_presidente": session.get("voto_presidente"),
        "voto_senadores": session.get("voto_senadores"),
        "voto_diputados": session.get("voto_diputados"),
        "voto_parlamento": session.get("voto_parlamento"),
    }

    actualizado = False
    for indice, votante in enumerate(votantes):
        if (
            votante.get("documento") == documento
            and votante.get("tipo_documento") == session["votante"]["tipo_documento"]
        ):
            votantes[indice] = registro
            actualizado = True
            break

    if not actualizado:
        votantes.append(registro)

    data["votantes"] = votantes
    guardar_resultados(data)
    session["voto_registrado"] = True


def construir_panel_resultados():
    data = leer_resultados()
    votantes = data.get("votantes", [])
    total_votantes = len(votantes)
    panel = []

    for campo, titulo in CARGOS:
        conteo = {}
        for votante in votantes:
            partido_id = votante.get(campo)
            if partido_id:
                clave = str(partido_id)
                conteo[clave] = conteo.get(clave, 0) + 1

        filas = []
        for partido in PARTIDOS:
            votos = conteo.get(str(partido["id"]), 0)
            porcentaje = round((votos / total_votantes) * 100, 2) if total_votantes else 0
            filas.append(
                {
                    "id": partido["id"],
                    "sigla": partido["sigla"],
                    "nombre": partido["nombre"],
                    "votos": votos,
                    "porcentaje": porcentaje,
                }
            )

        filas.sort(key=lambda item: (-item["votos"], item["nombre"]))
        lider = filas[0] if filas and filas[0]["votos"] > 0 else None
        panel.append(
            {
                "titulo": titulo,
                "lider": lider,
                "resultados": [fila for fila in filas if fila["votos"] > 0][:10],
            }
        )

    return {"total_votantes": total_votantes, "panel": panel}


@app.route("/", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        tipo_documento = request.form.get("tipo_documento", "").strip()
        documento = request.form.get("documento", "").strip().upper()
        nombre = request.form.get("nombre", "").strip()

        if not tipo_documento or not documento or not nombre:
            return render_template(
                "registro.html",
                error="Seleccione un tipo de documento, ingrese el numero correspondiente y escriba su nombre.",
                progreso=1,
            )

        if tipo_documento == "dni":
            if not re.fullmatch(r"\d{8}", documento):
                return render_template(
                    "registro.html",
                    error="El DNI debe contener exactamente 8 digitos numericos.",
                    progreso=1,
                )
        elif tipo_documento == "ce":
            if not re.fullmatch(r"\d{9}", documento):
                return render_template(
                    "registro.html",
                    error="El Carnet de Extranjeria debe contener exactamente 9 digitos numericos.",
                    progreso=1,
                )
        else:
            return render_template(
                "registro.html",
                error="Seleccione un tipo de documento valido.",
                progreso=1,
            )

        if documento_ya_registrado(tipo_documento, documento):
            return render_template(
                "registro.html",
                error="Este documento ya fue utilizado en una votacion registrada.",
                progreso=1,
            )

        session.clear()
        session["votante"] = {
            "tipo_documento": tipo_documento,
            "documento": documento,
            "nombre": nombre,
        }
        session["voto_registrado"] = False
        return redirect(url_for("votacion", etapa_slug="presidente"))

    return render_template("registro.html", error=None, progreso=1)


@app.route("/<etapa_slug>", methods=["GET", "POST"])
def votacion(etapa_slug):
    etapa = obtener_etapa(etapa_slug)
    if etapa is None:
        return redirect(url_for("registro"))

    if requiere_registro():
        return redirect(url_for("registro"))

    if request.method == "POST":
        opcion = request.form.get("partido")
        if not opcion:
            return render_template(
                "votacion.html",
                etapa=etapa,
                partidos=PARTIDOS,
                progreso=etapa["numero"],
                error="Seleccione una organizacion politica para continuar.",
                votante=session["votante"],
            )

        session[etapa["campo"]] = opcion
        if etapa["siguiente"] == "gracias":
            return redirect(url_for("gracias"))
        return redirect(url_for("votacion", etapa_slug=etapa["siguiente"]))

    return render_template(
        "votacion.html",
        etapa=etapa,
        partidos=PARTIDOS,
        progreso=etapa["numero"],
        error=None,
        votante=session["votante"],
    )


@app.route("/gracias")
def gracias():
    if requiere_registro():
        return redirect(url_for("registro"))

    registrar_voto()
    panel_resultados = construir_panel_resultados()

    resumen = {
        "Presidencia": nombre_partido(session.get("voto_presidente")),
        "Senadores": nombre_partido(session.get("voto_senadores")),
        "Diputados": nombre_partido(session.get("voto_diputados")),
        "Parlamento Andino": nombre_partido(session.get("voto_parlamento")),
    }
    return render_template(
        "gracias.html",
        progreso=5,
        votante=session["votante"],
        resumen=resumen,
        panel_resultados=panel_resultados,
    )


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
