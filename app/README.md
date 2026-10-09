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
still pending. Keep development private.

See [live setup](../docs/live-setup.md) for the server secrets template and
read-only verification commands. Complete-snapshot refresh now reports additions,
removals and revisions without splicing adjustment vintages. Reduced-bandwidth
overlap-only refresh remains deferred. The app retains a separate provider cache
per session and never requests history through a future cutoff.
