# Portfolio Risk Engine

**A mathematics-first research project in portfolio risk, sensitivity, and constrained allocation.**

> What drives a portfolio's estimated risk, how does a decision change it, and how dependable is that conclusion?

The intended centerpiece is a C++ numerical engine with custom reverse-mode automatic differentiation and constrained quadratic optimization. Python handles market-data preparation, covariance estimation, independent reference calculations, and bindings. Streamlit will expose the engine through a private hosted interface.

**Current milestone: mathematical foundation and independently runnable NumPy reference.** C++, automatic market data, the numerical optimizer, and hosted UI are pending. This is a staged start to the full project, not the final engine.

## Start here

- [Technical paper](docs/paper/README.md): derivations, examples, assumptions, and research sources.
- [Project specification](docs/specification.md): scope and completion criteria.
- [Verified status](docs/status.md) and [decisions](docs/decisions.md).
- [Requirements and evidence](docs/requirements.md).
- [Original project brief](docs/project-brief.md).

## Run the first milestone

Python 3.10 or newer:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install .
python -m unittest discover -s tests -v
python -m examples.two_asset --output work/two-asset.json
```

Tests require only NumPy and Python's standard library. All fixtures are synthetic and need no API credentials. GitHub Actions is configured to repeat the reference checks on Python 3.10 and 3.12; a configured workflow is not evidence of a successful remote run.

## The mathematics

For fixed symmetric positive-semidefinite covariance $\Sigma$, and long-only weights $w$ summing to one:

$$v=w^T\Sigma w,\qquad \sigma=\sqrt{v},\qquad \nabla_w\sigma=\frac{\Sigma w}{\sigma}\quad(\sigma>0).$$

Risk contribution is $RC_i=w_i\partial_i\sigma$, and $\sum_i RC_i=\sigma$. Adding dollars to a holding changes every normalized weight; the reference differentiates through this normalization. The future allocator will minimize variance of $(h+x)/(V+B)$ subject to no sales, a fixed contribution, and concentration bounds.

The worked example has weights $(0.6,0.4)$, asset volatilities $(0.2,0.1)$, and correlation $0.3$. Portfolio volatility is **13.74045%**; asset A holds 60% of capital but accounts for **83.89831%** of volatility contribution. These are hypothetical inputs, not estimates for real securities.

## Implemented and planned

| Area | Current state |
| --- | --- |
| Risk / derivatives / dollar normalization | NumPy reference and analytical checks |
| Simple returns / sample covariance | Complete aligned arrays only |
| Shrinkage | Fixed-alpha sensitivity reference; estimated Ledoit–Wolf coefficient pending |
| Allocation | Mathematical formulation and feasibility checks; solver pending |
| C++ / autodiff / pybind11 | Designed; implementation pending |
| Alpaca / Streamlit | Research and integration contract; no live connection or deployment |

Private development only. Keep credentials, personal holdings, and market-data caches out of commits. USD-denominated US stocks and ETFs, long-only, continuous dollar allocations; cash and leveraged/inverse funds are excluded initially. No price prediction, trading bot, brokerage execution, or return promises.
