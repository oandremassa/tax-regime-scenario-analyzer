# Business rules

This project demonstrates a rule-driven comparison workflow. It is not a tax compliance system.

## Input validation

- annual revenue must be greater than zero;
- payroll can be zero, but this creates a warning;
- service share plus commerce share should equal 100%;
- imported monthly CSV files must contain `month`, `revenue`, `payroll`, and `costs`.

## Scenario engine

The engine compares three generic representations of common Brazilian tax-regime concepts:

- Simplified Regime;
- Presumed Profit;
- Actual Profit.

The rates and formulas are intentionally simplified and are stored in code only to demonstrate architecture, calculation flow, validation and scenario ranking.

## Decision-support output

For each scenario, the application returns:

- estimated annual burden;
- effective rate;
- monthly equivalent;
- a short explanation of the model.

The lowest estimated scenario is highlighted, but the UI explicitly avoids presenting the result as professional tax advice.
