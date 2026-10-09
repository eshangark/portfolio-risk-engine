"""Portfolio analysis UI. Numerical calculations execute in the compiled engine."""
import os
import hashlib
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import streamlit as st
from portfolio_risk import _core
from portfolio_risk.data import AlpacaData,DataError,prepare_history,symbols_checked,completed_history_end
from portfolio_risk.estimation import estimate_covariance
from portfolio_risk.research import chronological_study
from portfolio_risk.backtest import contribution_backtest

st.set_page_config(page_title='Portfolio Risk Engine',page_icon='∇',layout='wide')
st.title('Portfolio Risk Engine')
st.caption('Understand risk, compare decisions, and inspect how the model changes the answer.')
source=st.sidebar.radio('Data source',['Synthetic example','Alpaca market data'])
st.sidebar.caption(f'Numerical engine {_core.__version__} · C++17')
st.sidebar.markdown('USD · long-only · fractional shares · no cash sleeve')


def credentials():
    def get(name):
        value=os.environ.get(name)
        if value: return value
        try: return st.secrets.get(name,'')
        except (FileNotFoundError,st.errors.StreamlitSecretNotFoundError): return ''
    return get('ALPACA_API_KEY'),get('ALPACA_API_SECRET')


def provider_for_session(feed):
    key,secret=credentials()
    identity=hashlib.sha256((key+'\0'+secret+'\0'+feed).encode()).hexdigest()
    if st.session_state.get('_provider_identity')!=identity:
        st.session_state['_provider']=AlpacaData(key,secret,feed=feed)
        st.session_state['_provider_identity']=identity
    return st.session_state['_provider']


if source=='Synthetic example':
    st.info('Hypothetical two-asset example. These inputs are not market observations.')
    symbols=['A','B']; holdings=np.array([600.,400.]); cov=np.array([[.04,.006],[.006,.01]])
    returns=None
else:
    text=st.sidebar.text_area('Holdings: symbol, amount (one per line)','SPY, 600\nBND, 400')
    unit=st.sidebar.selectbox('Amount represents',['Dollars','Shares','Weights'])
    notional=st.sidebar.number_input('Portfolio value for hypothetical weights ($)',min_value=1.,value=1000.) if unit=='Weights' else None
    feed=st.sidebar.selectbox('Feed',['iex','sip'])
    st.sidebar.caption('IEX covers one exchange. SIP access depends on your subscription.')
    method=st.sidebar.selectbox('Covariance method',['sample','ledoit_wolf'])
    window=st.sidebar.selectbox('Completed return observations',[63,126,252],index=2)
    history_days=st.sidebar.selectbox('History lookback (calendar days)',[550,2200])
    confirmed=st.sidebar.checkbox('My symbols are US stocks or unleveraged ETFs, with no cash positions.')
    if not confirmed: st.info('Confirm the supported universe to load your portfolio.'); st.stop()
    refresh=st.sidebar.button('Retrieve / refresh data')
    if not refresh and 'market_request' not in st.session_state: st.stop()
    st.session_state.market_request=True
    try:
        pairs=[line.split(',') for line in text.splitlines() if line.strip()]
        if any(len(pair)!=2 for pair in pairs): raise DataError('Use one symbol, amount pair per line.')
        symbols=list(symbols_checked([p[0] for p in pairs])); amounts=np.array([float(p[1]) for p in pairs])
        if not np.isfinite(amounts).all() or np.any(amounts<0) or amounts.sum()<=0: raise DataError('Amounts must be nonnegative with a positive total.')
        if unit=='Weights' and abs(amounts.sum()-1)>1e-12: raise DataError('Hypothetical weights must sum to one.')
        now=pd.Timestamp(datetime.now(timezone.utc)); start=(now-pd.Timedelta(days=history_days)).normalize()
        # Never request the future or the most recent 15 minutes from restricted feeds.
        end=completed_history_end(now).floor('15min')
        provider=provider_for_session(feed)
        with st.spinner('Retrieving completed daily observations…'):
            history=provider.history(tuple(symbols),start.isoformat(),end.isoformat(),force_refresh=refresh)
            prepared=prepare_history(history,start,end,asof=now,min_observations=window)
        returns=prepared.returns
        estimate=estimate_covariance(returns.iloc[-window:].to_numpy(),method)
        cov=estimate.covariance
        if unit=='Shares':
            latest=provider.latest_prices(symbols,now)
            st.dataframe(pd.DataFrame(latest).T)
            if any(row['stale'] for row in latest.values()): raise DataError('Valuation stopped because one or more recent prices are stale.')
            holdings=amounts*np.array([latest[s]['price'] for s in symbols])
        else: holdings=amounts*(notional if unit=='Weights' else 1)
        with st.expander('Data and estimation details',expanded=False):
            st.json({**prepared.metadata,'latest_completed_session':prepared.latest_session,'common_return_rows':len(returns),
                     'dropped_return_dates':prepared.dropped_return_dates,'dataset_sha256':prepared.identity,
                     'sample_window':window,'estimator':method,
                     'window_start':str(returns.iloc[-window:].index[0].date()),
                     'window_end':str(returns.index[-1].date()),
                     'normalization':estimate.normalization,'shrinkage':estimate.shrinkage,
                     'annualization':estimate.annualization})
            st.dataframe(returns.tail(10))
        st.caption(f'History retrieved {history.retrieved_at}. Feed: {feed.upper()}. Completed daily returns; this is not a streaming quote display.')
        st.warning('Provider-adjusted history is used. Its dividend convention has not yet been checked against live events.')
    except (ValueError,DataError) as exc: st.error(str(exc)); st.stop()

