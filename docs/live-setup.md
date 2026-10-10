# Live data and private deployment

The app is integrated with Alpaca's **market-data endpoints only**. It cannot
place orders. An account and server-side API credentials are still required.

## Account setup

1. Create or sign in to your account at [Alpaca](https://alpaca.markets/).
2. Obtain an API key and secret through your account dashboard. Keep them out of
   chat, source files, screenshots and GitHub commits. Do not change a paid plan
   merely to run the initial IEX example.
3. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) with access
   to the private GitHub repository. No account has been created by this project.

## Deploy the prepared app

Choose repository `eshangark/portfolio-risk-engine`, branch `main`, entry point
`app/streamlit_app.py`, and Python 3.12. The root dependency files build the C++
extension. Use the platform's advanced settings / Secrets field:

```toml
ALPACA_API_KEY = "your-key"
ALPACA_API_SECRET = "your-secret"
```

Verify sharing is restricted before entering personal holdings. Run the
synthetic example first: volatility must be 13.74%, and a $200 contribution with
60% caps must purchase $200 of B. Then select Alpaca, initially IEX, confirm the
supported universe and click Retrieve / refresh data. IEX is one-exchange data;
SIP requires the relevant account access. The app makes no streaming or guaranteed
real-time claim. Share valuation stops on stale observations.

Check the retrieved timestamp, feed, completed session, sample coverage and
normalization in Data and estimation details. A 401/403 is an account or feed
access failure, not a reason to switch feeds silently.

## Command-line validation

In an environment with the package installed, supply `ALPACA_API_KEY` and
`ALPACA_API_SECRET` through the environment, then:

```sh
python -m examples.live_report --feed iex --symbols SPY BND --output work/live-report.json
python -m examples.live_report --feed iex --symbols SPY BND --study --output work/live-study.json
```

These are read-only data requests. The latter runs the predeclared chronological
protocol; it does not choose windows based on future results or simulate trading.
Reports remain under ignored `work/`; they are not public research results.
Hosted IEX retrieval was verified on 2026-10-09. The app also exposes the
chronological variance study and a cash-flow-aware historical contribution
backtest. Select 2,200 calendar days for the longer study. Backtests stop if
daily returns are missing; they never silently skip unknown wealth changes.

## Adjustment audits and revision policy

`portfolio_risk.adjustments.audit_event` compares a provider-adjusted return with
an independently specified split ratio and cash distribution. For a pre-event
price P, post-event price Q, new shares per old share k and cash per old share d,
the holder's event return is `(k*Q+d)/P-1`.

- `k`: new shares received per old share.
- `Q`: price per new share after the event.
- `d`: cash distribution per old share.
- `P`: price per old share before the event.

Supply checked event terms and prices;
a synthetic arithmetic test alone cannot certify Alpaca's dividend convention.

Every expired or manually refreshed adjusted history is fetched as a complete
snapshot and audited for additions, removals and revisions, including older
dates. Cached histories are copied before use. This detects incremental changes
without mixing adjustment vintages. Reduced-bandwidth overlap-only refresh is
not implemented because a short overlap cannot rule out arbitrary older revisions.

Sources checked October 9, 2026: [Alpaca history](https://docs.alpaca.markets/us/reference/stockbars),
[corporate-action availability caveat](https://docs.alpaca.markets/us/reference/corporateactions-1),
[Streamlit secrets](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management).
SIP entitlement, known live action checks and data-display rights remain
separate from software test results. Keep development and the app private.
