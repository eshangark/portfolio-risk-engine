# Numerical validation and historical evaluation

The engine minimizes a convex fixed-covariance objective. It does not optimize
expected returns or establish forecasting skill. Testing supplies evidence for
covered domains; it cannot prove arbitrary floating-point inputs are reliable.

## Independent checks

The suite checks analytical formulas against the custom reverse-mode tape,
NumPy and central finite differences; Euler risk attribution; dollar-normalization
derivatives; permutation and scale invariance; singular/zero covariance; negative
risk contributions; invalid inputs; tape ownership and repeated reverse passes.
Native address/undefined-behavior sanitizers exercise C++ lifetimes and projection.

The expanded stress suite includes 48 random risk instances at 2, 3, 8 and 16
assets. It compares 48 allocation solves (24 covariance/constraint instances,
both analytical and AD modes) with OSQP, including rank-one covariances. It also
checks a separate convex certificate: for gradient g at feasible w and v minimizing
g·v over the feasible set, `g·(w-v)` bounds objective suboptimality from above.
The certificate uses a greedy linear oracle, not the projection routine.

Adversarial projection tests cover score differences up to 1e300, budgets from
1e-200 to 1e200, huge common offsets and capacities whose float64 sum overflows.
The audit fixed full-score-range scaling by selecting a capacity pivot, clipping
necessarily saturated/zero scores and scaling by the budget. Covariance and
dollar-gradient scale checks span 1e-200 to 1e200. Values outside representable
spectral/derivative domains may be rejected; convergence is always reported.

## Backtest contract

`contribution_backtest` starts with 1,000 hypothetical dollars, divided equally.
Every 21 observations, it adds 200 dollars using Ledoit-Wolf covariance fitted
only on the preceding 126 observations. All purchases are nonnegative; holdings
drift with each subsequent daily simple return. An equal-dollar-purchase baseline
uses identical deposit dates and amounts. No fees, spreads, taxes or execution
constraints are modeled. No orders or brokerage endpoints are involved.

For a deposit C before daily return r, pre-return holdings are `h+x` and ending
holdings are `(h+x)*(1+r)`. Daily portfolio return is ending/pre-return wealth
minus one. The product of these return factors is a time-weighted index; deposits
therefore do not masquerade as returns. Volatility uses sample daily standard
deviation times sqrt(252); drawdown uses that index and includes its initial value.
Terminal wealth includes deposits and is reported separately. Zero-return and
constant-common-return fixtures have independently known ledger outcomes.
Future-only edits must leave prior decisions and ledger entries exactly unchanged.
Inputs are made contiguous to avoid layout-dependent BLAS reduction differences.

Missing return dates suppress the hosted backtest. Revised provider histories,
selected surviving tickers and unverified dividend conventions mean the evaluation
is not a point-in-time or survivorship-free investment study. Hyperparameters are
fixed before evaluation; these examples are not a search for a winning strategy.

The separate `chronological_study` compares forecast and subsequent 21-observation
variance at independent fixed-holdings cutoffs. It is not a cumulative backtest.

## Reproduce

```sh
python -m pip install '.[test,app]'
python -m unittest discover -s tests -v
python -m examples.backtest_report --output work/backtest-report.json
python -m examples.research_report --output work/research-report.json
```

The backtest report uses four Gaussian regimes, four assets and seed 91026. This
is a stress simulation, not observed market performance. CI stores full reports
as artifacts. Raw market data, API caches, credentials and personal portfolios
are excluded from the tracked tree.

## Historical evidence

[Run 37997031520](https://github.com/eshangark/portfolio-risk-engine/actions/runs/37997031520)
at `cb737b9b` passed all 42 tests on Python 3.10 and 3.12, native sanitizers,
the four-regime backtest, chronological study and benchmarks. The initial
expanded run correctly failed the exact-prefix backtest check; contiguous input
layout fixed it without changing that expectation. The synthetic backtest
evaluated 882 observations and 42 contributions. Optimized / equal-purchase
volatility was 23.3873% / 23.2907%, drawdown -38.0320% / -37.0318%, and
time-weighted return 1.3306% / 2.3450%. This example shows that fitted minimum
variance does not guarantee better realized outcomes. [Recorded summary](results/backtest-summary.json).

[Run 37958614693](https://github.com/eshangark/portfolio-risk-engine/actions/runs/37958614693)
at `aeea037` passed the earlier 34-test suite on Python 3.10 and 3.12 and native
sanitizers. [Measured API benchmarks](results/benchmark.json) include validation,
eigendecomposition and bindings, with source/environment identity. At 50 assets,
custom AD was slower than NumPy; no universal speedup is claimed.

At `8da7a371`, hosted IEX-adjusted SPY/BND history produced 379 common returns
through 2026-10-09, no dropped dates, and 36 chronological evaluations across six
test blocks. Mean calibration ratios (sample / Ledoit-Wolf) were 0.9040 / 0.8344
(63 observations), 1.0251 / 0.9666 (126), and 1.2418 / 1.1551 (252). The dataset
identity was `2a3c00006e0e1b8b35309c375b0c00989d291c180d78ca569382c371e9905080`.
This short two-asset example cannot establish estimator superiority.

The extended hosted run at `cb737b9b` used 1,513 complete IEX-adjusted returns
for SPY/BND/GLD/QQQ, retrieved `2026-10-09T22:05:14.729587+00:00`.
The cumulative backtest evaluated 1,387 observations from 2021-04-05 through
2026-10-09, with 67 contributions totaling 13,400 dollars. It completed every
solve and had no dropped return dates.

| Measure | Minimum estimated variance | Equal-dollar purchases |
| --- | ---: | ---: |
| Terminal wealth, including deposits | $17,738.59 | $23,078.07 |
| Time-weighted return | 31.99% | 93.75% |
| Annualized realized volatility | 7.20% | 12.27% |
| Maximum drawdown | -18.66% | -21.70% |

The minimum-variance policy had lower realized volatility and drawdown but also
lower return and terminal wealth on this chosen history. The independent
fixed-holdings study completed 360 evaluations over 60 test blocks. Mean
calibration ratios ranged from 1.1366 to 1.1975, indicating underestimation
of subsequent variance on average in these groups. No general superiority is
inferred. [Aggregate provenance and results](results/live-evaluation-summary.json).

## Practical boundaries

USD US ordinary stocks and unleveraged ETFs, long-only, fractional purchases,
no cash sleeve, options, leverage or sales. Eligible assets currently require
user confirmation. SIP entitlement, live corporate-action convention checks,
point-in-time histories, trading costs and data redistribution rights remain
separate limitations. The repository and hosted app remain private. No
open-source license has been selected.
