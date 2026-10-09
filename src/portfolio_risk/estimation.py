"""Covariance estimates with explicit normalization and annualization metadata."""
from dataclasses import dataclass
import numpy as np
from .reference import sample_covariance

@dataclass(frozen=True)
class Estimate:
    covariance: np.ndarray
    method: str
    observations: int
    normalization: str
    shrinkage: float | None
    annualization: float


def estimate_covariance(returns,method='sample',annualization=252):
    r=np.asarray(returns,dtype=float)
    sample=sample_covariance(r)  # Reuse input validation, not the C++ implementation.
    if not np.isfinite(annualization) or annualization<=0: raise ValueError('annualization must be positive')
    if method=='sample': return Estimate(sample*annualization,method,len(r),'T-1',None,annualization)
    if method!='ledoit_wolf': raise ValueError('unknown covariance estimator')
    from sklearn.covariance import LedoitWolf
    fitted=LedoitWolf(store_precision=False,assume_centered=False).fit(r)
    return Estimate(fitted.covariance_*annualization,method,len(r),'T',float(fitted.shrinkage_),annualization)
