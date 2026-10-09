# Verified project status

Updated 2026-10-09, America/New_York.

## Live integration update (verified synthetic and Linux results)

The owner configured server secrets and deployed the private Streamlit app.
On 2026-10-09 the hosted C++ engine ran the synthetic example (13.74% volatility,
$200 allocated to B) and retrieved IEX-adjusted SPY/BND history successfully.
There were 379 common daily return observations, no dropped return dates, and
the latest completed session was 2026-10-09. The hypothetical $600/$400 portfolio
had 8.47805897% estimated annual volatility over the last 252 observations;
the $200 contribution went to BND, yielding 7.42762416% volatility. All six
window/estimator comparisons converged. The Share dialog showed “Make this app
public” unchecked. [Deployment](https://portfolio-risk-eng-fwywewfctjzvsqsxvhmumt.streamlit.app/).
Dataset identity: `2a3c00006e0e1b8b35309c375b0c00989d291c180d78ca569382c371e9905080`;
retrieval time `2026-10-09T21:36:29.866272+00:00`, source revision `15ccd273`.
These observations validate integration, not investment performance.

Added server setup instructions, a read-only live report command,
complete-snapshot revision auditing, independent corporate-event arithmetic,
chronological study and benchmark commands. Corrected history requests to avoid
future/restricted recent timestamps and isolated provider caches per session.
Added a C++ projection fix for large common offsets and scale-invariance tests.
Eight local data tests pass. [Run 37958614693](https://github.com/eshangark/portfolio-risk-engine/actions/runs/37958614693)
at `aeea037dcf3a5dafaa3cc98adcc868255d813792` passed all 34 tests on Python 3.10
and 3.12, native sanitizers, all examples and the benchmark. The synthetic study
completed 72 evaluations (mean calibration ratio 1.0096; not market evidence).
[Benchmarks](results/benchmark.json) include validation and binding overhead:
at 50 assets, NumPy 285.10 us, C++ analytical 182.34 us, C++ AD 884.69 us median
on the recorded Python 3.12 runner. The chronological runner is now accessible
from the market-data interface. At source revision `8da7a371`, hosted SPY/BND
history produced 36 live model evaluations over six nonoverlapping 21-observation
test blocks. Each model had six evaluations. Mean calibration ratios for
sample / Ledoit-Wolf were 0.9040 / 0.8344 (63 observations), 1.0251 / 0.9666
(126), and 1.2418 / 1.1551 (252). Mean successive allocation L1 changes were
zero in every group, reflecting boundary solutions in this two-asset example.
Dataset identity matched the integration snapshot above; retrieval time was
`2026-10-09T21:38:30.377874+00:00`. This is a short chosen-universe study,
not a general estimator ranking, unbiased vintage test or return backtest.

## Completed engine milestone

- C++17/Eigen risk core, custom reverse-mode tape, pybind11 package and constrained allocator implemented.
- Independent NumPy formulas, sample and fitted Ledoit–Wolf estimation, Alpaca adapter, calendar preparation and Streamlit app implemented.
- [Run 37956387933](https://github.com/eshangark/portfolio-risk-engine/actions/runs/37956387933), commit `8438207338cb59ff0a47db6f78eb5a3129ff1a94`: all 27 tests passed on Ubuntu/Python 3.10 and 3.12; native address/undefined-behavior sanitizer test passed; both example reports produced and uploaded.
- [Measured C++ report](results/engine-report.json) preserves Python 3.12 job output with source hashes. Weight-gradient error 2.78e-17; dollar-gradient error 4.07e-20 on the two-asset fixture. Allocation purchases [0,200], variance .0155, reported constraint and mapping residuals zero.
- Streamlit AppTest path failure fixed by resolving the script from the test file's location. No numerical expectations were weakened.
- Paper converted to standalone LaTeX and PDF, with derivations, implementation detail, measured evidence and limitations. Old paper Markdown chapters replaced; planning documents retained per owner instruction.

## Remaining work

The interface addition passed all three jobs in
[run 37994607531](https://github.com/eshangark/portfolio-risk-engine/actions/runs/37994607531)
at `8da7a371`: Python 3.10, Python 3.12 and native sanitizers.

1. Additional hosted valuation/freshness interactions and broader real-data studies.
2. Known live split/dividend checks, automated eligible-universe checks, and reduced-bandwidth incremental refresh. IEX history access is verified; SIP entitlement is not. Current refresh audits complete adjusted snapshots; it never splices adjustment vintages.
3. Chronological real-data estimation/allocation study and wider scale stress testing. End-to-end benchmarks are measured; isolated kernel/binding benchmarks remain separate. No market-performance advantage claimed.
4. Final publication review: remove agreed planning files when instructed, choose license and check data-display rights. Keep repository private until explicit direction.

## Environment and continuation

The working copy lives under Documents/Codex; local edits occur there and may sync through the user's iCloud settings. GitHub contains committed code and remote test results. Local C++ compilation remains unavailable because Apple developer tools are absent; compiled validation runs on GitHub's Ubuntu machines. No Linux installation on the user's Mac is needed for these checks.

Bundled Git/Python are available. Command-line GitHub authentication is not configured; commits are uploaded through the connected GitHub API. Do not install a system toolchain, move the project or delete environments without a task-specific reason and authorization.

Read AGENTS.md, README.md, this file, decisions and requirements when resuming. Keep measured evidence tied to its original revision even when later documentation changes.
