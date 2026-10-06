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


def test_simplified_regime_filing_parser(tmp_path: Path):
    p = tmp_path / "simplified_regime_filing.txt"
    p.write_text("SIMPLIFIED REGIME FILING\nTWELVE_MONTH_REVENUE: 1.200.000,00\nCURRENT_TAX: 12.500,00", encoding="utf-8")
    result = parse_document(p)
    assert result["parser"] == "simplified_regime_filing_proxy"
    assert result["rbt12"] == 1200000
