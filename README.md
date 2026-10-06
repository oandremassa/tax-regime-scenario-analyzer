# Tax Regime Scenario Analyzer

A small full-stack data application for organizing company assumptions, validating financial inputs and comparing tax scenarios in a single workflow.

This repository is an **anonymized portfolio rebuild** inspired by a real process-improvement challenge in an accounting environment. All company names, identifiers and figures in this public version are fictional or synthetic.

> The calculation engine is intentionally simplified. This project is for software/data portfolio purposes only and must not be used for tax, accounting or legal advice.

## What problem does it solve?

The original operational problem was not only calculation. The larger issue was fragmented information: company master data in one place, financial inputs in spreadsheets, manual scenario comparisons and little history of what had been calculated before.

This project turns that workflow into a compact application with structured inputs, validation, repeatable calculations and saved simulation history.

## Features

- synthetic company master data;
- annual financial input form;
- CSV import for monthly revenue, payroll and costs;
- input validation and data-quality warnings;
- comparison of three illustrative tax scenarios;
- effective-rate and annual-burden view;
- saved simulation history;
- lightweight REST API;
- SQLite persistence;
- automated tests with Pytest;
- Docker and Gunicorn support;
- GitHub Actions test workflow.

## Stack

**Backend:** Python, Flask, SQLite  
**Frontend:** HTML, CSS, JavaScript  
**Testing:** Pytest  
**Deployment:** Docker, Gunicorn

## Project structure

```text
tax-regime-scenario-analyzer/
├── app/
│   ├── __init__.py
│   ├── db.py
│   ├── engine.py
│   ├── routes.py
│   ├── seed.py
│   ├── static/
│   │   ├── app.js
│   │   └── styles.css
│   └── templates/
│       └── index.html
├── data/
│   └── monthly_financials.csv
├── docs/
│   ├── architecture.md
│   ├── business-rules.md
│   └── data-model.md
├── tests/
│   ├── test_api.py
│   └── test_engine.py
├── .github/workflows/tests.yml
├── Dockerfile
├── Procfile
├── requirements.txt
└── run.py
```

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Open `http://127.0.0.1:5000`.

The database is created automatically and seeded with four fictional companies.

## Try the CSV import

Use the sample file:

```text
data/monthly_financials.csv
```

The importer expects these columns:

```text
month,revenue,payroll,costs
```

After import, the annual revenue, payroll and cost fields are filled with the aggregated CSV values.

## API examples

Health check:

```http
GET /api/health
```

Companies:

```http
GET /api/companies
GET /api/companies/1
POST /api/companies
```

Analysis and simulation:

```http
POST /api/analyses
POST /api/simulate
GET /api/history/1
```

## Run tests

```bash
pytest -q
```

## Docker

```bash
docker build -t tax-scenario-analyzer .
docker run -p 8000:8000 tax-scenario-analyzer
```

Open `http://127.0.0.1:8000`.

## What this project demonstrates

- translating an operational process into a data model;
- separating input, calculation and presentation layers;
- basic data validation and traceability;
- scenario comparison for decision support;
- building a usable interface on top of a small API;
- keeping public portfolio data separate from real client data.

## Public-data note

No real accounting-firm database, client document, company registration number, credential or proprietary tax table is included in this repository. The demo dataset exists only to reproduce the workflow safely.

## License

MIT