weights=holdings/holdings.sum()
result=_core.risk(weights,cov,autodiff=True)
col1,col2=st.columns(2)
col1.metric('Estimated annual volatility',f"{result['volatility']:.2%}")
col2.metric('Portfolio value',f'${holdings.sum():,.2f}')
st.caption('Constant-weight return volatility under a fixed covariance estimate; not a prediction or a complete investment objective.')
rc=result['contributions']; grad=result['gradient']
frame=pd.DataFrame({'Asset':symbols,'Capital weight':weights,'Dollar holding':holdings})
if rc is not None:
    frame['Risk contribution']=rc; frame['Share of volatility']=rc/result['volatility']
    frame['Marginal volatility']=grad
    st.dataframe(frame.set_index('Asset'),width='stretch')
    leader=int(np.argmax(rc)); st.write(f"{symbols[leader]} contributes the most estimated volatility: {rc[leader]/result['volatility']:.1%}, compared with {weights[leader]:.1%} of capital.")
    st.bar_chart(frame.set_index('Asset')[['Capital weight','Share of volatility']])
else:
    st.dataframe(frame); st.info('Volatility is zero; the usual volatility gradient is unavailable.')

st.subheader('Compare a new purchase')
asset=st.selectbox('Buy asset',symbols)
amount=st.number_input('New cash purchase ($)',min_value=0.,value=100.)
delta=np.zeros(len(symbols)); delta[symbols.index(asset)]=amount
new_h=holdings+delta; after=_core.risk(new_h/new_h.sum(),cov)
exact=after['volatility']-result['volatility']
st.write(f'After purchase: {after["volatility"]:.4%} volatility; change {100*exact:+.4f} percentage points.')
if grad is not None:
    linear=float(_core.dollar_gradient(holdings,cov)@delta)
    st.write(f'Local derivative approximation: {100*linear:+.4f} percentage points. Approximation error: {100*(linear-exact):+.4f} points.')

