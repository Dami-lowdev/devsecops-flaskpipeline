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
