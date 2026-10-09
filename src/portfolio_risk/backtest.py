"""Cash-flow-aware historical simulation of hypothetical no-sale contributions."""
import hashlib
import numpy as np
import pandas as pd
from .estimation import estimate_covariance


def contribution_backtest(returns, window=126, interval=21, method='ledoit_wolf',
                          initial_value=1000., contribution=200., allocator=None):
    """Choose before each return; drift holdings; compare equal-dollar purchases.

    Returns must be economically adjusted simple returns. No fees, taxes, spreads
    or execution model. Present-day histories do not supply point-in-time vintages.
    Caps are 100%: the no-sale constraint alone restricts each decision.
    """
    if allocator is None:
        from ._core import allocate
        allocator=allocate
    if not isinstance(returns,pd.DataFrame) or not isinstance(returns.index,pd.DatetimeIndex):
        raise ValueError('Returns require a dated DataFrame.')
    if returns.index.hasnans or not returns.index.is_unique or not returns.index.is_monotonic_increasing:
        raise ValueError('Dates must be valid, unique and increasing.')
    # Fix memory order so identical prefixes use identical BLAS reduction paths,
    # even when pandas supplies different layouts after a future-only edit.
    values=np.ascontiguousarray(returns.to_numpy(dtype=float))
    if values.ndim!=2 or values.shape[1]==0 or not np.isfinite(values).all() or np.any(values<=-1):
        raise ValueError('Finite simple returns strictly above -1 required.')
    if not isinstance(window,int) or window<2 or not isinstance(interval,int) or interval<1 or len(values)<=window:
        raise ValueError('Invalid windows or insufficient history.')
    if not np.isfinite(initial_value) or initial_value<=0 or not np.isfinite(contribution) or contribution<0:
        raise ValueError('Invalid starting value or contribution.')
    if method not in ('sample','ledoit_wolf'): raise ValueError('Unknown estimator.')
    n=values.shape[1]; holdings=np.full(n,initial_value/n); baseline=holdings.copy()
    records=[]; portfolio_returns=[]; equal_returns=[]; decisions=[]; deposits=0.
    for i in range(window,len(values)):
        if (i-window)%interval==0:
            estimate=estimate_covariance(values[i-window:i],method)
            solution=allocator(holdings,contribution,estimate.covariance,np.ones(n))
            if not solution['converged']: raise ValueError('Backtest solve did not converge; result suppressed.')
            purchase=np.asarray(solution['purchases'],dtype=float)
            if (not np.isfinite(purchase).all() or np.any(purchase < -1e-10*max(1,contribution))
                    or abs(purchase.sum()-contribution)>1e-8*max(1,contribution)):
                raise ValueError('Backtest purchase violates the cash-flow ledger.')
            holdings+=purchase; baseline+=contribution/n; deposits+=contribution
            decisions.append({'date':str(returns.index[i]),'train_end':str(returns.index[i-1]),
                'purchases':purchase.tolist(),'weights':(holdings/holdings.sum()).tolist(),
                'predicted_variance':float(solution['variance']),
                'scaled_projected_gradient_norm':float(solution['scaled_projected_gradient_norm'])})
        before=float(holdings.sum()); equal_before=float(baseline.sum())
        holdings*=1+values[i]; baseline*=1+values[i]
        if (not np.isfinite(holdings).all() or not np.isfinite(baseline).all()
                or not np.isfinite([holdings.sum(),baseline.sum()]).all()
                or min(holdings.sum(),baseline.sum())<=0):
            raise ValueError('Backtest wealth exceeds numerical domain.')
        daily=float(holdings.sum()/before-1); equal_daily=float(baseline.sum()/equal_before-1)
        if not np.isfinite([daily,equal_daily]).all(): raise ValueError('Backtest returns exceed numerical domain.')
        portfolio_returns.append(daily); equal_returns.append(equal_daily)
        records.append({'date':str(returns.index[i]),'wealth':float(holdings.sum()),
                        'equal_purchase_wealth':float(baseline.sum()),'cumulative_deposits':deposits,
                        'return':daily,'equal_purchase_return':equal_daily})
    def metrics(series,wealth):
        r=np.asarray(series); curve=np.r_[1.,np.cumprod(1+r)]
        if not np.isfinite(curve).all(): raise ValueError('Time-weighted index exceeds numerical domain.')
        return {'terminal_wealth':float(wealth),'time_weighted_return':float(curve[-1]-1),
            'annualized_volatility':float(np.std(r,ddof=1)*np.sqrt(252)) if len(r)>1 else None,
            'max_drawdown':float(np.min(curve/np.maximum.accumulate(curve)-1))}
    return {'design':'Buy-only contributions before daily returns; fixed estimator, no execution model',
        'symbols':list(map(str,returns.columns)),'window':window,'interval':interval,'method':method,
        'initial_value':initial_value,'contribution':contribution,'total_contributions':deposits,
        'observations':len(records),'annualization':252,
        'data_sha256':hashlib.sha256(returns.to_csv(float_format='%.17g').encode()).hexdigest(),
        'optimized':metrics(portfolio_returns,holdings.sum()),
        'equal_purchases':metrics(equal_returns,baseline.sum()),'decisions':decisions,'ledger':records}
