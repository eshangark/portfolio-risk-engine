# 4. Architecture and data methodology

## Separation of responsibilities

The proposed dependency chain is provider adapter → validated dataset → Python covariance estimate → C++ risk/AD/optimization engine → Python orchestration → Streamlit presentation. The engine accepts arrays and explicit parameters; it must never fetch network data or depend on dashboard session state. [pybind11](https://pybind11.readthedocs.io/en/stable/) supplies the Python/C++ boundary. The NumPy reference remains an independent oracle.

Each numerical result should carry asset ordering, units, covariance method and parameters, sample dates, row count, data hash, engine version and diagnostics. Binding contracts must validate shape, dtype, memory ownership and exception translation. C++17 and a packaged extension built with CMake/scikit-build-core are proposed for milestone 2, subject to a Linux build and hosted smoke test.

## Provider contract — proposed, not implemented

Alpaca is the selected initial market-data provider. Use only data endpoints, with credentials loaded server-side from deployment secrets or environment variables. Never place credentials in browser state, logs, commits or examples. Store private user holdings only in transient session state initially.

An adapter must return historical daily observations separately from valuation observations. Every response records provider, requested and actual feed, adjustment mode, requested range, event timestamp, retrieval timestamp and freshness state. [Alpaca's access documentation](https://docs.alpaca.markets/us/docs/about-market-data-api) distinguishes IEX coverage from consolidated coverage and subscription-dependent historical access. Verify the connected account's actual entitlement; never silently switch feeds or call automatic refresh real-time.

[Historical bars documentation](https://docs.alpaca.markets/us/reference/stockbars) states raw is the default and offers split, dividend and spin-off adjustments. Explicitly request the chosen mode. Confirm its dividend convention and consistency around known corporate actions before describing it as total return. Pagination follows `next_page_token`; page limits apply across symbols rather than independently to each symbol. Account access, adjustment fixtures and data-display permissions have not yet been tested.

Proposed reliability behavior: bounded retries for transient transport errors, HTTP 429 and retryable server failures, with backoff and `Retry-After`; fail clearly on authentication and malformed data. Initial backfill and incremental refresh use cache keys including symbols, feed, adjustment, dates and provider version. Re-fetch an overlap and invalidate history when corporate-action adjustments revise prior observations. Never splice histories with different adjustment bases. Cache availability is an optimization, not a correctness assumption.

## Observation policy

Only completed exchange sessions enter daily covariance. Use an exchange calendar and explicit timezone handling; a calendar day is not necessarily a trading session. Validate positive finite prices, unique ordered timestamps, identifiers and minimum sample size. Do not forward-fill or turn a gap into a zero return.

Compute each daily return only when both prices for adjacent expected sessions exist; then align common valid return dates across all included assets. Dropping a missing price row first can accidentally create a multi-session return labeled daily. Display excluded sessions and effective coverage. The reference currently accepts only already-aligned complete arrays; calendar-aware processing is pending.

Recent unadjusted prices used for valuing shares must identify event time, feed, session and delay. A last trade is a valuation observation, not a guaranteed executable price. A freshness policy must account for holidays and closed markets and warn or stop instead of silently carrying stale prices into a decision. Preserve these flags through every comparison.

## Hosting feasibility — researched, not deployed

[Streamlit currently permits one private Community Cloud app](https://docs.streamlit.io/deploy/streamlit-community-cloud/share-your-app). Private-repository apps start private, and the sharing setting must be verified at deployment. Existing private-app capacity and account authorization are not yet checked.

[Community Cloud dependency documentation](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies) describes a Debian Linux runtime with `packages.txt` for system packages. Milestone 2 will add explicit build dependencies, install the extension and run a synthetic C++ calculation remotely. A successful Ubuntu CI build does not prove the actual hosted environment works. Capture the deployed URL, build log, C++ import, numerical result and private-access check before claiming success. Do not create a fake deployment badge.

Display/redistribution permissions are unresolved; provider API access alone does not establish permission to publish market data. Check applicable terms before public deployment. Keep fixtures synthetic until retention rights are established.
