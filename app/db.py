import sqlite3
from flask import current_app

SCHEMA = """
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_code TEXT UNIQUE NOT NULL,
    legal_name TEXT NOT NULL,
    sector TEXT NOT NULL,
    city TEXT,
    state TEXT,
    current_regime TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    reference_year INTEGER NOT NULL,
    annual_revenue REAL NOT NULL DEFAULT 0,
    payroll REAL NOT NULL DEFAULT 0,
    operating_costs REAL NOT NULL DEFAULT 0,
    service_share REAL NOT NULL DEFAULT 0,
    commerce_share REAL NOT NULL DEFAULT 0,
    source_note TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS simulations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    analysis_id INTEGER NOT NULL,
    engine_version TEXT NOT NULL,
    result_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(company_id) REFERENCES companies(id),
    FOREIGN KEY(analysis_id) REFERENCES analyses(id)
);

CREATE TABLE IF NOT EXISTS imports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    file_name TEXT NOT NULL,
    rows_loaded INTEGER NOT NULL DEFAULT 0,
    annual_revenue REAL NOT NULL DEFAULT 0,
    annual_payroll REAL NOT NULL DEFAULT 0,
    annual_costs REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY(company_id) REFERENCES companies(id)
);
"""


def connect(path=None):
    db_path = path or current_app.config["DATABASE_PATH"]
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_db(path):
    with sqlite3.connect(path) as con:
        con.executescript(SCHEMA)
        con.commit()
