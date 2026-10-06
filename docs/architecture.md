# Architecture

The application is intentionally small and easy to inspect.

```text
Browser
  |
  | HTTP / JSON
  v
Flask application
  |-- routes.py      API and web routes
  |-- engine.py      scenario calculation and validation
  |-- db.py          SQLite schema and connections
  |-- seed.py        synthetic demo data
  |
  v
SQLite
  |-- companies
  |-- analyses
  |-- simulations
  |-- imports
```

## Design choices

- **Flask** keeps the backend compact and readable.
- **SQLite** is enough for a portfolio demo and requires no external service.
- **Vanilla JavaScript** keeps the frontend dependency-free.
- **Persisted simulations** provide basic auditability.
- **CSV import** represents a lightweight ingestion step from operational spreadsheets.
- **Synthetic seed data** makes the repository safe to run publicly.

## Public-safe boundary

No production database, client files, credentials, names, registration numbers or proprietary calculation tables are included. The scenario formulas are deliberately simplified.
