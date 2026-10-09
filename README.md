# Portfolio Risk Engine

A mathematics-first C++17 and Python engine for portfolio risk, automatic differentiation and constrained contribution allocation.

**What drives estimated portfolio risk, how does a decision change it, and how dependent is the answer on the model?**

The compiled engine evaluates volatility and risk contributions, differentiates dollar normalization with a custom reverse-mode tape, and allocates a new contribution using projected gradient on a capped simplex. Python supplies independent reference calculations, covariance estimation, an Alpaca data adapter and a Streamlit interface.

- [Technical paper (PDF)](docs/paper/portfolio-risk-engine.pdf) and [LaTeX source](docs/paper/portfolio-risk-engine.tex)
- [Measured numerical results](docs/results/engine-report.json)
- [Validation run](https://github.com/eshangark/portfolio-risk-engine/actions/runs/37997031520): 42 tests on Python 3.10 and 3.12, native C++ sanitizers, independent solver certificates, cash-flow backtest and repeated API benchmarks
- [Benchmark results](docs/results/benchmark.json): includes cases where custom AD is slower than NumPy
- [Validation and backtest methodology](docs/validation.md)

## Build and run

Requires Python 3.10+, a C++17 compiler, CMake and Eigen3. On Debian/Ubuntu, install `build-essential libeigen3-dev`; on macOS, install Apple's command-line developer tools and Eigen3 first. The package build supplies CMake through scikit-build-core when needed.

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install '.[test,app]'
python -m unittest discover -s tests -v
python -m examples.engine_report --output work/engine-report.json
streamlit run app/streamlit_app.py
```

The synthetic app needs no credentials. [App setup](app/README.md) describes server-side Alpaca secrets and private hosting configuration. The [private hosted app](https://portfolio-risk-eng-fwywewfctjzvsqsxvhmumt.streamlit.app/) and IEX history retrieval were verified on 2026-10-09; see [validation](docs/validation.md) for the methodology and results.

[Live setup and verification](docs/live-setup.md) gives the account steps, server
secrets template and read-only API probe. Requests respect a conservative history
cutoff; explicit refresh audits full snapshots for added, removed and revised bars.
Caches are isolated by session. Dividend/split audits compare provider returns
against independently supplied event economics.

Research and measurement commands (synthetic unless `live_report` is selected):

```sh
python -m examples.research_report --output work/research-report.json
python -m examples.backtest_report --output work/backtest-report.json
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m examples.benchmark --output work/benchmark.json
python -m examples.live_report --study --output work/live-study.json
```

## Mathematics

For fixed symmetric PSD covariance $\Sigma$ and long-only weights summing to one:

$$v=w^T\Sigma w,\qquad \sigma=\sqrt{v},\qquad \nabla_w\sigma=\Sigma w/\sigma\quad(\sigma>0).$$

Risk contribution is $RC_i=w_i\partial_i\sigma$, with $\sum_i RC_i=\sigma$. Adding dollars changes all normalized weights. The allocator minimizes the variance of $(h+x)/(V+B)$ with $x\ge0$, $\sum_i x_i=B$, and post-contribution concentration caps. Its output includes feasibility and projected-gradient residuals, iteration count and convergence status.

In the worked example, weights $(0.6,0.4)$ and covariance entries $(.04,.006;.006,.01)$ give **13.74045% volatility**. Asset A holds 60% of capital but contributes **83.89831%** of volatility. A $200 contribution to holdings $(600,400)$ with 60% caps is allocated entirely to B, yielding weights $(.5,.5)$ and variance .0155. Inputs are hypothetical annual quantities.

## Capabilities and remaining work

| Area | Implemented | Remaining validation |
| --- | --- | --- |
| C++ / autodiff | Risk, attribution, dollar and shrinkage sensitivities; owned tape; scale tests; benchmark runner | Extreme scale limits; isolated kernel/binding timings |
| Allocation | Capped-simplex projection, analytical/AD gradients, OSQP comparison; hosted two-asset study | Broader allocation stability study |
| Estimation | Sample covariance, fitted Ledoit–Wolf, explicit normalization; 36 hosted chronological evaluations | Broader estimation-quality study |
| Data | Pagination, bounded retries, audited snapshot refresh, session alignment, stale-price checks; live IEX history verified | SIP entitlement, event verification, overlap-only network refresh |
| Interface | Private hosted C++ operation, live market workflow, estimation comparisons and chronological study controls | Wider hosted interaction coverage |

Scope: USD US stocks and unleveraged ETFs; long-only, continuous dollar purchases, no cash sleeve. Asset eligibility currently requires user confirmation. Historical covariance is a model estimate, not a forecast guarantee. No trading, brokerage execution or return promises. Keep credentials, holdings and market-data caches outside commits. The repository remains private; no open-source license has been selected.

## Rebuild the paper

The PDF is the reading copy; the standalone `.tex` is the editable source. With Tectonic installed:

```sh
tectonic docs/paper/portfolio-risk-engine.tex
```

The tracked tree contains source, tests, setup documentation and research evidence.
