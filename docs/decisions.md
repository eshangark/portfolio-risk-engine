# Decisions

| ID | Decision | Rationale and consequence |
| --- | --- | --- |
| D01 | Mathematics-first C++ engine; Python reference precedes it | Gives independent oracles and clear domains before custom numerical code |
| D02 | Private GitHub development, private Streamlit target | Public code or market-data publication needs explicit direction |
| D03 | USD US ordinary stocks and unleveraged ETFs; long-only | Bounds financial/modeling scope; eligibility enforcement pending provider integration |
| D04 | Cash excluded initially, full contribution invested | Avoids an implicit all-cash optimum; whole-account cash must never be silently omitted |
| D05 | Sample covariance uses T-1; Ledoit–Wolf planned | Transparent baseline plus research-backed shrinkage; reconcile empirical normalization explicitly |
| D06 | Fixed-alpha shrinkage is a sensitivity reference | Do not mislabel it an estimated Ledoit–Wolf implementation |
| D07 | No sales, continuous purchases, optional post-contribution caps | Practical convex allocation; whole-share rounding deferred |
| D08 | Projected gradient with capped-simplex projection planned | Small auditable algorithm; independent solver validation remains required |
| D09 | Synthetic offline fixtures first | Reproducible tests without credentials, retention rights or live service failures |
| D10 | Float64, scale-relative PSD allowance; no material matrix repair | Singular valid covariance allowed; invalid correlation structures rejected |
| D11 | Zero volatility value allowed; standard gradient unavailable | Do not divide by zero or silently report a fabricated sensitivity |
| D12 | One complete foundation milestone in the initial setup | Keep full scope and later milestones explicit; no premature UI or invented results |
| D13 | No open-source license selected yet | Private development; owner can choose licensing before public release |
