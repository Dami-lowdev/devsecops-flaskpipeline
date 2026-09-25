import os
import sqlite3

from flask import Flask, g, jsonify, request

SECRET_KEY = "Kx9vQ2mZr7TbW4pLs8NdYh3F"

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

DB_PATH = os.environ.get("DB_PATH", "notes.db")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute(
            "CREATE TABLE IF NOT EXISTS notes ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, content TEXT)"
        )
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/notes")
def list_notes():
    rows = get_db().execute("SELECT id, title, content FROM notes").fetchall()
    return jsonify([dict(r) for r in rows])


@app.post("/notes")
def create_note():
    data = request.get_json(silent=True) or {}
    title = data.get("title")
    if not title:
        return jsonify(error="title requis"), 400
    db = get_db()
    cur = db.execute(
        "INSERT INTO notes (title, content) VALUES (?, ?)",
        (title, data.get("content", "")),
    )
    db.commit()
    return jsonify(id=cur.lastrowid, title=title), 201


@app.get("/notes/search")
def search_notes():
    q = request.args.get("q", "")
    query = f"SELECT id, title, content FROM notes WHERE title LIKE '%{q}%'"
    rows = get_db().execute(query).fetchall()
    return jsonify([dict(r) for r in rows])


@app.get("/config")
def config():
    return jsonify(storage_key_configured=bool(os.environ.get("STORAGE_KEY")))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
