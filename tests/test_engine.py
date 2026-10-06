from app.engine import calculate, build_validations


def company():
    return {
        "id": 1,
        "cnae": "6201-5/01",
        "current_regime": "Brazilian Simplified Tax Regime",
        "service_annex": "review",
        "iss_rate": 0.025,
        "icms_rate": 0.0,
    }


def monthly():
    return [
        {
            "month": f"2026-{i:02d}",
            "commerce_revenue": 0,
            "industry_revenue": 0,
            "service_revenue": 100000 + i * 1000,
            "payroll": 32000,
            "costs": 15000,
            "expenses": 18000,
            "current_tax_paid": 12000,
        }
        for i in range(1, 13)
    ]


def test_three_scenarios_are_returned():
    result = calculate(company(), {"id": 1}, monthly(), ["income_statement", "simplified_regime_filing"])
    assert len(result["scenarios"]) == 3
    assert {x["key"] for x in result["scenarios"]} == {"simplified_regime", "presumed_profit", "actual_profit"}
    assert result["best_scenario"]["key"] in {"simplified_regime", "presumed_profit", "actual_profit"}


def test_full_dataset_has_no_period_blocker():
    items = build_validations(company(), {"id": 1}, monthly(), ["income_statement", "simplified_regime_filing"])
    assert not any(x["code"] == "PERIOD_COVERAGE" for x in items)


def test_incomplete_period_blocks():
    items = build_validations(company(), {"id": 1}, monthly()[:6], ["income_statement", "simplified_regime_filing"])
    period = next(x for x in items if x["code"] == "PERIOD_COVERAGE")
    assert period["severity"] == "blocking"


def test_zero_revenue_does_not_produce_scenarios():
    rows = monthly()
    for row in rows:
        row["service_revenue"] = 0
    result = calculate(company(), {"id": 1}, rows, ["income_statement", "simplified_regime_filing"])
    assert result["scenarios"] == []
