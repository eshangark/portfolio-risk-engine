# Decisions

| ID | Decision | Rationale and consequence |
| --- | --- | --- |
| D01 | Mathematics-first C++ engine; Python reference precedes it | Gives independent oracles and clear domains before custom numerical code |
| D02 | Private GitHub development, private Streamlit target | Public code or market-data publication needs explicit direction |
| D03 | USD US ordinary stocks and unleveraged ETFs; long-only | Bounds financial/modeling scope; eligibility enforcement pending provider integration |
| D04 | Cash excluded initially, full contribution invested | Avoids an implicit all-cash optimum; whole-account cash must never be silently omitted |
| D05 | Sample covariance uses T-1; fitted Ledoit–Wolf uses T | Both implemented; empirical normalization explicitly reconstructed in tests |
| D06 | Fixed-alpha shrinkage is a sensitivity reference | Do not mislabel it an estimated Ledoit–Wolf implementation |
| D07 | No sales, continuous purchases, optional post-contribution caps | Practical convex allocation; whole-share rounding deferred |
| D08 | Projected gradient with capped-simplex projection | Implemented in scaled post-contribution weight coordinates; checked against OSQP objectives |
| D09 | Synthetic offline fixtures first | Reproducible tests without credentials, retention rights or live service failures |
| D10 | Float64, scale-relative PSD allowance; no material matrix repair | Singular valid covariance allowed; invalid correlation structures rejected |
| D11 | Zero volatility value allowed; standard gradient unavailable | Do not divide by zero or silently report a fabricated sensitivity |
| D12 | One complete foundation milestone in the initial setup | Keep full scope and later milestones explicit; no premature UI or invented results |
| D13 | No open-source license selected yet | Private development; owner can choose licensing before public release |
| D14 | LaTeX source and PDF replace paper Markdown | Owner prefers a PDF; keep editable source for reproducible rebuilding |
| D15 | Complete engine validation before hosted access | Linux CI validates compiled code while hosting remains a separate unverified account step |
| D16 | Re-fetch adjusted history on cache expiry | Avoid incorrect incremental splicing until historical revision handling is validated |
| D17 | Retain planning files during development | Owner will specify when to remove them before public release |
| D18 | Audit complete snapshots for incremental changes | Short overlaps cannot detect arbitrary old revisions; network-volume optimization is deferred rather than claiming revision safety |
| D19 | Chronological independent contribution decisions | Fixed initial holdings at each cutoff separate variance calibration from cumulative trading or return claims |
| D20 | Benchmark full validated APIs first | Includes eigendecomposition and binding costs; does not pretend these are isolated kernel timings |
