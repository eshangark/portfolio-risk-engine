# Requirements to evidence

`Verified` means the stated local synthetic check passed. `Designed` is not implementation. See [status](status.md).

| ID | Requirement | Theory | Implementation / evidence | Status |
| --- | --- | --- | --- | --- |
| R01 | Private development repository | specification | GitHub repo and private visibility verified | Verified |
| R02 | Returns/sample covariance/PSD | paper/01-risk.md | reference.py; hand and NumPy covariance test | Verified reference |
| R03 | Risk, analytical gradient, attribution | paper/02-differentiation.md | reference.py; hand values, Euler and finite differences | Verified reference |
| R04 | Purchase normalization and transfers | paper/02-differentiation.md | dollar_gradient; multiple-step tests | Verified reference |
| R05 | Valid covariance-parameter sensitivity | paper/01-risk.md, paper/02-differentiation.md | fixed-alpha path and finite differences | Verified reference |
| R06 | Estimated shrinkage and window comparison | paper/01-risk.md | Ledoit–Wolf selected; coefficient fitting absent | Designed |
| R07 | C++ library and bindings | paper/04-architecture.md | cpp/README.md; no compiled engine | Pending M2 |
| R08 | Reverse-mode ownership, shared expressions, reset | paper/02-differentiation.md | tape contract only | Pending M3 |
| R09 | Alpaca backfill, incremental refresh, caching, pagination, retries | paper/04-architecture.md | provider contract only | Pending M4 |
| R10 | Freshness, calendar alignment, corporate actions | paper/04-architecture.md | complete-array rejection only; live/stale fixtures absent | Partial reference |
| R11 | Constrained allocation and feasibility | paper/03-optimization.md | purchase_bounds feasible/infeasible tests | Feasibility verified; solver pending |
| R12 | Projection, optimizer stopping, solver comparison | paper/03-optimization.md | formulation and diagnostics; no numerical solve | Pending M5 |
| R13 | Single/perfect correlation, singular/nearly singular, zero | paper/05-validation.md | test_reference.py named cases | Verified reference |
| R14 | Invalid dimensions/nonfinite/weights/covariance | paper/05-validation.md | rejection tests | Verified reference |
| R15 | Permutation, scaling and local vs exact decisions | paper/02-differentiation.md | tests and two_asset.py report | Verified reference |
| R16 | Private remotely hosted interface | paper/04-architecture.md | current hosting docs checked; no app | Pending M2 smoke / M6 product |
| R17 | Reproducible technical paper, sources and versioning | paper/README.md | 6 chapters, example JSON and hashes | Foundation complete; living document |
| R18 | Chronological practical validation and fair benchmarks | paper/05-validation.md | study design only | Pending M6 |
| R19 | CI, secure credentials, no holdings in source | README.md, AGENTS.md | tests.yml, .gitignore; remote run status in status.md | Configured |

All numerical tests are in [tests/test_reference.py](../tests/test_reference.py); the reference is [portfolio_risk/reference.py](../src/portfolio_risk/reference.py). This table must grow with actual test links when later work is implemented.
