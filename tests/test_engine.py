from app.engine import calculate


def test_engine_returns_three_scenarios():
    result = calculate({
        "annual_revenue": 2_000_000,
        "payroll": 400_000,
        "operating_costs": 600_000,
        "service_share": 80,
        "commerce_share": 20,
    })
    assert len(result["scenarios"]) == 3
    assert result["recommended_scenario"] in {"Simplified Regime", "Presumed Profit", "Actual Profit"}
    assert result["scenarios"][0]["estimated_tax"] <= result["scenarios"][-1]["estimated_tax"]


def test_engine_flags_invalid_revenue_mix():
    result = calculate({
        "annual_revenue": 1_000_000,
        "payroll": 200_000,
        "operating_costs": 300_000,
        "service_share": 70,
        "commerce_share": 20,
    })
    assert any("add up to 100" in alert for alert in result["alerts"])
