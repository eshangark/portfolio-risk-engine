"""Portfolio analysis UI. Numerical calculations execute in the compiled engine."""
import os
import hashlib
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import altair as alt
import streamlit as st
from portfolio_risk import _core
from portfolio_risk.data import AlpacaData,DataError,prepare_history,symbols_checked,completed_history_end
from portfolio_risk.estimation import estimate_covariance
from portfolio_risk.research import chronological_study
from portfolio_risk.backtest import contribution_backtest

st.set_page_config(page_title='Portfolio Risk Engine',page_icon='∇',layout='wide')
appearance=st.pills('Appearance',['Light','Dark'],selection_mode='single',default='Light',key='appearance')
dark_mode=appearance=='Dark'
palette=({'background':'#101820','surface':'#1C2935','text':'#E8EFF5','muted':'#B5C5D1','border':'#3D5263','accent':'#70D0D8'}
         if dark_mode else {'background':'#FAFBFC','surface':'#EEF2F5','text':'#192D3A','muted':'#526574','border':'#C8D2DA','accent':'#286E77'})
st.markdown(f"""<style>
.stApp, [data-testid="stHeader"], [data-testid="stSidebar"] {{background: {palette['background']}; color: {palette['text']}; color-scheme: {'dark' if dark_mode else 'light'};}}
[data-testid="stAppViewContainer"] {{color: {palette['text']};}}
[data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p, h1,h2,h3, label, [data-testid="stMetricValue"], [data-testid="stWidgetLabel"] p {{color: {palette['text']} !important;}}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p, [data-testid="stCaption"] {{color: {palette['muted']} !important; opacity: 1;}}
[data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"], [data-testid="stVerticalBlockBorderWrapper"] {{border-color: {palette['border']} !important;}}
[data-testid="stVerticalBlockBorderWrapper"] > div {{border-color: {palette['border']} !important;}}
[data-testid="stMetric"], [data-testid="stExpander"], [data-testid="stAlert"], [data-testid="stJson"] {{background: {palette['surface']}; color: {palette['text']}; border-color: {palette['border']};}}
[data-testid="stExpander"] summary, [data-testid="stExpander"] svg, [data-testid="stHeader"] button, [data-testid="stSidebar"] button {{color: {palette['text']} !important;}}
[role="tab"] {{color: {palette['muted']} !important;}} [role="tab"][aria-selected="true"] {{color: {palette['accent']} !important;}}
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div, [data-testid="stNumberInput"] button, .stButton > button {{background: {palette['surface']} !important; color: {palette['text']} !important; border-color: {palette['border']} !important;}}
input, textarea {{background: {palette['surface']} !important; color: {palette['text']} !important; -webkit-text-fill-color: {palette['text']} !important;}}
[data-baseweb="slider"] {{color: {palette['text']} !important;}}
[data-testid="stToolbar"] button, [data-testid="stHeader"] svg {{color: {palette['muted']} !important;}}
[data-testid="stMarkdownContainer"] a {{color: {palette['accent']};}}
[data-testid="stTooltipContent"], [data-baseweb="tooltip"], [data-baseweb="popover"] > div, [role="tooltip"], [role="listbox"], [role="menu"], [data-testid="stDialog"] [role="dialog"] {{background: {palette['surface']} !important; color: {palette['text']} !important; border: 1px solid {palette['border']};}}
[data-testid="stTooltipContent"] *, [data-baseweb="tooltip"] *, [data-baseweb="popover"] *, [role="tooltip"] *, [role="listbox"] *, [role="menu"] * {{color: {palette['text']} !important;}}
[data-baseweb="select"] button {{background: {palette['surface']} !important; color: {palette['text']} !important;}}
[data-baseweb="select"] svg {{color: {palette['text']} !important;}}
[role="option"] {{background: {palette['surface']} !important; color: {palette['text']} !important;}}
[role="option"]:hover, [role="menuitem"]:hover {{background: {palette['border']} !important;}}
[data-testid="stTooltipIcon"] svg, [data-testid="stTooltipHoverTarget"] svg {{color: {palette['muted']} !important;}}
button[data-variant="pills"] {{background: {palette['surface']} !important; color: {palette['text']} !important; border: 1px solid {palette['border']} !important;}}
button[data-variant="pills"][aria-checked="true"] {{background: {palette['accent']} !important; color: {palette['background']} !important;}}
button[data-variant="pills"][aria-checked="true"] p {{color: {palette['background']} !important;}}
button[data-variant="pills"]:focus-visible {{outline: 2px solid {palette['accent']}; outline-offset: 3px;}}
</style>""",unsafe_allow_html=True)
st.markdown("""<style>
.block-container {max-width: 1200px; padding-top: 4.5rem;}
h1 {letter-spacing: -.04em;} h2,h3 {letter-spacing: -.02em;}
[data-testid="stMetric"] {border-radius: 16px; padding: 18px;}
.stButton > button {border-radius: 10px;}
</style>""", unsafe_allow_html=True)

