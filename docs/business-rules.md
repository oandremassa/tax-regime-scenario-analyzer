# Illustrative business rules

This file documents the public portfolio model, not Brazilian tax advice.

## Brazilian Simplified Tax Regime proxy

A schedule-based effective-rate function is applied independently to commerce, industry and services. Services use a Service Tier III / Service Tier V proxy based on a Factor R threshold. The component breakdown is an illustrative allocation of the total modeled burden.

## Presumed Profit Regime proxy

The engine separates service and trade/industry revenue, applies different presumed Corporate Income Tax / Social Contribution bases, includes federal social-contribution gross rates, company-entered Service Tax, and a simplified State VAT gross proxy.

## Actual Profit Regime proxy

The engine uses an operating-profit proxy as the Corporate Income Tax / Social Contribution base, adds gross federal social contributions before credits, Service Tax and a simplified State VAT proxy. It does not model real-world additions/exclusions, tax losses, credits or special regimes.

## Generated validations

Examples include:

- incomplete 12-month period;
- missing business activity code;
- service revenue without confirmed Service Tax rate;
- missing service-tier review;
- missing current regime;
- zero revenue;
- unusually high payroll;
- mixed commerce/services profile;
- missing income statement evidence;
- missing simplified-regime filing evidence when the current regime is the Brazilian Simplified Tax Regime.

## Human review

A generated validation may be marked `validated` by the demo user. The platform still keeps the original generated control and audit event visible.
