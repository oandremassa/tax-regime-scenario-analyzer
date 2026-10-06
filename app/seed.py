from __future__ import annotations

import json
from datetime import datetime, timezone

from .db import get_db
from .engine import calculate, build_validations, ENGINE_VERSION


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _months(year, revenue_base, service_share, commerce_share, payroll_base, costs_base, expenses_base, tax_rate):
    season = [0.84, 0.91, 0.96, 1.00, 1.06, 1.10, 0.98, 1.04, 1.12, 1.18, 1.24, 1.34]
    rows = []
    for i, multiplier in enumerate(season, start=1):
        revenue = revenue_base * multiplier
        commerce = revenue * commerce_share
        service = revenue * service_share
        industry = max(revenue - commerce - service, 0)
        rows.append({
            "month": f"{year}-{i:02d}",
            "commerce_revenue": round(commerce, 2),
            "industry_revenue": round(industry, 2),
            "service_revenue": round(service, 2),
            "payroll": round(payroll_base * (1 + ((i - 1) * 0.008)), 2),
            "costs": round(costs_base * multiplier * 0.97, 2),
            "expenses": round(expenses_base * (0.96 + i * 0.006), 2),
            "current_tax_paid": round(revenue * tax_rate, 2),
        })
    return rows


def _insert_company(db, company, analysis_title, year, rows, doc_types):
    ts = now()
    cur = db.execute(
        """INSERT INTO companies(identifier,legal_name,trade_name,cnae,city,state,current_regime,service_annex,iss_rate,icms_rate,notes,created_at,updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            company["identifier"], company["legal_name"], company["trade_name"], company["cnae"],
            company["city"], company["state"], company["current_regime"], company["service_annex"],
            company["iss_rate"], company["icms_rate"], company["notes"], ts, ts,
        ),
    )
    cid = cur.lastrowid
    cur = db.execute(
        """INSERT INTO analyses(company_id,title,fiscal_year,period_start,period_end,status,source_note,created_at,updated_at)
           VALUES (?,?,?,?,?,'review',?,?,?)""",
        (cid, analysis_title, year, f"{year}-01", f"{year}-12", "Seeded synthetic 12-month portfolio dataset.", ts, ts),
    )
    aid = cur.lastrowid

    for r in rows:
        db.execute(
            """INSERT INTO monthly_financials(analysis_id,month,commerce_revenue,industry_revenue,service_revenue,payroll,costs,expenses,current_tax_paid,source,created_at,updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,'synthetic_seed',?,?)""",
            (aid, r["month"], r["commerce_revenue"], r["industry_revenue"], r["service_revenue"], r["payroll"], r["costs"], r["expenses"], r["current_tax_paid"], ts, ts),
        )

    for idx, doc_type in enumerate(doc_types, start=1):
        db.execute(
            """INSERT INTO documents(company_id,analysis_id,original_name,doc_type,parser_name,sha256,status,parsed_json,uploaded_at)
               VALUES (?,?,?,?,?,?,?, ?,?)""",
            (cid, aid, f"synthetic_{doc_type}_{year}_{idx}.demo", doc_type, f"{doc_type}_demo", f"DEMO-SHA-{cid}-{idx}", "processed", json.dumps({"synthetic": True, "doc_type": doc_type}), ts),
        )

    result = calculate(company, {"id": aid, "fiscal_year": year}, rows, doc_types)
    db.execute(
        """INSERT INTO simulations(company_id,analysis_id,engine_version,input_json,result_json,created_at)
           VALUES (?,?,?,?,?,?)""",
        (cid, aid, ENGINE_VERSION, json.dumps({"seeded": True, "source": "synthetic"}), json.dumps(result), ts),
    )

    for item in build_validations(company, {"id": aid, "fiscal_year": year}, rows, doc_types):
        db.execute(
            """INSERT OR IGNORE INTO validation_items(company_id,analysis_id,code,title,detail,severity,status,source_note,created_at,updated_at)
               VALUES (?,?,?,?,?,?,'pending',?,?,?)""",
            (cid, aid, item["code"], item["title"], item["detail"], item["severity"], item.get("source_note"), ts, ts),
        )

    db.execute(
        """INSERT INTO audit_log(company_id,analysis_id,action,entity,entity_id,field_name,old_value,new_value,created_at)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (cid, aid, "seed", "analysis", aid, "status", None, "review", ts),
    )
    return cid, aid


