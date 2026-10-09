# Project specification

## Research question and scope

Explain estimated portfolio volatility, attribute it, differentiate meaningful decisions, and assess the stability of conclusions across covariance choices. The numerical engine is the main deliverable. Teach enough linear algebra, statistics, calculus, and numerical optimization for a calculus student to reproduce the arguments.

Initial supported financial universe: USD-priced US-listed ordinary stocks and unleveraged ETFs; positive prices, nonnegative positions, no borrowing, no shorting, no derivatives, no foreign-exchange conversion. Delisted symbols, identifier changes, leveraged/inverse funds, and complex corporate actions require explicit validation before inclusion. Provider eligibility checks arrive with ingestion.

Cash is excluded from the initial risky-asset model and from eligible purchase destinations. A contribution must be fully invested among included assets. Do not silently omit existing cash and label the result whole-account risk. A future explicit zero-risk cash sleeve needs a separate decision: otherwise minimum variance can choose all cash. Ignore fees, taxes, spreads, execution constraints and liquidity impact; allocations permit fractional shares.

Inputs will be tickers with share quantities, dollar holdings, or hypothetical normalized weights. Share valuation uses recent unadjusted market observations with timestamps and feed labels. Covariance uses completed, consistently adjusted historical daily observations. These are distinct products.

## Milestones and acceptance

1. **Foundation:** sourced mathematical paper draft, project contracts, hand-worked case, runnable NumPy reference, meaningful offline tests, requirements table and private repository workflow.
2. **Build/deployment:** C++17 library, pybind11 import, reproducible Linux build in CI, synthetic Streamlit smoke page hosted privately. Verify server restart works while the developer machine is off.
3. **Differentiation:** owned tape, shared-node accumulation, reset and lifetime checks, composed purchase derivatives, risk contributions; analytical and step-swept finite-difference comparisons.
4. **Data/estimation:** provider interface and Alpaca adapter, credentials server-side, pagination/retries/cache/incremental refresh, calendar alignment, adjustment verification, estimated Ledoit–Wolf covariance and window comparisons.
5. **Allocation:** capped-simplex projection, projected gradient, feasibility and stopping diagnostics, comparison with an established QP solver using objective and residuals, model-sensitivity study.
6. **Integration/research:** accessible interface, documented user tasks, chronological evaluation without look-ahead, reproducible figures and tables, fair NumPy benchmarks and completed technical paper.

Each milestone updates code, theory, tests and status together. A numerical result is not evidence of financial forecasting skill. Conclusions across models are sensitivity results, never confidence intervals without a separately justified statistical procedure.
