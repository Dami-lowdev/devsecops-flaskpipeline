import pytest

import app as app_module


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(app_module, "DB_PATH", str(tmp_path / "test.db"))
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_create_and_list_notes(client):
    r = client.post("/notes", json={"title": "Première note", "content": "Bonjour"})
    assert r.status_code == 201
    notes = client.get("/notes").get_json()
    assert len(notes) == 1
    assert notes[0]["title"] == "Première note"


def test_create_note_requires_title(client):
    r = client.post("/notes", json={"content": "sans titre"})
    assert r.status_code == 400


def test_search_notes(client):
    client.post("/notes", json={"title": "kubernetes"})
    client.post("/notes", json={"title": "docker"})
    results = client.get("/notes/search?q=dock").get_json()
    assert [n["title"] for n in results] == ["docker"]


def test_search_is_not_injectable(client):
    client.post("/notes", json={"title": "publique"})
    client.post("/notes", json={"title": "secret", "content": "note privée"})
    results = client.get("/notes/search?q=' OR 1=1--").get_json()
    assert results == []


def test_config_reads_storage_key_from_file(client, tmp_path, monkeypatch):
    secret_file = tmp_path / "storage_key"
    secret_file.write_text("valeur-vault\n")
    monkeypatch.delenv("STORAGE_KEY", raising=False)
    monkeypatch.setenv("STORAGE_KEY_FILE", str(secret_file))
    r = client.get("/config")
    assert r.get_json() == {"storage_key_configured": True}
    assert "valeur-vault" not in r.get_data(as_text=True)


def test_config_without_secret(client, monkeypatch):
    monkeypatch.delenv("STORAGE_KEY", raising=False)
    monkeypatch.delenv("STORAGE_KEY_FILE", raising=False)
    assert client.get("/config").get_json() == {"storage_key_configured": False}


def test_security_headers(client):
    r = client.get("/health")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["Content-Security-Policy"] == "default-src 'none'; frame-ancestors 'none'"
    assert r.headers["Cross-Origin-Resource-Policy"] == "same-origin"
    assert r.headers["Cache-Control"] == "no-store"


def test_errors_are_json(client):
    r = client.get("/inexistant")
    assert r.status_code == 404
    assert r.is_json
    assert r.get_json() == {"error": "Not Found"}
    r = client.delete("/health")
    assert r.status_code == 405
    assert r.is_json
