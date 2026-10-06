from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

ENGINE_VERSION = "2.1.0-portfolio"


@dataclass(frozen=True)
class Scenario:
    key: str
    label: str
    subtitle: str
    total_tax: float
    effective_rate: float
    components: dict
    assumptions: list[str]
    monthly_estimate: float

    def as_dict(self):
        return {
            "key": self.key,
            "label": self.label,
            "subtitle": self.subtitle,
            "total_tax": round(self.total_tax, 2),
            "effective_rate": round(self.effective_rate, 2),
            "components": {k: round(v, 2) for k, v in self.components.items()},
            "assumptions": self.assumptions,
            "monthly_estimate": round(self.monthly_estimate, 2),
        }


SCHEDULES = {
    "commerce": [
        (180_000, 0.040, 0),
        (360_000, 0.073, 5_940),
        (720_000, 0.095, 13_860),
        (1_800_000, 0.107, 22_500),
        (3_600_000, 0.143, 87_300),
        (4_800_000, 0.190, 378_000),
    ],
    "industry": [
        (180_000, 0.045, 0),
        (360_000, 0.078, 5_940),
        (720_000, 0.100, 13_860),
        (1_800_000, 0.112, 22_500),
        (3_600_000, 0.147, 85_500),
        (4_800_000, 0.300, 720_000),
    ],
    "annex_iii": [
        (180_000, 0.060, 0),
        (360_000, 0.112, 9_360),
        (720_000, 0.135, 17_640),
        (1_800_000, 0.160, 35_640),
        (3_600_000, 0.210, 125_640),
        (4_800_000, 0.330, 648_000),
    ],
    "annex_v": [
        (180_000, 0.155, 0),
        (360_000, 0.180, 4_500),
        (720_000, 0.195, 9_900),
        (1_800_000, 0.205, 17_100),
        (3_600_000, 0.230, 62_100),
        (4_800_000, 0.305, 540_000),
    ],
}


def _n(value) -> float:
    try:
        return max(float(value or 0), 0.0)
    except (TypeError, ValueError):
        return 0.0


def _effective_from_schedule(rbt12: float, schedule: list[tuple[float, float, float]]) -> float:
    revenue = max(rbt12, 1.0)
    ceiling, nominal, deduction = schedule[-1]
    for band in schedule:
        if revenue <= band[0]:
            ceiling, nominal, deduction = band
            break
    effective = ((revenue * nominal) - deduction) / revenue
    return max(effective, 0.0)


def _irpj_with_surcharge(base: float) -> tuple[float, float]:
    base = _n(base)
    regular = base * 0.15
    surcharge = max(base - 240_000, 0) * 0.10
    return regular, surcharge


def _aggregate(monthly_rows: Iterable[Mapping]) -> dict:
    rows = [dict(r) for r in monthly_rows]
    sums = {
        "commerce_revenue": 0.0,
        "industry_revenue": 0.0,
        "service_revenue": 0.0,
        "payroll": 0.0,
        "costs": 0.0,
        "expenses": 0.0,
        "current_tax_paid": 0.0,
    }
    monthly = []
    for row in rows:
        item = {k: _n(row.get(k)) for k in sums}
        item["month"] = row.get("month")
        item["revenue"] = item["commerce_revenue"] + item["industry_revenue"] + item["service_revenue"]
        monthly.append(item)
        for key in sums:
            sums[key] += item[key]

    total_revenue = sums["commerce_revenue"] + sums["industry_revenue"] + sums["service_revenue"]
    operating_profit = total_revenue - sums["payroll"] - sums["costs"] - sums["expenses"]
    return {
        **sums,
        "revenue": total_revenue,
        "operating_profit": operating_profit,
        "margin": (operating_profit / total_revenue * 100) if total_revenue else 0,
        "factor_r": (sums["payroll"] / total_revenue) if total_revenue else 0,
        "months": len(rows),
        "monthly": monthly,
    }


def _allocate_simplified_regime(total: float, company: Mapping, agg: Mapping) -> dict:
    service_share = agg["service_revenue"] / agg["revenue"] if agg["revenue"] else 0
    trade_share = (agg["commerce_revenue"] + agg["industry_revenue"]) / agg["revenue"] if agg["revenue"] else 0
    iss_icms = total * (0.24 * service_share + 0.28 * trade_share)
    cpp = total * 0.30
    remaining = max(total - iss_icms - cpp, 0)
    return {
        "Corporate Income Tax (IRPJ)": remaining * 0.16,
        "Social Contribution on Net Profit (CSLL)": remaining * 0.14,
        "Social Integration Contribution (PIS/Pasep)": remaining * 0.10,
        "Social Security Financing Contribution (COFINS)": remaining * 0.42,
        "Employer Social Security Contribution (CPP)": cpp,
        "Service Tax / State VAT allocation (ISS/ICMS)": iss_icms,
        "Other federal allocation": remaining * 0.18,
    }


