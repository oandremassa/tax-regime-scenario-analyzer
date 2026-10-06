ENGINE_VERSION = "portfolio-1.0"


def _money(value):
    return round(float(value or 0), 2)


def validate_inputs(analysis):
    alerts = []
    revenue = float(analysis.get("annual_revenue") or 0)
    payroll = float(analysis.get("payroll") or 0)
    service = float(analysis.get("service_share") or 0)
    commerce = float(analysis.get("commerce_share") or 0)

    if revenue <= 0:
        alerts.append("Annual revenue must be greater than zero.")
    if payroll <= 0:
        alerts.append("Payroll is empty; payroll-sensitive comparisons may be incomplete.")
    if abs((service + commerce) - 100) > 0.01:
        alerts.append("Service share and commerce share should add up to 100%.")
    return alerts


def calculate(analysis):
    """Illustrative scenario model for portfolio use only.

    The model intentionally uses simplified assumptions. It is not a tax filing
    calculator and must not be used for legal, accounting or tax advice.
    """
    revenue = float(analysis.get("annual_revenue") or 0)
    payroll = float(analysis.get("payroll") or 0)
    costs = float(analysis.get("operating_costs") or 0)
    service_share = float(analysis.get("service_share") or 0) / 100
    commerce_share = float(analysis.get("commerce_share") or 0) / 100

    if revenue <= 0:
        return {"engine_version": ENGINE_VERSION, "scenarios": [], "alerts": validate_inputs(analysis)}

    # Simplified, configurable assumptions for demonstration purposes.
    simple_rate = 0.075 + max(revenue - 1_000_000, 0) / 12_000_000 * 0.055
    simple_rate = min(simple_rate, 0.155)
    simple_estimate = revenue * simple_rate + payroll * 0.006

    presumed_rate = (service_share * 0.1325) + (commerce_share * 0.0775)
    presumed_estimate = revenue * presumed_rate + payroll * 0.012

    accounting_margin = max(revenue - costs - payroll, 0)
    actual_estimate = revenue * 0.0365 + accounting_margin * 0.15 + payroll * 0.012

    scenarios = [
        ("Simplified Regime", simple_estimate, "Illustrative revenue-band model"),
        ("Presumed Profit", presumed_estimate, "Weighted service/commerce assumption"),
        ("Actual Profit", actual_estimate, "Revenue taxes plus taxable accounting margin"),
    ]

    result = []
    for name, estimate, note in scenarios:
        result.append({
            "name": name,
            "estimated_tax": _money(estimate),
            "effective_rate": round((estimate / revenue) * 100, 2),
            "monthly_equivalent": _money(estimate / 12),
            "note": note,
        })

    result.sort(key=lambda item: item["estimated_tax"])
    best = result[0]

    return {
        "engine_version": ENGINE_VERSION,
        "recommended_scenario": best["name"],
        "estimated_annual_difference": _money(result[-1]["estimated_tax"] - best["estimated_tax"]),
        "scenarios": result,
        "alerts": validate_inputs(analysis),
        "disclaimer": "Portfolio demonstration only. The rates and formulas are intentionally simplified and are not tax advice.",
    }
