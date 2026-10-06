# Case study — accounting process improvement

## Operational challenge

A tax comparison can look like a spreadsheet exercise, but the practical workflow is broader: client master data may be incomplete, source documents arrive in different formats, financial periods are inconsistent, accounting and fiscal information must be reconciled, and the final result needs to be explainable to both specialists and decision-makers.

The portfolio case therefore focuses on **workflow quality** as much as calculation output.

## Product response

The application centralizes company master data, a 12-month financial matrix and source-document intake. It makes missing or inconsistent context visible through a validation center before exposing the three-regime comparison. The final result is available both as an analyst-facing component breakdown and an executive report.

## Why the three regimes are always visible

A comparison product is easier to interpret when the output structure is consistent. Even when one scenario is mathematically unattractive, keeping Simples Nacional, Lucro Presumido and Lucro Real in the same presentation helps users understand the magnitude and composition of the alternatives.

## Why 12 months matter

Month-only comparisons can overreact to seasonality. The public rebuild therefore seeds and expects a complete fiscal-year view, while explicitly flagging incomplete periods.

## Why document history matters

A scenario is more defensible when users can see which evidence was uploaded, which parser handled it, whether the file generated warnings, and when the calculation was created. This is why documents, simulations and audit events are modeled as first-class records rather than temporary UI state.

## Public reconstruction

The original business context is not copied into this repository. The public version preserves the engineering pattern — inputs, evidence, controls, scenario transparency and auditability — using fictional companies, synthetic financial values and an illustrative calculation engine.
