# Illustrative business rules

This file documents the public portfolio model, not Brazilian tax advice.

## Simples Nacional proxy

A schedule-based effective-rate function is applied independently to commerce, industry and services. Services use an Annex III / Annex V proxy based on a Factor R threshold. The component breakdown is an illustrative allocation of the total modeled burden.

## Lucro Presumido proxy

The engine separates service and trade/industry revenue, applies different presumed IRPJ/CSLL bases, includes PIS/COFINS gross rates, company-entered ISS, and a simplified ICMS gross proxy.

## Lucro Real proxy

The engine uses an operating-profit proxy as the IRPJ/CSLL base, adds gross PIS/COFINS before credits, ISS and a simplified ICMS proxy. It does not model real-world additions/exclusions, tax losses, credits or special regimes.

## Generated validations

Examples include:

- incomplete 12-month period;
- missing CNAE/activity;
- service revenue without confirmed ISS;
- missing service-annex review;
- missing current regime;
- zero revenue;
- unusually high payroll;
- mixed commerce/services profile;
- missing DRE evidence;
- missing PGDAS evidence when the current regime is Simples Nacional.

## Human review

A generated validation may be marked `validated` by the demo user. The platform still keeps the original generated control and audit event visible.
