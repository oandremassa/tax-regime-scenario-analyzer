import tempfile
from app import create_app


def make_client():
    temp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    app = create_app({"TESTING": True, "DATABASE_PATH": temp.name})
    return app.test_client()


def test_health_endpoint():
    client = make_client()
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json()["ok"] is True


def test_companies_are_seeded():
    client = make_client()
    response = client.get("/api/companies")
    data = response.get_json()
    assert response.status_code == 200
    assert len(data) == 4


def test_create_analysis_and_simulate():
    client = make_client()
    payload = {
        "company_id": 1,
        "reference_year": 2027,
        "annual_revenue": 2100000,
        "payroll": 350000,
        "operating_costs": 620000,
        "service_share": 90,
        "commerce_share": 10,
    }
    analysis = client.post("/api/analyses", json=payload)
    assert analysis.status_code == 201
    analysis_id = analysis.get_json()["id"]

    simulation = client.post("/api/simulate", json={"company_id": 1, "analysis_id": analysis_id})
    assert simulation.status_code == 200
    assert len(simulation.get_json()["scenarios"]) == 3
