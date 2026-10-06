# Case study

## Context

The project started from a process problem rather than a coding exercise. Financial and operational information was spread across spreadsheets and manual routines, while scenario comparisons were difficult to reproduce and review later.

The goal of the public rebuild is to show how I translated that kind of workflow into a small data application without exposing production information.

## Main problems mapped

- company information was not treated as a consistent master dataset;
- financial inputs could arrive in different files and formats;
- calculations depended on manual consolidation;
- validation issues were easy to miss;
- previous simulations were difficult to trace;
- management needed a clearer summary instead of another spreadsheet with raw formulas.

## Solution approach

I separated the workflow into four layers:

1. **Company master data** — one structured record per company.
2. **Financial assumptions** — annual revenue, payroll, costs and business mix.
3. **Scenario engine** — a dedicated calculation module instead of formulas embedded in the interface.
4. **Decision-support output** — comparable annual burden, effective rate, monthly equivalent and validation notes.

A small CSV ingestion step was added to represent the transition from operational spreadsheets to structured application data.

## What I would change for production

A production version would require validated tax rules, role-based permissions, encrypted storage, a production database, document-level audit trails, regulatory versioning and review by qualified tax professionals. Those elements are intentionally outside the scope of this public repository.

## Portfolio focus

The value of this project is in the workflow design: data modeling, validation, traceability, API structure and translating a real operational problem into software that is easier to use and review.
