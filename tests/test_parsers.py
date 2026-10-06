from pathlib import Path
from app.parsers import parse_document


def test_financial_csv_parser(tmp_path: Path):
    p = tmp_path / "financials.csv"
    p.write_text(
        "month,commerce_revenue,industry_revenue,service_revenue,payroll,costs,expenses,current_tax_paid\n"
        "2026-01,10000,0,90000,30000,10000,12000,11000\n",
        encoding="utf-8",
    )
    result = parse_document(p)
    assert result["parser"] == "csv_financials"
    assert len(result["monthly_rows"]) == 1
    assert result["monthly_rows"][0]["service_revenue"] == 90000


def test_pgdas_like_parser(tmp_path: Path):
    p = tmp_path / "pgdas.txt"
    p.write_text("PGDAS SIMPLES NACIONAL\nRBT12: 1.200.000,00\nDAS: 12.500,00", encoding="utf-8")
    result = parse_document(p)
    assert result["parser"] == "pgdas_proxy"
    assert result["rbt12"] == 1200000
