import json
import queue
import sqlite3
import threading
import uuid
from contextlib import closing
from datetime import datetime
from pathlib import Path

from flask import Flask, Response, g, jsonify, render_template, request, send_from_directory, session


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "survey.db"
CONFIG_PATH = BASE_DIR / "election_data.json"
SECRET_KEY = "encuesta-abril-2026-cambia-esta-clave"


app = Flask(__name__, template_folder=str(BASE_DIR))
app.config["SECRET_KEY"] = SECRET_KEY
app.config["JSON_AS_ASCII"] = False


class LiveBroadcaster:
    def __init__(self):
        self._listeners = set()
        self._lock = threading.Lock()

    def subscribe(self):
        listener = queue.Queue()
        with self._lock:
            self._listeners.add(listener)
        return listener

    def unsubscribe(self, listener):
        with self._lock:
            self._listeners.discard(listener)

    def publish(self, payload):
        with self._lock:
            listeners = list(self._listeners)
        for listener in listeners:
            listener.put(payload)


broadcaster = LiveBroadcaster()


def load_config():
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with closing(sqlite3.connect(DB_PATH)) as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS voters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                voter_id INTEGER NOT NULL,
                office_id TEXT NOT NULL,
                candidate_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(voter_id, office_id),
                FOREIGN KEY(voter_id) REFERENCES voters(id)
            );
            """
        )
        db.commit()


def ensure_demo_data():
    init_db()


def current_voter():
    voter_id = session.get("voter_id")
    if not voter_id:
        return None
    row = get_db().execute(
        "SELECT id, name, email, created_at FROM voters WHERE id = ?", (voter_id,)
    ).fetchone()
    return dict(row) if row else None


def get_vote_status(voter_id):
    rows = get_db().execute(
        "SELECT office_id, candidate_id FROM votes WHERE voter_id = ?", (voter_id,)
    ).fetchall()
    return {row["office_id"]: row["candidate_id"] for row in rows}


def build_results():
    config = load_config()
    db = get_db()
    total_voters = db.execute("SELECT COUNT(*) FROM voters").fetchone()[0]
    total_votes = db.execute("SELECT COUNT(*) FROM votes").fetchone()[0]

    offices = []
    for office in config["offices"]:
        counts = {
            row["candidate_id"]: row["total"]
            for row in db.execute(
                """
                SELECT candidate_id, COUNT(*) AS total
                FROM votes
                WHERE office_id = ?
                GROUP BY candidate_id
                """,
                (office["id"],),
            ).fetchall()
        }
        office_total = sum(counts.values())
        candidates = []
        for candidate in office["candidates"]:
            votes = counts.get(candidate["id"], 0)
            pct = round((votes / office_total * 100), 2) if office_total else 0
            candidates.append(
                {
                    "id": candidate["id"],
                    "name": candidate["name"],
                    "party": candidate.get("party", ""),
                    "list_name": candidate.get("list_name", candidate.get("party", "")),
                    "short_name": candidate.get("short_name", candidate["name"]),
                    "badge": candidate.get("badge", ""),
                    "color": candidate.get("color", "#274c77"),
                    "votes": votes,
                    "percentage": pct,
                }
            )
        offices.append(
            {
                "id": office["id"],
                "title": office["title"],
                "description": office.get("description", ""),
                "total_votes": office_total,
                "candidates": sorted(
                    candidates, key=lambda item: (-item["votes"], item["name"])
                ),
            }
        )

    return {
        "title": config["title"],
        "subtitle": config["subtitle"],
        "election_date": config["election_date"],
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "summary": {
            "registered_voters": total_voters,
            "total_votes_cast": total_votes,
            "offices_count": len(offices),
        },
        "offices": offices,
    }


def build_bootstrap():
    config = load_config()
    voter = current_voter()
    selections = get_vote_status(voter["id"]) if voter else {}
    return {
        "config": config,
        "results": build_results(),
        "voter": voter,
        "selections": selections,
    }


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.get("/styles.css")
def styles():
    return send_from_directory(BASE_DIR, "styles.css", mimetype="text/css")


@app.get("/app.js")
def app_script():
    return send_from_directory(BASE_DIR, "app.js", mimetype="application/javascript")


@app.get("/dashboard.js")
def dashboard_script():
    return send_from_directory(BASE_DIR, "dashboard.js", mimetype="application/javascript")


@app.get("/api/bootstrap")
def bootstrap():
    return jsonify(build_bootstrap())


@app.post("/api/register")
def register():
    payload = request.get_json(force=True)
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip().lower()

    if not name or not email or "@" not in email:
        return jsonify({"error": "Ingresa un nombre y un correo valido."}), 400

    db = get_db()
    existing = db.execute(
        "SELECT id, name, email, created_at FROM voters WHERE email = ?", (email,)
    ).fetchone()

    if existing:
        voter_id = existing["id"]
        if existing["name"] != name:
            db.execute("UPDATE voters SET name = ? WHERE id = ?", (name, voter_id))
            db.commit()
        voter = dict(
            db.execute(
                "SELECT id, name, email, created_at FROM voters WHERE id = ?", (voter_id,)
            ).fetchone()
        )
    else:
        db.execute(
            "INSERT INTO voters (name, email, created_at) VALUES (?, ?, ?)",
            (name, email, datetime.utcnow().isoformat() + "Z"),
        )
        db.commit()
        voter_id = db.execute("SELECT id FROM voters WHERE email = ?", (email,)).fetchone()[0]
        voter = dict(
            db.execute(
                "SELECT id, name, email, created_at FROM voters WHERE id = ?", (voter_id,)
            ).fetchone()
        )

    session["voter_id"] = voter["id"]
    return jsonify({"voter": voter, "selections": get_vote_status(voter["id"])})


@app.post("/api/vote")
def cast_vote():
    voter = current_voter()
    if not voter:
        return jsonify({"error": "Debes registrarte antes de votar."}), 401

    payload = request.get_json(force=True)
    selections = payload.get("selections") or {}
    config = load_config()
    valid_offices = {office["id"]: office for office in config["offices"]}

    if set(selections.keys()) != set(valid_offices.keys()):
        return jsonify({"error": "Debes elegir una opcion para cada cargo."}), 400

    for office_id, candidate_id in selections.items():
        valid_candidates = {candidate["id"] for candidate in valid_offices[office_id]["candidates"]}
        if candidate_id not in valid_candidates:
            return jsonify({"error": "Se detecto una opcion invalida."}), 400

    db = get_db()
    existing = get_vote_status(voter["id"])
    if existing:
        return jsonify({"error": "Este correo ya registro sus votos."}), 409

    timestamp = datetime.utcnow().isoformat() + "Z"
    for office_id, candidate_id in selections.items():
        db.execute(
            """
            INSERT INTO votes (voter_id, office_id, candidate_id, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (voter["id"], office_id, candidate_id, timestamp),
        )
    db.commit()

    payload = build_results()
    broadcaster.publish(payload)
    return jsonify({"ok": True, "results": payload})


@app.get("/api/results")
def results():
    return jsonify(build_results())


@app.get("/api/stream")
def stream():
    listener = broadcaster.subscribe()

    def event_stream():
        initial = build_results()
        yield f"event: snapshot\ndata: {json.dumps(initial, ensure_ascii=False)}\n\n"
        try:
            while True:
                try:
                    payload = listener.get(timeout=30)
                    yield f"event: snapshot\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
                except queue.Empty:
                    heartbeat = {"id": str(uuid.uuid4())}
                    yield f"event: heartbeat\ndata: {json.dumps(heartbeat)}\n\n"
        finally:
            broadcaster.unsubscribe(listener)

    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    }
    return Response(event_stream(), mimetype="text/event-stream", headers=headers)


ensure_demo_data()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000, threaded=True)