def _simplified_regime(company: Mapping, agg: Mapping) -> Scenario:
    rbt12 = max(agg["revenue"], 1)
    service_annex = "annex_iii" if agg["factor_r"] >= 0.28 else "annex_v"
    service_annex_label = "Service Tier III proxy" if service_annex == "annex_iii" else "Service Tier V proxy"

    commerce_rate = _effective_from_schedule(rbt12, SCHEDULES["commerce"])
    industry_rate = _effective_from_schedule(rbt12, SCHEDULES["industry"])
    service_rate = _effective_from_schedule(rbt12, SCHEDULES[service_annex])

    total = (
        agg["commerce_revenue"] * commerce_rate
        + agg["industry_revenue"] * industry_rate
        + agg["service_revenue"] * service_rate
    )
    effective = total / agg["revenue"] * 100 if agg["revenue"] else 0
    assumptions = [
        f"12-month gross revenue proxy: BRL {agg['revenue']:,.2f}",
        f"Factor R proxy: {agg['factor_r'] * 100:.2f}%",
        f"Services modeled under {service_annex_label}",
        "Component split is illustrative and used only for portfolio transparency.",
    ]
    return Scenario(
        "simplified_regime",
        "Brazilian Simplified Tax Regime",
        service_annex_label,
        total,
        effective,
        _allocate_simplified_regime(total, company, agg),
        assumptions,
        total / max(agg["months"], 1),
    )


def _presumed(company: Mapping, agg: Mapping) -> Scenario:
    service = agg["service_revenue"]
    trade = agg["commerce_revenue"] + agg["industry_revenue"]
    revenue = agg["revenue"]

    irpj_base = service * 0.32 + trade * 0.08
    csll_base = service * 0.32 + trade * 0.12
    irpj, surcharge = _irpj_with_surcharge(irpj_base)
    csll = csll_base * 0.09
    pis = revenue * 0.0065
    cofins = revenue * 0.03
    iss = service * _n(company.get("iss_rate"))
    icms_proxy = trade * _n(company.get("icms_rate")) * 0.35

    components = {
        "Corporate Income Tax (IRPJ)": irpj,
        "Corporate Income Tax surcharge (IRPJ)": surcharge,
        "Social Contribution on Net Profit (CSLL)": csll,
        "Social Integration Contribution (PIS)": pis,
        "Social Security Financing Contribution (COFINS)": cofins,
        "Service Tax (ISS)": iss,
        "State VAT gross proxy (ICMS)": icms_proxy,
    }
    total = sum(components.values())
    effective = total / revenue * 100 if revenue else 0
    assumptions = [
        "Presumed bases are modeled by activity mix for demonstration.",
        f"Service Tax input (ISS): {_n(company.get('iss_rate')) * 100:.2f}%",
        f"State VAT input (ICMS): {_n(company.get('icms_rate')) * 100:.2f}% with simplified gross proxy.",
        "Credits, special regimes, withholding and activity-specific adjustments are not modeled.",
    ]
    return Scenario("presumed_profit", "Presumed Profit Regime", "Activity-based presumed bases", total, effective, components, assumptions, total / max(agg["months"], 1))


def _actual(company: Mapping, agg: Mapping) -> Scenario:
    revenue = agg["revenue"]
    profit = max(agg["operating_profit"], 0)
    irpj, surcharge = _irpj_with_surcharge(profit)
    csll = profit * 0.09
    pis = revenue * 0.0165
    cofins = revenue * 0.076
    iss = agg["service_revenue"] * _n(company.get("iss_rate"))
    trade = agg["commerce_revenue"] + agg["industry_revenue"]
    icms_proxy = trade * _n(company.get("icms_rate")) * 0.20

    components = {
        "Corporate Income Tax (IRPJ)": irpj,
        "Corporate Income Tax surcharge (IRPJ)": surcharge,
        "Social Contribution on Net Profit (CSLL)": csll,
        "Social Integration Contribution gross (PIS)": pis,
        "Social Security Financing Contribution gross (COFINS)": cofins,
        "Service Tax (ISS)": iss,
        "State VAT gross proxy (ICMS)": icms_proxy,
    }
    total = sum(components.values())
    effective = total / revenue * 100 if revenue else 0
    assumptions = [
        f"Operating profit proxy before tax: BRL {profit:,.2f}",
        "Federal social contributions are shown gross before non-cumulative credits.",
        "Loss carryforwards, tax additions/exclusions and tax credits are not modeled.",
        "Quarterly/annual tax timing is summarized as an annual scenario.",
    ]
    return Scenario("actual_profit", "Actual Profit Regime", "Profit-based proxy", total, effective, components, assumptions, total / max(agg["months"], 1))


