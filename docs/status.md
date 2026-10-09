# Verified project status

Updated 2026-10-08, America/New_York.

## Milestone 1: foundation

- Private repository created at https://github.com/eshangark/portfolio-risk-engine; GitHub API returned `private: true` and `visibility: private`.
- Mathematical specification, living paper, source register, architectural/data contracts, decisions and requirements table prepared.
- NumPy reference implements risk, analytical sensitivities, dollar normalization, simple returns, sample covariance, fixed-alpha shrinkage and purchase feasibility.
- All 13 local tests passed on Python 3.12.14 / NumPy 2.3.5, macOS arm64. Offline two-asset example ran and generated docs/results/two-asset.json.
- GitHub Actions configured for Python 3.10 and 3.12. Remote workflow outcome is not yet recorded here.

## Current limitations

No C++ engine, custom AD, estimated Ledoit–Wolf coefficient, numerical optimizer, live Alpaca integration, or Streamlit application is implemented yet. No deployment, real-market validation or benchmark has run. These are subsequent milestones, not omitted requirements.

The system Git/Python entry points require missing Apple developer tools. The bundled Codex Git and Python runtimes work and were used for the foundation. C++ local compilation will require a toolchain or a validated Linux build environment. GitHub repository creation used the browser; repository content can be written through the connected GitHub API.

## Next complete milestone

Add the C++17 risk core with pybind11, package and test on Linux against the independent reference, then deploy a private synthetic Streamlit smoke test. Verify the actual target build and private access before adding market-data credentials. Hosting authorization/private-app slot availability and provider credentials/terms will be checked when needed.

## Session handoff

Read AGENTS.md, README.md, this status, decisions and requirements first. Keep the repository private. Preserve the original project brief. Use synthetic fixtures until market-data retention permissions are established. See paper/05-validation.md for reproduction commands and comprehension questions.
