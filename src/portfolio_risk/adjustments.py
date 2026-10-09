"""Independent event arithmetic for auditing provider adjustment conventions."""
import numpy as np


def audit_event(raw_before, raw_after, adjusted_before, adjusted_after,
                new_shares_per_old=1., cash_per_old_share=0., tolerance=1e-4):
    """Compare provider price ratio to holder wealth around a declared event.

    Cash is measured per pre-event share; split and cash inputs must come from
    independently checked event terms. No automatic claim of dividend reinvestment.
    """
    values=np.asarray([raw_before,raw_after,adjusted_before,adjusted_after,
                       new_shares_per_old,cash_per_old_share,tolerance],dtype=float)
    if not np.isfinite(values).all() or np.any(values[:5]<=0) or cash_per_old_share<0 or tolerance<0:
        raise ValueError('Event prices and ratio must be positive; cash and tolerance nonnegative.')
    wealth_return=(new_shares_per_old*raw_after+cash_per_old_share)/raw_before-1
    provider_return=adjusted_after/adjusted_before-1
    return {'holder_wealth_return':wealth_return,'provider_adjusted_return':provider_return,
            'difference':provider_return-wealth_return,'tolerance':tolerance,
            'matches_declared_event':bool(abs(provider_return-wealth_return)<=tolerance),
            'scope':'One declared event; not proof of total-return equivalence for all dates.'}