def show_frame(data,**kwargs):
    # Canvas-backed tables need cell colors as well as the surrounding CSS.
    styled=data.style.set_properties(**{'background-color':palette['surface'],'color':palette['text']})
    st.dataframe(styled,**kwargs)

def show_chart(chart):
    chart=(chart.configure(background=palette['background'])
           .configure_axis(labelColor=palette['text'],titleColor=palette['text'],gridColor=palette['border'],domainColor=palette['border'])
           .configure_legend(labelColor=palette['text'],titleColor=palette['text'])
           .configure_view(stroke=palette['border']))
    st.altair_chart(chart,use_container_width=True,theme=None)
st.caption('PORTFOLIO ANALYSIS')
st.title('Understand your portfolio risk')
st.write('Go from understanding your risk to exploring what to do with new money. The engine combines asset co-movement, automatic differentiation, and constrained optimization to explain risk and calculate contribution allocations. Start with the demo below, then choose market data in the sidebar to explore your own holdings; no orders are placed.')
feature_columns=st.columns(4)
for column,title,description in zip(feature_columns,
        ['1 · Understand risk','2 · Test a purchase','3 · Optimize new money','4 · Check against history'],
        ['See which assets drive volatility, beyond their share of your money.',
         'Compare risk before and after a purchase, with a derivative-based estimate.',
         'Calculate purchases that minimize estimated variance within your concentration limit.',
         'Compare estimated risk with later observations and backtest contributions.']):
    with column:
        with st.container(border=True):
            st.markdown(f'**{title}**')
            st.caption(description)
st.caption('Explore the four tabs below. Try Allocate a contribution to see the optimizer in action; expand calculation panels for the mathematics.')
source=st.sidebar.radio('Data source',['Synthetic example','Alpaca market data'])
st.sidebar.caption(f'Numerical engine {_core.__version__} · C++17')
st.sidebar.caption('Supported: USD US stocks and unleveraged ETFs. Purchases only; fractional shares; no cash balance.')


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
    method=st.sidebar.selectbox('Risk estimation',['sample','ledoit_wolf'],format_func=lambda x: {'sample':'Historical sample','ledoit_wolf':'Smoothed estimate (Ledoit–Wolf)'}[x],help='Sample uses observed co-movement directly. Smoothing reduces sensitivity to noisy estimates.')
    window=st.sidebar.selectbox('Days used to estimate risk',[63,126,252],index=2,help='Trading observations. A shorter window reacts faster; a longer window includes more history.')
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
            show_frame(pd.DataFrame(latest).T)
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
            show_frame(returns.tail(10))
        st.caption(f'History retrieved {history.retrieved_at}. Feed: {feed.upper()}. Completed daily returns; this is not a streaming quote display.')
        st.warning('Provider-adjusted history is used. Its dividend convention has not yet been checked against live events.')
    except (ValueError,DataError) as exc: st.error(str(exc)); st.stop()

