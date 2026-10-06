CREATE TABLE IF NOT EXISTS companies (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  identifier TEXT NOT NULL UNIQUE,
  legal_name TEXT NOT NULL,
  trade_name TEXT,
  cnae TEXT,
  city TEXT,
  state TEXT,
  current_regime TEXT,
  service_annex TEXT,
  iss_rate REAL DEFAULT 0,
  icms_rate REAL DEFAULT 0,
  notes TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS analyses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  company_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  fiscal_year INTEGER NOT NULL,
  period_start TEXT NOT NULL,
  period_end TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft',
  source_note TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS monthly_financials (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  analysis_id INTEGER NOT NULL,
  month TEXT NOT NULL,
  commerce_revenue REAL NOT NULL DEFAULT 0,
  industry_revenue REAL NOT NULL DEFAULT 0,
  service_revenue REAL NOT NULL DEFAULT 0,
  payroll REAL NOT NULL DEFAULT 0,
  costs REAL NOT NULL DEFAULT 0,
  expenses REAL NOT NULL DEFAULT 0,
  current_tax_paid REAL NOT NULL DEFAULT 0,
  source TEXT NOT NULL DEFAULT 'manual',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(analysis_id, month),
  FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS documents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  company_id INTEGER NOT NULL,
  analysis_id INTEGER,
  original_name TEXT NOT NULL,
  doc_type TEXT,
  parser_name TEXT,
  sha256 TEXT,
  status TEXT NOT NULL,
  parsed_json TEXT,
  uploaded_at TEXT NOT NULL,
  FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
  FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS validation_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  company_id INTEGER NOT NULL,
  analysis_id INTEGER,
  code TEXT NOT NULL,
  title TEXT NOT NULL,
  detail TEXT,
  severity TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  source_note TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(company_id, analysis_id, code),
  FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
  FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS simulations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  company_id INTEGER NOT NULL,
  analysis_id INTEGER NOT NULL,
  engine_version TEXT NOT NULL,
  input_json TEXT NOT NULL,
  result_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
  FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  company_id INTEGER,
  analysis_id INTEGER,
  action TEXT NOT NULL,
  entity TEXT NOT NULL,
  entity_id INTEGER,
  field_name TEXT,
  old_value TEXT,
  new_value TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS regulatory_sources (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  jurisdiction TEXT,
  topic TEXT,
  version TEXT,
  status TEXT NOT NULL,
  url TEXT,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scenario_rules (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  regime TEXT NOT NULL,
  rule_name TEXT NOT NULL,
  rule_value REAL,
  unit TEXT,
  status TEXT NOT NULL,
  effective_from TEXT,
  effective_to TEXT,
  updated_at TEXT NOT NULL
);