def seed_demo_data():
    db = get_db()
    if db.execute("SELECT 1 FROM companies LIMIT 1").fetchone():
        return

    sources = [
        ("Simples Nacional reference schedule", "Brazil", "Simplified regime", "Portfolio reference", "reviewed", "https://www8.receita.fazenda.gov.br/SimplesNacional/"),
        ("Corporate income tax reference", "Brazil", "IRPJ / CSLL", "Portfolio reference", "reviewed", "https://www.gov.br/receitafederal/"),
        ("Indirect taxes reference", "Brazil", "PIS / COFINS / ISS / ICMS", "Portfolio reference", "review_required", "https://www.gov.br/receitafederal/"),
    ]
    for title, jurisdiction, topic, version, status, url in sources:
        db.execute(
            "INSERT INTO regulatory_sources(title,jurisdiction,topic,version,status,url,updated_at) VALUES (?,?,?,?,?,?,?)",
            (title, jurisdiction, topic, version, status, url, now()),
        )

    rules = [
        ("presumed", "PIS rate", 0.0065, "decimal", "illustrative"),
        ("presumed", "COFINS rate", 0.03, "decimal", "illustrative"),
        ("actual", "PIS gross rate", 0.0165, "decimal", "illustrative"),
        ("actual", "COFINS gross rate", 0.076, "decimal", "illustrative"),
        ("all", "IRPJ base rate", 0.15, "decimal", "illustrative"),
        ("all", "CSLL proxy rate", 0.09, "decimal", "illustrative"),
    ]
    for regime, name, value, unit, status in rules:
        db.execute(
            """INSERT INTO scenario_rules(regime,rule_name,rule_value,unit,status,effective_from,effective_to,updated_at)
               VALUES (?,?,?,?,?,'2026-01-01',NULL,?)""",
            (regime, name, value, unit, status, now()),
        )

    companies = [
        ({
            "identifier": "DEMO-001",
            "legal_name": "Aurora Creative Labs Ltda.",
            "trade_name": "Aurora Labs",
            "cnae": "6201-5/01",
            "city": "São Paulo",
            "state": "SP",
            "current_regime": "Simples Nacional",
            "service_annex": None,
            "iss_rate": 0.025,
            "icms_rate": 0.00,
            "notes": "Synthetic service company used to demonstrate Factor R and 12-month review.",
        }, "FY2026 Tax Planning", 2026, _months(2026, 118000, 1.0, 0.0, 36000, 18000, 21000, 0.118), ["dre"]),
        ({
            "identifier": "DEMO-002",
            "legal_name": "Northstar Retail & Services Ltda.",
            "trade_name": "Northstar",
            "cnae": "4751-2/01",
            "city": "Campinas",
            "state": "SP",
            "current_regime": "Lucro Presumido",
            "service_annex": "Mixed operations review",
            "iss_rate": 0.03,
            "icms_rate": 0.12,
            "notes": "Synthetic mixed-operation company with commerce and services.",
        }, "2026 Strategic Regime Review", 2026, _months(2026, 235000, 0.28, 0.58, 54000, 82000, 31000, 0.142), ["dre", "nfe"]),
        ({
            "identifier": "DEMO-003",
            "legal_name": "Lumen Industrial Systems Ltda.",
            "trade_name": "Lumen Systems",
            "cnae": "2829-1/99",
            "city": "Sorocaba",
            "state": "SP",
            "current_regime": "Lucro Real",
            "service_annex": None,
            "iss_rate": 0.02,
            "icms_rate": 0.12,
            "notes": "Synthetic industrial profile for higher-volume scenario testing.",
        }, "2026 Corporate Tax Benchmark", 2026, _months(2026, 420000, 0.08, 0.12, 87000, 218000, 48000, 0.165), ["dre", "nfe", "xml"]),
    ]

    for data in companies:
        _insert_company(db, *data)

    db.commit()
