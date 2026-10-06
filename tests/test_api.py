import pytest
from app import create_app


@pytest.fixture()
def app(tmp_path):
    return create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "test.db"),
        "UPLOAD_FOLDER": str(tmp_path / "uploads"),
        "SECRET_KEY": "test",
    })


@pytest.fixture()
def client(app):
    return app.test_client()


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json()["ok"] is True


def test_seeded_workspace(client):
    bootstrap = client.get("/api/bootstrap").get_json()
    assert len(bootstrap["companies"]) >= 3
    assert bootstrap["selected_analysis_id"] is not None


def test_analysis_detail_and_simulation(client):
    bootstrap = client.get("/api/bootstrap").get_json()
    aid = bootstrap["selected_analysis_id"]
    detail = client.get(f"/api/analyses/{aid}")
    assert detail.status_code == 200
    assert len(detail.get_json()["monthly"]) == 12

    sim = client.post("/api/simulate", json={"analysis_id": aid})
    assert sim.status_code == 200
    body = sim.get_json()
    assert len(body["scenarios"]) == 3
    assert body["simulation_id"] >= 1
