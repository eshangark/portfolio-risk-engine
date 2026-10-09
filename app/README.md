# Run the interface

Install the engine and application extras with `python -m pip install '.[app]'`,
then run `streamlit run app/streamlit_app.py` from the repository root.

The synthetic example requires no credentials. For Alpaca, supply
`ALPACA_API_KEY` and `ALPACA_API_SECRET` through server environment variables or
Streamlit secrets. Never commit a secrets file. Select the feed explicitly.

Community Cloud configuration: private repository, branch `main`, entry point
`app/streamlit_app.py`, Python 3.12. Root `packages.txt` installs the C++ compiler
and Eigen; `requirements.txt` builds the Python extension. Verify Sharing is
restricted to specific people. Private hosted C++ operation and IEX history
retrieval were verified on 2026-10-09.

SIP entitlement, dividend/split convention checks, and display permissions are
still pending. Keep development private.

See [live setup](../docs/live-setup.md) for the server secrets template and
read-only verification commands. Complete-snapshot refresh now reports additions,
removals and revisions without splicing adjustment vintages. Reduced-bandwidth
overlap-only refresh remains deferred. The app retains a separate provider cache
per session and never requests history through a future cutoff.

Choose a history lookback, retrieve data and expand the chronological study or
historical contribution backtest. These use fixed hypothetical policies, not
account holdings or order submission. See [validation](../docs/validation.md).
When changing the installed Python/C++ package, update the dependency manifest
to trigger a Community Cloud rebuild; a script rerun alone can retain an older
installed wheel. Check the displayed engine version after deployment.
