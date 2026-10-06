from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from flask import Blueprint, current_app, jsonify, render_template, request
from werkzeug.utils import secure_filename

from .db import get_db
from .engine import ENGINE_VERSION, build_validations, calculate
from .parsers import parse_document, sha256_file

bp = Blueprint("main", __name__)


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def row_dict(row):
    return dict(row) if row else None


def audit(db, *, action, entity, entity_id=None, company_id=None, analysis_id=None, field_name=None, old_value=None, new_value=None):
    db.execute(
        """INSERT INTO audit_log(company_id,analysis_id,action,entity,entity_id,field_name,old_value,new_value,created_at)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (company_id, analysis_id, action, entity, entity_id, field_name,
         None if old_value is None else str(old_value), None if new_value is None else str(new_value), now()),
    )


def company_or_404(db, company_id):
    return db.execute("SELECT * FROM companies WHERE id=?", (company_id,)).fetchone()


def analysis_or_404(db, analysis_id):
    return db.execute("SELECT * FROM analyses WHERE id=?", (analysis_id,)).fetchone()


def analysis_rows(db, analysis_id):
    return db.execute("SELECT * FROM monthly_financials WHERE analysis_id=? ORDER BY month", (analysis_id,)).fetchall()


def document_types(db, analysis_id):
    return [r["doc_type"] for r in db.execute("SELECT doc_type FROM documents WHERE analysis_id=?", (analysis_id,)).fetchall()]


def sync_validations(db, company, analysis, monthly, doc_types):
    company_map = dict(company) if not isinstance(company, dict) else company
    analysis_map = dict(analysis) if not isinstance(analysis, dict) else analysis
    monthly_maps = [dict(row) if not isinstance(row, dict) else row for row in monthly]
    generated = build_validations(company_map, analysis_map, monthly_maps, doc_types)
    generated_codes = {x["code"] for x in generated}
    ts = now()

    for item in generated:
        existing = db.execute(
            "SELECT * FROM validation_items WHERE company_id=? AND analysis_id=? AND code=?",
            (company["id"], analysis["id"], item["code"]),
        ).fetchone()
        if existing:
            db.execute(
                """UPDATE validation_items SET title=?,detail=?,severity=?,source_note=?,updated_at=?
                   WHERE id=?""",
                (item["title"], item["detail"], item["severity"], item.get("source_note"), ts, existing["id"]),
            )
        else:
            db.execute(
                """INSERT INTO validation_items(company_id,analysis_id,code,title,detail,severity,status,source_note,created_at,updated_at)
                   VALUES (?,?,?,?,?,?,'pending',?,?,?)""",
                (company["id"], analysis["id"], item["code"], item["title"], item["detail"], item["severity"], item.get("source_note"), ts, ts),
            )

    # Automatically resolve generated checks that no longer apply, but preserve human validation history.
    current = db.execute(
        "SELECT id,code,status FROM validation_items WHERE company_id=? AND analysis_id=?",
        (company["id"], analysis["id"]),
    ).fetchall()
    for item in current:
        if item["code"] not in generated_codes and item["status"] == "pending":
            db.execute("UPDATE validation_items SET status='resolved',updated_at=? WHERE id=?", (ts, item["id"]))

    return db.execute(
        """SELECT * FROM validation_items WHERE company_id=? AND analysis_id=?
           ORDER BY CASE severity WHEN 'blocking' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, id""",
        (company["id"], analysis["id"]),
    ).fetchall()


@bp.get("/")
def index():
    return render_template("index.html")


@bp.get("/api/health")
def health():
    return jsonify({"ok": True, "release": "2.1.0", "engine": ENGINE_VERSION, "edition": "public-portfolio"})


@bp.get("/api/bootstrap")
def bootstrap():
    db = get_db()
    companies = db.execute("SELECT * FROM companies ORDER BY legal_name").fetchall()
    company_id = request.args.get("company_id", type=int) or (companies[0]["id"] if companies else None)
    company = company_or_404(db, company_id) if company_id else None
    analyses = db.execute(
        "SELECT * FROM analyses WHERE company_id=? ORDER BY fiscal_year DESC,id DESC", (company_id,)
    ).fetchall() if company_id else []
    analysis_id = request.args.get("analysis_id", type=int) or (analyses[0]["id"] if analyses else None)

    return jsonify({
        "companies": [dict(x) for x in companies],
        "selected_company": row_dict(company),
        "analyses": [dict(x) for x in analyses],
        "selected_analysis_id": analysis_id,
        "engine_version": ENGINE_VERSION,
    })


@bp.get("/api/dashboard")
def dashboard():
    db = get_db()
    company_count = db.execute("SELECT COUNT(*) n FROM companies").fetchone()["n"]
    analysis_count = db.execute("SELECT COUNT(*) n FROM analyses").fetchone()["n"]
    pending = db.execute("SELECT COUNT(*) n FROM validation_items WHERE status='pending'").fetchone()["n"]
    docs = db.execute("SELECT COUNT(*) n FROM documents").fetchone()["n"]
    sims = db.execute("SELECT COUNT(*) n FROM simulations").fetchone()["n"]
    recent = db.execute(
        """SELECT s.id,s.created_at,s.analysis_id,c.trade_name,c.legal_name,a.title,s.result_json
           FROM simulations s JOIN companies c ON c.id=s.company_id JOIN analyses a ON a.id=s.analysis_id
           ORDER BY s.id DESC LIMIT 6"""
    ).fetchall()
    activity = db.execute(
        """SELECT a.*,c.trade_name,c.legal_name FROM audit_log a
           LEFT JOIN companies c ON c.id=a.company_id ORDER BY a.id DESC LIMIT 8"""
    ).fetchall()
    return jsonify({
        "metrics": {"companies": company_count, "analyses": analysis_count, "pending_validations": pending, "documents": docs, "simulations": sims},
        "recent_simulations": [
            {**{k: r[k] for k in r.keys() if k != "result_json"}, "result": json.loads(r["result_json"])} for r in recent
        ],
        "activity": [dict(x) for x in activity],
    })


@bp.route("/api/companies", methods=["GET", "POST"])
def companies():
    db = get_db()
    if request.method == "GET":
        rows = db.execute("SELECT * FROM companies ORDER BY legal_name").fetchall()
        return jsonify([dict(x) for x in rows])

    p = request.get_json(silent=True) or {}
    legal_name = str(p.get("legal_name") or "").strip()
    identifier = str(p.get("identifier") or "").strip()
    if not legal_name or not identifier:
        return jsonify({"error": "legal_name and identifier are required"}), 400
    ts = now()
    try:
        cur = db.execute(
            """INSERT INTO companies(identifier,legal_name,trade_name,cnae,city,state,current_regime,service_annex,iss_rate,icms_rate,notes,created_at,updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (identifier, legal_name, p.get("trade_name"), p.get("cnae"), p.get("city"), p.get("state"), p.get("current_regime"), p.get("service_annex"), float(p.get("iss_rate") or 0), float(p.get("icms_rate") or 0), p.get("notes"), ts, ts),
        )
        audit(db, action="create", entity="company", entity_id=cur.lastrowid, company_id=cur.lastrowid, new_value=legal_name)
        db.commit()
    except Exception as exc:
        if "UNIQUE" in str(exc).upper():
            return jsonify({"error": "identifier already exists"}), 409
        raise
    return jsonify(row_dict(company_or_404(db, cur.lastrowid))), 201


@bp.route("/api/companies/<int:company_id>", methods=["GET", "PATCH"])
def company_detail(company_id):
    db = get_db()
    company = company_or_404(db, company_id)
    if not company:
        return jsonify({"error": "company not found"}), 404
    if request.method == "GET":
        analyses = db.execute("SELECT * FROM analyses WHERE company_id=? ORDER BY fiscal_year DESC,id DESC", (company_id,)).fetchall()
        return jsonify({"company": dict(company), "analyses": [dict(x) for x in analyses]})

    p = request.get_json(silent=True) or {}
    allowed = {"legal_name", "trade_name", "cnae", "city", "state", "current_regime", "service_annex", "iss_rate", "icms_rate", "notes"}
    updates = {k: p[k] for k in allowed if k in p}
    if not updates:
        return jsonify(dict(company))
    for k in ("iss_rate", "icms_rate"):
        if k in updates:
            updates[k] = float(updates[k] or 0)
    for key, value in updates.items():
        audit(db, action="update", entity="company", entity_id=company_id, company_id=company_id, field_name=key, old_value=company[key], new_value=value)
    updates["updated_at"] = now()
    db.execute("UPDATE companies SET " + ",".join(f"{k}=?" for k in updates) + " WHERE id=?", (*updates.values(), company_id))
    db.commit()
    return jsonify(row_dict(company_or_404(db, company_id)))


@bp.get("/api/companies/<int:company_id>/analyses")
def company_analyses(company_id):
    db = get_db()
    rows = db.execute("SELECT * FROM analyses WHERE company_id=? ORDER BY fiscal_year DESC,id DESC", (company_id,)).fetchall()
    return jsonify([dict(x) for x in rows])


@bp.post("/api/analyses")
def create_analysis():
    db = get_db()
    p = request.get_json(silent=True) or {}
    company_id = int(p.get("company_id") or 0)
    if not company_or_404(db, company_id):
        return jsonify({"error": "company not found"}), 404
    year = int(p.get("fiscal_year") or datetime.now().year)
    title = str(p.get("title") or f"FY{year} Tax Planning").strip()
    ts = now()
    cur = db.execute(
        """INSERT INTO analyses(company_id,title,fiscal_year,period_start,period_end,status,source_note,created_at,updated_at)
           VALUES (?,?,?,?,?,'draft',?,?,?)""",
        (company_id, title, year, p.get("period_start") or f"{year}-01", p.get("period_end") or f"{year}-12", p.get("source_note"), ts, ts),
    )
    audit(db, action="create", entity="analysis", entity_id=cur.lastrowid, company_id=company_id, analysis_id=cur.lastrowid, new_value=title)
    db.commit()
    return jsonify(row_dict(analysis_or_404(db, cur.lastrowid))), 201


@bp.get("/api/analyses/<int:analysis_id>")
def analysis_detail(analysis_id):
    db = get_db()
    analysis = analysis_or_404(db, analysis_id)
    if not analysis:
        return jsonify({"error": "analysis not found"}), 404
    company = company_or_404(db, analysis["company_id"])
    monthly = analysis_rows(db, analysis_id)
    docs = db.execute("SELECT * FROM documents WHERE analysis_id=? ORDER BY id DESC", (analysis_id,)).fetchall()
    validations = sync_validations(db, company, analysis, monthly, [d["doc_type"] for d in docs])
    db.commit()
    latest = db.execute("SELECT * FROM simulations WHERE analysis_id=? ORDER BY id DESC LIMIT 1", (analysis_id,)).fetchone()
    return jsonify({
        "analysis": dict(analysis),
        "company": dict(company),
        "monthly": [dict(x) for x in monthly],
        "documents": [dict(x) for x in docs],
        "validations": [dict(x) for x in validations],
        "latest_simulation": ({**dict(latest), "result": json.loads(latest["result_json"])} if latest else None),
    })


@bp.put("/api/analyses/<int:analysis_id>/monthly")
def save_monthly(analysis_id):
    db = get_db()
    analysis = analysis_or_404(db, analysis_id)
    if not analysis:
        return jsonify({"error": "analysis not found"}), 404
    p = request.get_json(silent=True) or {}
    rows = p.get("rows") or []
    ts = now()
    numeric = ["commerce_revenue", "industry_revenue", "service_revenue", "payroll", "costs", "expenses", "current_tax_paid"]
    for row in rows:
        month = str(row.get("month") or "")[:7]
        if len(month) != 7:
            continue
        vals = [float(row.get(k) or 0) for k in numeric]
        db.execute(
            """INSERT INTO monthly_financials(analysis_id,month,commerce_revenue,industry_revenue,service_revenue,payroll,costs,expenses,current_tax_paid,source,created_at,updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,'manual',?,?)
               ON CONFLICT(analysis_id,month) DO UPDATE SET
                 commerce_revenue=excluded.commerce_revenue,industry_revenue=excluded.industry_revenue,service_revenue=excluded.service_revenue,
                 payroll=excluded.payroll,costs=excluded.costs,expenses=excluded.expenses,current_tax_paid=excluded.current_tax_paid,
                 source='manual',updated_at=excluded.updated_at""",
            (analysis_id, month, *vals, ts, ts),
        )
    db.execute("UPDATE analyses SET status='review',updated_at=? WHERE id=?", (ts, analysis_id))
    audit(db, action="save", entity="monthly_financials", company_id=analysis["company_id"], analysis_id=analysis_id, entity_id=analysis_id, new_value=f"{len(rows)} rows")
    db.commit()
    return jsonify({"ok": True, "rows": len(rows)})


@bp.post("/api/upload")
def upload():
    db = get_db()
    company_id = request.form.get("company_id", type=int)
    analysis_id = request.form.get("analysis_id", type=int)
    files = request.files.getlist("files")
    if not company_id or not analysis_id or not files:
        return jsonify({"error": "company_id, analysis_id and files are required"}), 400
    company = company_or_404(db, company_id)
    analysis = analysis_or_404(db, analysis_id)
    if not company or not analysis or analysis["company_id"] != company_id:
        return jsonify({"error": "invalid company/analysis"}), 404

    results = []
    for item in files:
        original = item.filename or "document"
        safe = secure_filename(original) or "document"
        saved = Path(current_app.config["UPLOAD_FOLDER"]) / f"{company_id}_{analysis_id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{safe}"
        item.save(saved)
        parsed = parse_document(saved)
        warnings = parsed.get("warnings") or []
        status = "processed_with_warning" if warnings else "processed"
        cur = db.execute(
            """INSERT INTO documents(company_id,analysis_id,original_name,doc_type,parser_name,sha256,status,parsed_json,uploaded_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (company_id, analysis_id, original, parsed.get("doc_type"), parsed.get("parser"), sha256_file(saved), status, json.dumps(parsed, ensure_ascii=False), now()),
        )
        imported = 0
        for row in parsed.get("monthly_rows") or []:
            numeric = ["commerce_revenue", "industry_revenue", "service_revenue", "payroll", "costs", "expenses", "current_tax_paid"]
            vals = [float(row.get(k) or 0) for k in numeric]
            db.execute(
                """INSERT INTO monthly_financials(analysis_id,month,commerce_revenue,industry_revenue,service_revenue,payroll,costs,expenses,current_tax_paid,source,created_at,updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,'document_import',?,?)
                   ON CONFLICT(analysis_id,month) DO UPDATE SET
                     commerce_revenue=excluded.commerce_revenue,industry_revenue=excluded.industry_revenue,service_revenue=excluded.service_revenue,
                     payroll=excluded.payroll,costs=excluded.costs,expenses=excluded.expenses,current_tax_paid=excluded.current_tax_paid,
                     source='document_import',updated_at=excluded.updated_at""",
                (analysis_id, row["month"], *vals, now(), now()),
            )
            imported += 1
        audit(db, action="upload", entity="document", entity_id=cur.lastrowid, company_id=company_id, analysis_id=analysis_id, new_value=original)
        results.append({"id": cur.lastrowid, "name": original, "status": status, "parser": parsed.get("parser"), "doc_type": parsed.get("doc_type"), "warnings": warnings, "monthly_rows_imported": imported})

    db.commit()
    return jsonify({"files": results})


@bp.get("/api/analyses/<int:analysis_id>/validations")
def validations(analysis_id):
    db = get_db()
    analysis = analysis_or_404(db, analysis_id)
    if not analysis:
        return jsonify({"error": "analysis not found"}), 404
    company = company_or_404(db, analysis["company_id"])
    rows = sync_validations(db, company, analysis, analysis_rows(db, analysis_id), document_types(db, analysis_id))
    db.commit()
    return jsonify([dict(x) for x in rows])


@bp.patch("/api/validations/<int:validation_id>")
def update_validation(validation_id):
    db = get_db()
    item = db.execute("SELECT * FROM validation_items WHERE id=?", (validation_id,)).fetchone()
    if not item:
        return jsonify({"error": "validation not found"}), 404
    p = request.get_json(silent=True) or {}
    status = p.get("status")
    if status not in {"pending", "validated", "resolved"}:
        return jsonify({"error": "invalid status"}), 400
    db.execute("UPDATE validation_items SET status=?,updated_at=? WHERE id=?", (status, now(), validation_id))
    audit(db, action="validate", entity="validation", entity_id=validation_id, company_id=item["company_id"], analysis_id=item["analysis_id"], field_name="status", old_value=item["status"], new_value=status)
    db.commit()
    return jsonify({"ok": True, "status": status})


@bp.post("/api/simulate")
def simulate():
    db = get_db()
    p = request.get_json(silent=True) or {}
    analysis_id = int(p.get("analysis_id") or 0)
    analysis = analysis_or_404(db, analysis_id)
    if not analysis:
        return jsonify({"error": "analysis not found"}), 404
    company = company_or_404(db, analysis["company_id"])
    monthly = analysis_rows(db, analysis_id)
    docs = document_types(db, analysis_id)
    validations = sync_validations(db, company, analysis, monthly, docs)
    result = calculate(dict(company), dict(analysis), [dict(x) for x in monthly], docs)
    # Persist human validation status separately; calculation returns current generated checks.
    result["validation_status_counts"] = {
        "pending": sum(1 for x in validations if x["status"] == "pending"),
        "validated": sum(1 for x in validations if x["status"] == "validated"),
        "resolved": sum(1 for x in validations if x["status"] == "resolved"),
    }
    cur = db.execute(
        """INSERT INTO simulations(company_id,analysis_id,engine_version,input_json,result_json,created_at)
           VALUES (?,?,?,?,?,?)""",
        (company["id"], analysis_id, ENGINE_VERSION, json.dumps({"source": "database", "analysis_id": analysis_id}), json.dumps(result), now()),
    )
    db.execute("UPDATE analyses SET status=?,updated_at=? WHERE id=?", ("preliminary" if result["blocking_validations"] else "review_ready", now(), analysis_id))
    audit(db, action="simulate", entity="simulation", entity_id=cur.lastrowid, company_id=company["id"], analysis_id=analysis_id, new_value=result.get("best_scenario", {}).get("key") if result.get("best_scenario") else None)
    db.commit()
    result["simulation_id"] = cur.lastrowid
    return jsonify(result)


@bp.get("/api/simulations/<int:simulation_id>")
def simulation_detail(simulation_id):
    db = get_db()
    row = db.execute(
        """SELECT s.*,c.legal_name,c.trade_name,c.identifier,a.title,a.fiscal_year
           FROM simulations s JOIN companies c ON c.id=s.company_id JOIN analyses a ON a.id=s.analysis_id WHERE s.id=?""",
        (simulation_id,),
    ).fetchone()
    if not row:
        return jsonify({"error": "simulation not found"}), 404
    d = dict(row)
    d["result"] = json.loads(d.pop("result_json"))
    d["input"] = json.loads(d.pop("input_json"))
    return jsonify(d)


@bp.get("/api/history/<int:company_id>")
def history(company_id):
    db = get_db()
    sims = db.execute(
        """SELECT s.id,s.analysis_id,s.engine_version,s.created_at,s.result_json,a.title
           FROM simulations s JOIN analyses a ON a.id=s.analysis_id WHERE s.company_id=? ORDER BY s.id DESC LIMIT 40""",
        (company_id,),
    ).fetchall()
    docs = db.execute("SELECT id,analysis_id,original_name,doc_type,parser_name,status,uploaded_at FROM documents WHERE company_id=? ORDER BY id DESC LIMIT 60", (company_id,)).fetchall()
    audit_rows = db.execute("SELECT * FROM audit_log WHERE company_id=? ORDER BY id DESC LIMIT 80", (company_id,)).fetchall()
    return jsonify({
        "simulations": [{**{k: r[k] for k in r.keys() if k != "result_json"}, "result": json.loads(r["result_json"])} for r in sims],
        "documents": [dict(x) for x in docs],
        "audit": [dict(x) for x in audit_rows],
    })


@bp.get("/api/rules/status")
def rules_status():
    db = get_db()
    sources = db.execute("SELECT * FROM regulatory_sources ORDER BY id").fetchall()
    rules = db.execute("SELECT * FROM scenario_rules ORDER BY regime,rule_name").fetchall()
    return jsonify({
        "engine_version": ENGINE_VERSION,
        "calculation_mode": "illustrative_public_portfolio",
        "production_tax_advice": False,
        "human_review_required": True,
        "sources": [dict(x) for x in sources],
        "rules": [dict(x) for x in rules],
    })


@bp.post("/api/reset-demo")
def reset_demo():
    # The public demo intentionally avoids destructive reset logic. Railway redeploy reseeds the database.
    return jsonify({"ok": True, "message": "This demo reseeds automatically on a fresh deployment. No destructive reset was performed."})
