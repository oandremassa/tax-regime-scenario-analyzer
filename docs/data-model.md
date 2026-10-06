# Data model

## companies
Synthetic fiscal master data: identifier, legal/trade names, CNAE/activity, municipality/state, current regime, service-annex reference, ISS/ICMS assumptions and notes.

## analyses
One tax-planning review for one company, with fiscal year, period, status and source notes.

## monthly_financials
Twelve-month structured facts: commerce, industry, services, payroll, costs, expenses and current-tax baseline.

## documents
Evidence intake metadata: original filename, document type, parser, SHA-256 reference, processing status and structured parser output.

## validation_items
Human review/control layer. Generated checks persist with severity and status (`pending`, `validated`, `resolved`).

## simulations
Immutable-style calculation snapshots containing engine version, input metadata, complete result JSON and timestamp.

## audit_log
Relevant workflow actions and before/after values.

## regulatory_sources / scenario_rules
Governance metadata. These tables make it explicit that fiscal references and software behavior are separate concerns.