st.subheader('Allocate a contribution')
budget=st.number_input('Total contribution ($)',min_value=0.,value=200.)
cap=st.slider('Maximum post-contribution weight per asset',min_value=0.01,max_value=1.,value=.60,step=.01)
try:
    allocation=_core.allocate(holdings,budget,cov,np.full(len(symbols),cap))
    if not allocation['converged']: st.warning('Iteration limit reached; treat this as an unfinished optimization result.')
    st.dataframe(pd.DataFrame({'Asset':symbols,'Purchase dollars':allocation['purchases'],'Resulting weight':allocation['weights']}).set_index('Asset'),width='stretch')
    st.write(f"Allocated volatility: {np.sqrt(allocation['variance']):.4%}. Variance improvement over a feasible projected-equal-purchase baseline: {allocation['improvement']:.6g}.")
    with st.expander('Optimization diagnostics'):
        st.json({k:v for k,v in allocation.items() if k not in ('purchases','weights')})
    if returns is not None:
        comparisons=[]
        for count in (63,126,252):
            if len(returns)<count: continue
            for name in ('sample','ledoit_wolf'):
                alternative=estimate_covariance(returns.iloc[-count:].to_numpy(),name)
                solution=_core.allocate(holdings,budget,alternative.covariance,np.full(len(symbols),cap))
                comparisons.append({'Window':count,'Estimator':name,'Volatility':np.sqrt(solution['variance']),
                                    'Converged':solution['converged'],**{s:float(x) for s,x in zip(symbols,solution['purchases'])}})
        st.subheader('Sensitivity to estimation choices')
        st.dataframe(pd.DataFrame(comparisons),width='stretch')
        st.caption('Allocation differences across models are sensitivity results, not a calibrated confidence interval.')
except ValueError as exc: st.error(f'No feasible allocation: {exc}')

if returns is not None:
    with st.expander('Chronological variance study'):
        st.write('Fit on preceding 63, 126 or 252 observations and evaluate the next 21 observations. Each decision starts with 100 dollars per asset and a 200-dollar contribution, with no concentration cap beyond 100%.')
        st.caption('This uses independent hypothetical decisions, not your holdings or a cumulative trading strategy. Revised history and a chosen asset universe can still introduce bias.')
        if st.button('Run chronological study'):
            try:
                with st.spinner('Evaluating separated training and test periods…'):
                    study=chronological_study(returns)
                rows=pd.DataFrame(study['results'])
                st.write(f"{len(rows)} model evaluations across {rows['test_start'].nunique()} nonoverlapping test blocks.")
                summary=rows.groupby(['window','method'],as_index=False).agg(
                    evaluations=('converged','size'),
                    mean_calibration_ratio=('calibration_ratio','mean'),
                    mean_allocation_l1_change=('allocation_l1_change','mean'))
                st.dataframe(summary,width='stretch')
                st.caption('Calibration ratio = realized / estimated annual variance. A ratio near one on this short sample does not establish predictive accuracy.')
                st.dataframe(rows.drop(columns=['weights']),width='stretch')
                st.json({'dataset_sha256':prepared.identity,'feed':feed,'adjustment':history.adjustment,
                         'retrieved_at':history.retrieved_at,'design':study['design'],
                         'initial_dollars_per_asset':study['initial_dollars_per_asset'],
                         'contribution':study['contribution'],'cap':study['cap'],'annualization':study['annualization']})
            except ValueError as exc:
                st.error(f'Study unavailable: {exc}')
    with st.expander('Historical contribution backtest'):
        st.write('Start with 1,000 hypothetical dollars equally divided among the selected assets. Every 21 observations, invest 200 dollars using the preceding 126 observations and Ledoit-Wolf covariance. Compare with equal-dollar purchases using identical cash flows.')
        st.caption('Holdings drift with each daily return. All decisions precede the return being evaluated. Fees, taxes, spreads and executable prices are excluded. Provider dividend conventions and historical revisions limit the interpretation.')
        if st.button('Run historical backtest'):
            try:
                with st.spinner('Simulating chronological contributions…'):
                    backtest=contribution_backtest(returns)
                st.dataframe(pd.DataFrame({name:backtest[name] for name in ('optimized','equal_purchases')}).T,width='stretch')
                st.write(f"{backtest['observations']} evaluated observations; {len(backtest['decisions'])} contributions totaling {backtest['total_contributions']:,.2f} dollars.")
                ledger=pd.DataFrame(backtest['ledger']).set_index('date')
                st.line_chart(ledger[['wealth','equal_purchase_wealth']])
                st.caption('Terminal wealth includes deposits. Time-weighted return removes the direct effect of deposits; volatility and drawdown use the daily time-weighted return series.')
                st.json({k:v for k,v in backtest.items() if k not in ('ledger','decisions','optimized','equal_purchases')})
            except ValueError as exc:
                st.error(f'Backtest unavailable: {exc}')
