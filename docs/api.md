# API reference

The browser UI is built entirely on the same JSON endpoints available to external clients.

## Context

### `GET /api/bootstrap`
Returns company list, selected company, analyses and engine version.

### `GET /api/dashboard`
Returns global workflow metrics, latest simulations and recent audit activity.

## Company master data

### `GET /api/companies`
List companies.

### `POST /api/companies`
Create a synthetic/demo company.

### `GET /api/companies/<id>`
Return company profile and analyses.

### `PATCH /api/companies/<id>`
Update fiscal master data. Relevant changes are added to the audit log.

## Analyses and monthly facts

### `POST /api/analyses`
Create a fiscal-year workspace.

### `GET /api/analyses/<id>`
Return company, analysis, monthly facts, documents, validations and latest simulation.

### `PUT /api/analyses/<id>/monthly`
Upsert the 12-month financial matrix.

## Evidence

### `POST /api/upload`
Multipart upload with `company_id`, `analysis_id` and one or more `files` values.

## Validation

### `GET /api/analyses/<id>/validations`
Regenerate and return control items.

### `PATCH /api/validations/<id>`
Set status to `pending`, `validated` or `resolved`.

## Scenarios

### `POST /api/simulate`
Body:

```json
{"analysis_id": 1}
```

Returns aggregate financials, generated validations, all three scenarios, tax components, assumptions, effective rates, scenario spread and current baseline.

### `GET /api/simulations/<id>`
Return one persisted simulation snapshot.

## Governance

### `GET /api/rules/status`
Returns public calculation-mode metadata, reference-source registry and illustrative rule metadata.
