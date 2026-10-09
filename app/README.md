# Run the interface

Install the engine and application extras with `python -m pip install '.[app]'`,
then run `streamlit run app/streamlit_app.py` from the repository root.

The synthetic example requires no credentials. For Alpaca, supply
`ALPACA_API_KEY` and `ALPACA_API_SECRET` through server environment variables or
Streamlit secrets. Never commit a secrets file. Select the feed explicitly.

Community Cloud configuration: private repository, branch `main`, entry point
`app/streamlit_app.py`, Python 3.12. Root `packages.txt` installs the C++ compiler
and Eigen; `requirements.txt` builds the Python extension. Verify Sharing is
restricted to specific people. No deployment is claimed until its URL, compiled
engine result and private-access setting have been checked.

Live entitlement, dividend/split convention checks, and display permissions are
still pending. Historical caches refresh whole adjusted windows; revision-safe
incremental refresh is not implemented. Keep development private.