weights=holdings/holdings.sum()
result=_core.risk(weights,cov,autodiff=True)
overview,purchase_tab,allocation_tab,history_tab=st.tabs(['Overview','Compare a purchase','Allocate a contribution','Historical checks'])
with overview:
    st.subheader('Where does your risk come from?')
    st.write('This page separates the share of money in each asset from its contribution to portfolio risk. The engine combines portfolio weights with asset variability and co-movement, then uses derivatives to attribute volatility. Compare the capital and risk shares below to identify which holdings drive the estimate.')
    col1,col2=st.columns(2)
    col1.metric('Estimated annual volatility',f"{result['volatility']:.2%}")
    col2.metric('Portfolio value',f'${holdings.sum():,.2f}')
    st.caption('Volatility measures how widely annual returns may vary under this historical model. It is not an expected return or a maximum possible loss.')
    with st.expander('How we calculate this'):
        st.write('1. Divide each holding by total portfolio value to get its weight.\n2. Combine weights with asset variances and co-movement.\n3. Take the square root to express risk as volatility.')
        st.latex(r'V=\sum_i h_i,\quad w_i=h_i/V,\quad \sigma=\sqrt{w^T\Sigma w}')
        st.markdown('- $V$: total portfolio value in dollars.\n- $h_i$: dollars held in asset $i$.\n- $w_i$: asset $i$’s fraction of portfolio value; $w$ collects all weights.\n- $i$: an asset index.\n- $\\sum_i$: add the quantity across all assets.\n- $T$ in $w^T$: transpose, which turns the weight column into a row.')
        st.write(f'Here, total value is ${holdings.sum():,.2f} and estimated variance is {result["volatility"]**2:.6f}. Its square root is {result["volatility"]:.2%}.')
    rc=result['contributions']; grad=result['gradient']
    frame=pd.DataFrame({'Asset':symbols,'Capital weight':weights,'Dollar holding':holdings})
    if rc is not None:
        frame['Risk contribution']=rc; frame['Share of volatility']=rc/result['volatility']
        frame['Marginal volatility']=grad
        show_frame(frame[['Asset','Capital weight','Dollar holding','Share of volatility']].set_index('Asset'),width='stretch',column_config={'Capital weight':st.column_config.NumberColumn(format='percent'),'Share of volatility':st.column_config.NumberColumn(format='percent'),'Dollar holding':st.column_config.NumberColumn(format='dollar')})
        st.caption('Capital weight is your share of invested money. Share of volatility is each asset’s contribution to total risk; it can be negative when an asset offsets other risks.')
        with st.expander('Risk attribution mathematics'):
            st.latex(r'RC_i=w_i(\Sigma w)_i/\sigma,\qquad \sum_i RC_i=\sigma')
            st.markdown('- $RC_i$: asset $i$’s contribution to portfolio volatility.\n- $w$: vector of portfolio weights; $w_i$ is the weight of asset $i$.\n- $i$: an asset index; $(\\Sigma w)_i$ selects entry $i$ of the matrix–vector product.\n- $\\sum_i$: sum across assets.')
            show_frame(frame.set_index('Asset'),width='stretch')
        leader=int(np.argmax(rc)); st.write(f"{symbols[leader]} contributes the most estimated volatility: {rc[leader]/result['volatility']:.1%}, compared with {weights[leader]:.1%} of capital.")
        chart_data=frame[['Asset','Capital weight','Share of volatility']].melt('Asset',var_name='Measure',value_name='Share')
        show_chart(alt.Chart(chart_data).mark_bar().encode(x='Asset:N',xOffset='Measure:N',y=alt.Y('Share:Q',axis=alt.Axis(format='%')),color=alt.Color('Measure:N',scale=alt.Scale(range=['#70D0D8','#E8AA65'])),tooltip=['Asset','Measure',alt.Tooltip('Share:Q',format='.1%')]))
    else:
        show_frame(frame); st.info('Volatility is zero; the usual volatility gradient is unavailable.')

with purchase_tab:
    st.subheader('What changes if you buy more?')
    st.write('Explore how adding money to one asset would change your portfolio risk. The engine recalculates every weight and volatility, and uses automatic differentiation to show a small-change approximation alongside the exact result. Choose an asset and a purchase amount below, then compare the before-and-after risk and approximation error.')
    asset=st.selectbox('Buy asset',symbols)
    amount=st.number_input('New cash purchase ($)',min_value=0.,value=100.)
    delta=np.zeros(len(symbols)); delta[symbols.index(asset)]=amount
    new_h=holdings+delta; after=_core.risk(new_h/new_h.sum(),cov)
    exact=after['volatility']-result['volatility']
    st.write(f'After purchase: {after["volatility"]:.4%} volatility; change {100*exact:+.4f} percentage points.')
    if grad is not None:
        linear=float(_core.dollar_gradient(holdings,cov)@delta)
        st.caption(f'Local derivative approximation: {100*linear:+.4f} percentage points. Approximation error: {100*(linear-exact):+.4f} points.')

    with st.expander('See the calculation'):
        st.latex(r'w_i^{new}=(h_i+\Delta h_i)/(V+\sum_j\Delta h_j)')
        st.markdown('- $w_i^{new}$: asset $i$’s weight after the purchase; “new” is a label, not an exponent.\n- $h_i$: existing dollars held in asset $i$.\n- $\\Delta h_i$: new dollars purchased in asset $i$; $\\Delta$ means change.\n- $V$: total portfolio value before the purchase.\n- $i$ and $j$: asset indices; $\\sum_j\\Delta h_j$ is the total new money added.')
        st.write('The exact result recalculates volatility with the new weights. The derivative is a local approximation; larger purchases can make it less accurate.')
