# Architecture

## Application flow

1. **Company Registry** stores the fiscal profile used by an analysis.
2. **Analysis Workspace** defines one fiscal-year review and holds monthly structured facts.
3. **Data Sources** ingest supporting evidence and attach parser/status/hash metadata.
4. **Validation Center** generates and tracks blocking/high/medium review items.
5. **Scenario Engine** receives company profile + 12-month data + document context and returns three comparable models.
6. **Executive Report** converts the latest simulation into a print-ready summary.
7. **History & Audit** preserves simulations, document intake and relevant changes.

## Backend layers

- `routes.py`: HTTP/API orchestration.
- `db.py`: SQLite connection lifecycle.
- `parsers.py`: document classification and safe structured extraction.
- `engine.py`: deterministic scenario calculations and generated validation rules.
- `seed.py`: synthetic portfolio demo state.
- `schema.sql`: relational model.

## Persistence model

The database keeps master data, analyses, monthly facts, documents, validation states, simulation snapshots, audit events, regulatory-source metadata and illustrative rule metadata separate. That separation is intentional: changing a company master-data field should not erase the history of a simulation already performed.

## Production evolution

A production-grade architecture would add authentication/RBAC, PostgreSQL, migrations, encrypted object storage, background file-processing jobs, monitored fiscal-rule services, approvals, retention policies, backups, observability and formal security controls.
