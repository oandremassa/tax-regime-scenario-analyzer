from datetime import datetime
from .db import connect


def _now():
    return datetime.now().isoformat(timespec="seconds")


def seed_demo_data(path):
    with connect(path) as con:
        count = con.execute("SELECT COUNT(*) AS n FROM companies").fetchone()["n"]
        if count:
            return

        companies = [
            ("DEMO-001", "Northstar Studio Ltd.", "Professional Services", "São Paulo", "SP", "Simplified Regime"),
            ("DEMO-002", "Aurora Foods Ltd.", "Food Manufacturing", "Campinas", "SP", "Presumed Profit"),
            ("DEMO-003", "Blue Harbor Commerce Ltd.", "Retail", "Santos", "SP", "Simplified Regime"),
            ("DEMO-004", "Vertex Digital Labs Ltd.", "Technology", "Curitiba", "PR", "Presumed Profit"),
        ]
        ts = _now()
        for row in companies:
            con.execute(
                "INSERT INTO companies(company_code,legal_name,sector,city,state,current_regime,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)",
                (*row, ts, ts),
            )

        samples = [
            (1, 2027, 2_400_000, 420_000, 610_000, 90, 10, "Synthetic baseline for demo"),
            (2, 2027, 4_800_000, 720_000, 2_350_000, 15, 85, "Synthetic manufacturing scenario"),
            (3, 2027, 1_650_000, 260_000, 810_000, 5, 95, "Synthetic retail scenario"),
            (4, 2027, 3_200_000, 640_000, 980_000, 100, 0, "Synthetic technology services scenario"),
        ]
        for item in samples:
            con.execute(
                "INSERT INTO analyses(company_id,reference_year,annual_revenue,payroll,operating_costs,service_share,commerce_share,source_note,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (*item, ts, ts),
            )
        con.commit()