def build_validations(company: Mapping, analysis: Mapping, monthly_rows: Iterable[Mapping], document_types: Iterable[str] = ()) -> list[dict]:
    rows = [dict(r) for r in monthly_rows]
    agg = _aggregate(rows)
    docs = {str(x or "").lower() for x in document_types}
    items = []

    def add(code, title, detail, severity, source=None):
        items.append({"code": code, "title": title, "detail": detail, "severity": severity, "source_note": source})

    if agg["months"] < 12:
        add("PERIOD_COVERAGE", "Incomplete 12-month period", f"Only {agg['months']} month(s) are loaded. A full-year comparison is recommended.", "blocking")
    if not company.get("cnae"):
        add("BUSINESS_ACTIVITY_CODE_MISSING", "Business activity code missing", "A business activity code is required for a production-grade tax assessment.", "high")
    if agg["service_revenue"] > 0 and _n(company.get("iss_rate")) <= 0:
        add("SERVICE_TAX_RATE_MISSING", "Service tax rate not confirmed", "Service revenue exists but no Service Tax rate has been confirmed for the company.", "blocking")
    if agg["service_revenue"] > 0 and not company.get("service_annex"):
        add("SERVICE_TAX_TIER_REVIEW", "Service tax tier requires review", "Service revenue exists and the simplified-regime service-tier reference has not been confirmed.", "high")
    if not company.get("current_regime"):
        add("REGIME_MISSING", "Current regime missing", "The company's current tax regime should be recorded for baseline comparison.", "high")
    if agg["revenue"] <= 0:
        add("REVENUE_ZERO", "Revenue is zero", "A scenario cannot be calculated without revenue.", "blocking")
    if agg["payroll"] > agg["revenue"] and agg["revenue"] > 0:
        add("PAYROLL_HIGH", "Payroll exceeds revenue", "Confirm that payroll and revenue use the same period.", "high")
    if agg["commerce_revenue"] > 0 and agg["service_revenue"] > 0:
        add("MIXED_OPERATIONS", "Mixed activity profile", "Commerce and services are both present. Review segregation and applicable taxes by activity.", "medium")
    if not ({"income_statement", "dre"} & docs):
        add("INCOME_STATEMENT_NOT_LOADED", "Income statement not loaded", "An income statement or equivalent accounting statement improves cost, expense and profit validation.", "medium")
    if not ({"simplified_regime_filing", "pgdas"} & docs) and str(company.get("current_regime") or "").lower().startswith("brazilian simplified"):
        add("SIMPLIFIED_FILING_NOT_LOADED", "Simplified-regime filing evidence not loaded", "A simplified-regime filing extract can be used to reconcile the current baseline.", "medium")

    return items


def calculate(company: Mapping, analysis: Mapping, monthly_rows: Iterable[Mapping], document_types: Iterable[str] = ()) -> dict:
    rows = [dict(r) for r in monthly_rows]
    agg = _aggregate(rows)
    validations = build_validations(company, analysis, rows, document_types)
    blocking_count = sum(1 for v in validations if v["severity"] == "blocking")

    if agg["revenue"] <= 0:
        scenarios = []
    else:
        scenarios = [_simplified_regime(company, agg), _presumed(company, agg), _actual(company, agg)]

    scenario_dicts = [s.as_dict() for s in scenarios]
    sorted_scenarios = sorted(scenario_dicts, key=lambda x: x["total_tax"]) if scenario_dicts else []
    best = sorted_scenarios[0] if sorted_scenarios else None
    highest = sorted_scenarios[-1] if sorted_scenarios else None
    baseline = agg["current_tax_paid"]

    for scenario in scenario_dicts:
        scenario["difference_vs_lowest"] = round(scenario["total_tax"] - (best["total_tax"] if best else 0), 2)
        scenario["difference_vs_current"] = round(scenario["total_tax"] - baseline, 2) if baseline else None

    return {
        "engine_version": ENGINE_VERSION,
        "status": "preliminary" if blocking_count else "review_ready",
        "blocking_validations": blocking_count,
        "aggregates": {
            k: round(v, 2) if isinstance(v, float) else v
            for k, v in agg.items()
            if k != "monthly"
        },
        "monthly": agg["monthly"],
        "validations": validations,
        "scenarios": scenario_dicts,
        "best_scenario": best,
        "highest_scenario": highest,
        "potential_savings_vs_highest": round((highest["total_tax"] - best["total_tax"]), 2) if best and highest else 0,
        "current_tax_baseline": round(baseline, 2),
        "portfolio_disclaimer": "Illustrative portfolio model only. It is not tax, accounting or legal advice.",
    }
