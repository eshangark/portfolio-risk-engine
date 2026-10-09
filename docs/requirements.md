# Requirements to evidence

Theory is in the [PDF](paper/portfolio-risk-engine.pdf). Verification below refers to synthetic checks at commit `8438207`, [run 37956387933](https://github.com/eshangark/portfolio-risk-engine/actions/runs/37956387933), unless stated otherwise.

| ID | Requirement | Theory chapter | Implementation / evidence | Status |
| --- | --- | --- | --- | --- |
| R01 | Private repository | Scope | GitHub visibility verified; publication not authorized | Verified |
| R02 | Returns, covariance, PSD | 1, 5 | reference.py, estimation.py; reference/data tests | Verified synthetic |
| R03 | Risk, gradient, attribution | 2 | C++ engine; analytical/AD/NumPy tests | Verified synthetic |
| R04 | Dollar normalization and transfers | 2 | dollar_gradient; finite differences | Verified synthetic |
| R05 | Valid covariance sensitivity | 1, 2 | shrinkage_sensitivity; fixed-alpha path tests | Verified synthetic |
| R06 | Estimated shrinkage and windows | 1, 4 | Fitted Ledoit–Wolf normalization tests; app comparison | Estimator verified; live study pending |
| R07 | C++ and Python bindings | 4 | CMake, wheel installation on two Python versions | Verified Linux |
| R08 | Reverse-mode ownership and accumulation | 2 | Shared/reset/lifetime tests; native sanitizers | Verified covered cases |
| R09 | Backfill, pagination, retries, cache, incremental | 4 | data.py; mocked HTTP tests | Implemented except incremental refresh |
| R10 | Calendar, freshness, corporate actions | 4 | Adjacent-session returns and stale tests | Synthetic verified; actions pending |
| R11 | Constrained purchases and feasibility | 3 | allocate; no-sale/cap/zero-budget cases | Verified synthetic |
| R12 | Projection, convergence, independent solver | 3, 5 | Variational checks and OSQP comparison | Verified synthetic |
| R13 | Singular/zero/perfect correlation | 1, 5 | Reference and compiled test fixtures | Verified synthetic |
| R14 | Invalid inputs | 5 | Shape, nonfinite, weights, symmetry/PSD rejection | Verified covered cases |
| R15 | Invariances and exact/local comparisons | 2, 5 | Reference tests; examples; app | Verified synthetic |
| R16 | Private hosted interface | 4 | App and deployment config; AppTest | Hosting pending |
| R17 | Reproducible sourced technical paper | All | Standalone LaTeX, PDF, measured JSON reports | Compiled; ongoing research |
| R18 | Chronological studies and fair benchmarks | 5 | Study design | Pending |
| R19 | CI and credentials handling | 4, 5 | tests.yml; ignored secrets; server-side adapter | CI verified; live secrets pending |

Source: [C++](../cpp/src/engine.cpp), [reference](../src/portfolio_risk/reference.py), [data](../src/portfolio_risk/data.py), [estimation](../src/portfolio_risk/estimation.py), [interface](../app/streamlit_app.py). Tests: [reference](../tests/test_reference.py), [engine](../tests/test_engine.py), [data](../tests/test_data.py), [app](../tests/test_app.py).

Integration update verified in [run 37958614693](https://github.com/eshangark/portfolio-risk-engine/actions/runs/37958614693),
commit `aeea037`: 34 tests on both Python versions and native sanitizers passed.
R09 now audits incremental changes from
complete snapshots; overlap-only network refresh remains deferred. R10 adds
independent event-return arithmetic. R18 adds `chronological_study`, tests proving
future observations cannot change the first fitted allocation, and a repeated
validated-API benchmark, measured on Linux. The chronological runner completed 72
synthetic evaluations. Live evidence remains pending credentials. See
[live setup](live-setup.md) for the concrete account and deployment steps.
