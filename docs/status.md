# Verified project status

Updated 2026-10-09, America/New_York.

## Live integration update (validation in progress)

The owner has created an Alpaca account; credentials and Streamlit sign-in are
still needed. Added server setup instructions, a read-only live report command,
complete-snapshot revision auditing, independent corporate-event arithmetic,
chronological study and benchmark commands. Corrected history requests to avoid
future/restricted recent timestamps and isolated provider caches per session.
Added a C++ projection fix for large common offsets and scale-invariance tests.
Eight local data tests pass; compiled tests and measurements require the next CI
run. No live API result or hosted deployment is claimed.

## Completed engine milestone

- C++17/Eigen risk core, custom reverse-mode tape, pybind11 package and constrained allocator implemented.
- Independent NumPy formulas, sample and fitted Ledoit–Wolf estimation, Alpaca adapter, calendar preparation and Streamlit app implemented.
- [Run 37956387933](https://github.com/eshangark/portfolio-risk-engine/actions/runs/37956387933), commit `8438207338cb59ff0a47db6f78eb5a3129ff1a94`: all 27 tests passed on Ubuntu/Python 3.10 and 3.12; native address/undefined-behavior sanitizer test passed; both example reports produced and uploaded.
- [Measured C++ report](results/engine-report.json) preserves Python 3.12 job output with source hashes. Weight-gradient error 2.78e-17; dollar-gradient error 4.07e-20 on the two-asset fixture. Allocation purchases [0,200], variance .0155, reported constraint and mapping residuals zero.
- Streamlit AppTest path failure fixed by resolving the script from the test file's location. No numerical expectations were weakened.
- Paper converted to standalone LaTeX and PDF, with derivations, implementation detail, measured evidence and limitations. Old paper Markdown chapters replaced; planning documents retained per owner instruction.

## Remaining work

1. Private Streamlit deployment: account authorization/capacity, actual hosted C++ build, private sharing verification and synthetic interaction check. No deployment exists yet.
2. Live Alpaca entitlement and known split/dividend checks, automated eligible-universe checks, and revision-safe incremental refresh. Current cache expiry re-fetches the entire adjusted window.
3. Chronological real-data estimation/allocation study, numerical scale hardening, and fair NumPy/C++ benchmarks. No empirical or speed advantage claimed.
4. Final publication review: remove agreed planning files when instructed, choose license and check data-display rights. Keep repository private until explicit direction.

## Environment and continuation

The working copy lives under Documents/Codex; local edits occur there and may sync through the user's iCloud settings. GitHub contains committed code and remote test results. Local C++ compilation remains unavailable because Apple developer tools are absent; compiled validation runs on GitHub's Ubuntu machines. No Linux installation on the user's Mac is needed for these checks.

Bundled Git/Python are available. Command-line GitHub authentication is not configured; commits are uploaded through the connected GitHub API. Do not install a system toolchain, move the project or delete environments without a task-specific reason and authorization.

Read AGENTS.md, README.md, this file, decisions and requirements when resuming. Keep measured evidence tied to its original revision even when later documentation changes.