with allocation_tab:
    st.subheader('Where could a new contribution go?')
    st.write('Turn a contribution budget into a calculated purchase amount for each asset. The engine uses automatic differentiation and repeated gradient steps, adjusting each candidate to spend the budget, avoid selling, and respect your final concentration limit while minimizing estimated variance. Enter your contribution and weight limit below, then inspect the purchase table and resulting risk; this objective does not maximize returns or guarantee future results.')
    budget=st.number_input('Total contribution ($)',min_value=0.,value=200.)
    cap=st.slider('Maximum post-contribution weight per asset',min_value=0.01,max_value=1.,value=.60,step=.01)
    try:
        with st.spinner('Checking constraints and minimizing estimated variance…'):
            allocation=_core.allocate(holdings,budget,cov,np.full(len(symbols),cap))
        if not allocation['converged']:
            st.warning('The solver did not finish. No allocation recommendation is shown; change the inputs and try again.')
            raise ValueError('Optimization has not converged.')
        show_frame(pd.DataFrame({'Asset':symbols,'Purchase dollars':allocation['purchases'],'Resulting weight':allocation['weights']}).set_index('Asset'),width='stretch')
        st.write(f"Allocated volatility: {np.sqrt(allocation['variance']):.4%}. Variance improvement over a feasible projected-equal-purchase baseline: {allocation['improvement']:.6g}.")
        st.caption('Lower estimated variance is the objective. This does not maximize returns or guarantee lower future risk.')
        with st.expander('How the allocation is calculated'):
            st.write('1. Check whether purchases can satisfy the limit.\n2. Search for purchases that reduce variance.\n3. Verify the budget, caps, and convergence.')
            st.latex(r'\min_{x}\; w(x)^T\Sigma w(x),\quad w(x)=(h+x)/(V+B)')
            st.markdown('- $x$: vector of purchase dollars, one entry per asset.\n- $h$: vector of existing dollar holdings.\n- $V$: existing total portfolio value.\n- $B$: total contribution to distribute.\n- $w(x)$: portfolio weights resulting from purchases $x$.\n- $\\min_x$: choose feasible purchases $x$ that make the objective as small as possible.\n- $T$: transpose; it turns the weight column into a row.')
            st.caption('Purchases are nonnegative, add up to the contribution, and keep each final weight within the limit.')
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
            show_frame(pd.DataFrame(comparisons),width='stretch')
            st.caption('Allocation differences across models are sensitivity results, not a calibrated confidence interval.')
    except ValueError as exc: st.error(f'No feasible allocation: {exc}')
with history_tab:
    st.subheader('Check the model against history')
    st.write('Explore whether risk estimates and contribution allocations held up on later historical observations. The engine fits each model on preceding data, evaluates subsequent returns, and compares optimized contributions with equal-dollar purchases using the same cash flows. Load market data, then run either study below and compare risk, returns, and drawdowns; these experiments do not establish future performance.')
    if returns is not None:
        with st.expander('Does estimated risk match later observations?'):
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
                    show_frame(summary,width='stretch')
                    st.caption('Calibration ratio = realized / estimated annual variance. A ratio near one on this short sample does not establish predictive accuracy.')
                    show_frame(rows.drop(columns=['weights']),width='stretch')
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
                        if prepared.dropped_return_dates:
                            raise ValueError('Backtests require complete adjacent-session history; missing daily returns cannot be skipped.')
                        backtest=contribution_backtest(returns)
                    metrics=pd.DataFrame({name:backtest[name] for name in ('optimized','equal_purchases')}).T.rename(index={'optimized':'Minimum-variance purchases','equal_purchases':'Equal-dollar purchases'},columns={'terminal_wealth':'Ending value ($)','time_weighted_return':'Return excluding deposits','annualized_volatility':'Annual volatility','max_drawdown':'Largest decline'})
                    show_frame(metrics,width='stretch',column_config={k:st.column_config.NumberColumn(format='percent') for k in ('Return excluding deposits','Annual volatility','Largest decline')})
                    st.write(f"{backtest['observations']} evaluated observations; {len(backtest['decisions'])} contributions totaling {backtest['total_contributions']:,.2f} dollars.")
                    ledger=pd.DataFrame(backtest['ledger']).set_index('date')
                    chart_data=ledger[['wealth','equal_purchase_wealth']].rename(columns={'wealth':'Minimum-variance purchases','equal_purchase_wealth':'Equal-dollar purchases'}).reset_index().melt('date',var_name='Strategy',value_name='Value')
                    show_chart(alt.Chart(chart_data).mark_line().encode(x=alt.X('date:T',title='Date'),y=alt.Y('Value:Q',title='Portfolio value ($)'),color=alt.Color('Strategy:N',scale=alt.Scale(range=['#70D0D8','#E8AA65'])),tooltip=['date:T','Strategy',alt.Tooltip('Value:Q',format=',.2f')]))
                    st.caption('Terminal wealth includes deposits. Time-weighted return removes the direct effect of deposits; volatility and drawdown use the daily time-weighted return series.')
                    st.json({k:v for k,v in backtest.items() if k not in ('ledger','decisions','optimized','equal_purchases')})
                except ValueError as exc:
                    st.error(f'Backtest unavailable: {exc}')
    else:
        st.info('Historical checks need market observations. Choose Alpaca market data in the sidebar and retrieve history to begin.')
