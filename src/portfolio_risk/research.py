"""Chronologically separated covariance/allocation evaluation, no trading simulation."""
import numpy as np
import pandas as pd
from .estimation import estimate_covariance


def chronological_study(returns, windows=(63,126,252), horizon=21, budget=200., cap=1., allocator=None):
    """Independent contribution decisions with fixed initial holdings at each cutoff.

    Fit on the preceding window, evaluate only the next nonoverlapping block.
    This is constant-weight variance calibration, not a cumulative strategy P&L.
    Data-vintage/survivorship bias is not cured by chronological slicing.
    """
    if allocator is None:
        from ._core import allocate
        allocator=allocate
    if not isinstance(returns,pd.DataFrame) or not isinstance(returns.index,pd.DatetimeIndex):
        raise ValueError('Returns require a dated DataFrame.')
    if returns.index.hasnans or not returns.index.is_unique or not returns.index.is_monotonic_increasing:
        raise ValueError('Return dates must be valid, unique and increasing.')
    values=returns.to_numpy(dtype=float)
    if values.ndim!=2 or values.shape[1]==0 or not np.isfinite(values).all(): raise ValueError('Finite nonempty returns required.')
    if not windows or any(not isinstance(w,int) or w<2 for w in windows): raise ValueError('Windows must be integers >=2.')
    if not isinstance(horizon,int) or horizon<2 or len(values)<max(windows)+horizon: raise ValueError('Insufficient history or invalid horizon.')
    if not np.isfinite(budget) or budget<0 or not np.isfinite(cap) or not 0<cap<=1: raise ValueError('Invalid allocation settings.')
    n=values.shape[1]; holdings=np.full(n,100.); rows=[]
    previous={}
    for cutoff in range(max(windows),len(values)-horizon+1,horizon):
        future=values[cutoff:cutoff+horizon]
        for window in windows:
            train=values[cutoff-window:cutoff]
            for method in ('sample','ledoit_wolf'):
                estimate=estimate_covariance(train,method)
                solution=allocator(holdings,budget,estimate.covariance,np.full(n,cap))
                if not solution['converged']: raise ValueError('Study solve did not converge; no empirical result emitted.')
                weights=np.asarray(solution['weights'])
                realized=float(np.var(future@weights,ddof=1)*252)
                key=(window,method); old=previous.get(key); previous[key]=weights.copy()
                rows.append({'train_start':str(returns.index[cutoff-window]),'train_end':str(returns.index[cutoff-1]),
                    'test_start':str(returns.index[cutoff]),'test_end':str(returns.index[cutoff+horizon-1]),
                    'window':window,'horizon':horizon,'method':method,'shrinkage':estimate.shrinkage,
                    'predicted_annual_variance':solution['variance'],'realized_annual_variance':realized,
                    'calibration_ratio':realized/solution['variance'] if solution['variance']>0 else None,
                    'allocation_l1_change':float(np.abs(weights-old).sum()) if old is not None else None,
                    'weights':weights.tolist(),'converged':True,
                    'scaled_projected_gradient_norm':solution['scaled_projected_gradient_norm']})
    return {'design':'Independent fixed-holdings contribution decisions; constant-weight variance evaluation',
            'initial_dollars_per_asset':100.,'contribution':budget,'cap':cap,
            'annualization':252,'overlapping_test_blocks':False,'results':rows}
