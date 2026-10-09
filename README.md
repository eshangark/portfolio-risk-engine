# Portfolio Risk Engine

A mathematics-first C++17 and Python engine for portfolio risk, automatic differentiation and constrained contribution allocation.

**What drives estimated portfolio risk, how does a decision change it, and how dependent is the answer on the model?**

The compiled engine evaluates volatility and risk contributions, differentiates dollar normalization with a custom reverse-mode tape, and allocates a new contribution using projected gradient on a capped simplex. Python supplies independent reference calculations, covariance estimation, an Alpaca data adapter and a Streamlit interface.

- [Technical paper (PDF)](docs/paper/portfolio-risk-engine.pdf) and [LaTeX source](docs/paper/portfolio-risk-engine.tex)
- [Measured numerical results](docs/results/engine-report.json)
- [Validation run](https://github.com/eshangark/portfolio-risk-engine/actions/runs/37956387933): 27 tests on Python 3.10 and 3.12, native C++ sanitizer checks, and reproducible examples
- [Verified status](docs/status.md), [requirements and evidence](docs/requirements.md), [specification](docs/specification.md)

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

The synthetic app needs no credentials. [App setup](app/README.md) describes server-side Alpaca secrets and private hosting configuration. **No hosted deployment or live-account validation is claimed.** The local project is a working copy; GitHub stores the committed source and runs Linux validation remotely.

## Mathematics

For fixed symmetric PSD covariance $\Sigma$ and long-only weights summing to one:

$$v=w^T\Sigma w,\qquad \sigma=\sqrt{v},\qquad \nabla_w\sigma=\Sigma w/\sigma\quad(\sigma>0).$$

Risk contribution is $RC_i=w_i\partial_i\sigma$, with $\sum_i RC_i=\sigma$. Adding dollars changes all normalized weights. The allocator minimizes the variance of $(h+x)/(V+B)$ with $x\ge0$, $\sum_i x_i=B$, and post-contribution concentration caps. Its output includes feasibility and projected-gradient residuals, iteration count and convergence status.

In the worked example, weights $(0.6,0.4)$ and covariance entries $(.04,.006;.006,.01)$ give **13.74045% volatility**. Asset A holds 60% of capital but contributes **83.89831%** of volatility. A $200 contribution to holdings $(600,400)$ with 60% caps is allocated entirely to B, yielding weights $(.5,.5)$ and variance .0155. Inputs are hypothetical annual quantities.

## Capabilities and remaining work

| Area | Implemented | Remaining validation |
| --- | --- | --- |
| C++ / autodiff | Risk, attribution, dollar and shrinkage sensitivities; owned tape | Broader scale stress tests and performance benchmarks |
| Allocation | Capped-simplex projection, analytical/AD gradients, OSQP comparison | Real-data allocation stability study |
| Estimation | Sample covariance, fitted Ledoit–Wolf, explicit normalization | Chronological estimation-quality study |
| Data | Pagination, bounded retries, cache, session alignment, stale-price checks | Live entitlement, corporate actions, incremental refresh |
| Interface | Synthetic and market workflows; tested synthetic interactions | Private hosted operation and live end-to-end checks |

Scope: USD US stocks and unleveraged ETFs; long-only, continuous dollar purchases, no cash sleeve. Asset eligibility currently requires user confirmation. Historical covariance is a model estimate, not a forecast guarantee. No trading, brokerage execution or return promises. Keep credentials, holdings and market-data caches outside commits. The repository remains private; no open-source license has been selected.

## Rebuild the paper

The PDF is the reading copy; the standalone `.tex` is the editable source. With Tectonic installed:

```sh
tectonic docs/paper/portfolio-risk-engine.tex
```

Planning documents remain during development and will be reviewed for removal before public release.
