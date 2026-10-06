import csv
import io
import json
from datetime import datetime
from flask import Blueprint, jsonify, render_template, request

from .db import connect
from .engine import calculate, ENGINE_VERSION

bp = Blueprint("main", __name__)


def now():
    return datetime.now().isoformat(timespec="seconds")


def as_dict(row):
    return dict(row) if row else None


@bp.get("/")
def index():
    return render_template("index.html")


@bp.get("/api/health")
def health():
    return jsonify({"ok": True, "engine": ENGINE_VERSION, "release": "1.0.0"})


@bp.get("/api/companies")
def list_companies():
    with connect() as con:
        rows = con.execute("SELECT * FROM companies ORDER BY legal_name").fetchall()
    return jsonify([as_dict(row) for row in rows])


@bp.post("/api/companies")
def create_company():
    payload = request.get_json(force=True) or {}
    required = ["company_code", "legal_name", "sector"]
    missing = [field for field in required if not str(payload.get(field, "")).strip()]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    ts = now()
    try:
        with connect() as con:
            cur = con.execute(
                """INSERT INTO companies(company_code,legal_name,sector,city,state,current_regime,created_at,updated_at)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (
                    payload["company_code"].strip(),
                    payload["legal_name"].strip(),
                    payload["sector"].strip(),
                    payload.get("city", "").strip(),
                    payload.get("state", "").strip(),
                    payload.get("current_regime", "").strip(),
                    ts,
                    ts,
                ),
            )
            con.commit()
            company_id = cur.lastrowid
        return jsonify({"id": company_id}), 201
    except Exception as exc:
        return jsonify({"error": f"Could not create company: {exc}"}), 400


@bp.get("/api/companies/<int:company_id>")
def get_company(company_id):
    with connect() as con:
        company = con.execute("SELECT * FROM companies WHERE id=?", (company_id,)).fetchone()
        analysis = con.execute(
            "SELECT * FROM analyses WHERE company_id=? ORDER BY updated_at DESC, id DESC LIMIT 1",
            (company_id,),
        ).fetchone()
    if not company:
        return jsonify({"error": "Company not found"}), 404
    return jsonify({"company": as_dict(company), "analysis": as_dict(analysis)})


@bp.post("/api/analyses")
def save_analysis():
    payload = request.get_json(force=True) or {}
    company_id = int(payload.get("company_id") or 0)
    if not company_id:
        return jsonify({"error": "company_id is required"}), 400

    numeric_fields = ["annual_revenue", "payroll", "operating_costs", "service_share", "commerce_share"]
    values = {}
    for field in numeric_fields:
        try:
            values[field] = float(payload.get(field) or 0)
        except (TypeError, ValueError):
            return jsonify({"error": f"Invalid numeric value for {field}"}), 400

    ts = now()
    with connect() as con:
        company = con.execute("SELECT id FROM companies WHERE id=?", (company_id,)).fetchone()
        if not company:
            return jsonify({"error": "Company not found"}), 404
        cur = con.execute(
            """INSERT INTO analyses(company_id,reference_year,annual_revenue,payroll,operating_costs,service_share,commerce_share,source_note,created_at,updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                company_id,
                int(payload.get("reference_year") or datetime.now().year),
                values["annual_revenue"],
                values["payroll"],
                values["operating_costs"],
                values["service_share"],
                values["commerce_share"],
                payload.get("source_note", "Manual input"),
                ts,
                ts,
            ),
        )
        con.commit()
        analysis_id = cur.lastrowid
        row = con.execute("SELECT * FROM analyses WHERE id=?", (analysis_id,)).fetchone()
    return jsonify(as_dict(row)), 201


@bp.post("/api/simulate")
def simulate():
    payload = request.get_json(force=True) or {}
    company_id = int(payload.get("company_id") or 0)
    analysis_id = int(payload.get("analysis_id") or 0)
    persist = bool(payload.get("persist", True))

    with connect() as con:
        analysis = con.execute(
            "SELECT * FROM analyses WHERE id=? AND company_id=?", (analysis_id, company_id)
        ).fetchone()
    if not analysis:
        return jsonify({"error": "Analysis not found"}), 404

    result = calculate(dict(analysis))
    if persist:
        with connect() as con:
            con.execute(
                "INSERT INTO simulations(company_id,analysis_id,engine_version,result_json,created_at) VALUES (?,?,?,?,?)",
                (company_id, analysis_id, ENGINE_VERSION, json.dumps(result), now()),
            )
            con.commit()
    return jsonify(result)


@bp.get("/api/history/<int:company_id>")
def history(company_id):
    with connect() as con:
        rows = con.execute(
            "SELECT * FROM simulations WHERE company_id=? ORDER BY id DESC LIMIT 20", (company_id,)
        ).fetchall()
        imports = con.execute(
            "SELECT * FROM imports WHERE company_id=? ORDER BY id DESC LIMIT 20", (company_id,)
        ).fetchall()
    return jsonify({
        "simulations": [
            {
                "id": row["id"],
                "analysis_id": row["analysis_id"],
                "engine_version": row["engine_version"],
                "created_at": row["created_at"],
                "result": json.loads(row["result_json"]),
            }
            for row in rows
        ],
        "imports": [as_dict(row) for row in imports],
    })


@bp.post("/api/import-monthly")
def import_monthly():
    company_id = int(request.form.get("company_id") or 0)
    uploaded = request.files.get("file")
    if not company_id or not uploaded:
        return jsonify({"error": "company_id and file are required"}), 400

    try:
        stream = io.StringIO(uploaded.stream.read().decode("utf-8-sig"))
        reader = csv.DictReader(stream)
        required = {"month", "revenue", "payroll", "costs"}
        if not required.issubset(set(reader.fieldnames or [])):
            return jsonify({"error": "CSV must contain month,revenue,payroll,costs"}), 400

        rows = list(reader)
        revenue = sum(float(r.get("revenue") or 0) for r in rows)
        payroll = sum(float(r.get("payroll") or 0) for r in rows)
        costs = sum(float(r.get("costs") or 0) for r in rows)
    except Exception as exc:
        return jsonify({"error": f"Could not parse CSV: {exc}"}), 400

    with connect() as con:
        company = con.execute("SELECT id FROM companies WHERE id=?", (company_id,)).fetchone()
        if not company:
            return jsonify({"error": "Company not found"}), 404
        con.execute(
            "INSERT INTO imports(company_id,file_name,rows_loaded,annual_revenue,annual_payroll,annual_costs,created_at) VALUES (?,?,?,?,?,?,?)",
            (company_id, uploaded.filename or "monthly.csv", len(rows), revenue, payroll, costs, now()),
        )
        con.commit()

    return jsonify({
        "rows_loaded": len(rows),
        "annual_revenue": round(revenue, 2),
        "payroll": round(payroll, 2),
        "operating_costs": round(costs, 2),
    })
