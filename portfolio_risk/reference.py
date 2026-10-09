"""Float64 mathematical reference. Covariance inputs carry one consistent time unit.

No market data, trading, autodiff, or numerical optimizer is implemented here.
"""
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class Risk:
    variance: float
    volatility: float
    gradient: np.ndarray | None
    contributions: np.ndarray | None


def _vector(value, name):
    a = np.asarray(value, dtype=np.float64)
    if a.ndim != 1 or a.size == 0 or not np.isfinite(a).all():
        raise ValueError(f"{name} must be a nonempty finite vector")
    return a


def weights_from_dollars(holdings):
    h = _vector(holdings, "holdings")
    total = h.sum()
    if np.any(h < 0) or not np.isfinite(total) or total <= 0:
        raise ValueError("holdings must be nonnegative with finite positive total")
    return h / total


def validate_weights(weights):
    w = _vector(weights, "weights")
    if np.any(w < 0) or abs(w.sum() - 1.0) > 1e-12:
        raise ValueError("long-only weights must be nonnegative and sum to one")
    return w


def covariance_matrix(covariance, n=None):
    """Validate PSD, accepting roundoff-sized asymmetry/negative eigenvalues.

    Symmetrization and projection change inputs only within a relative tolerance
    of 100*n*eps*max(abs(S)). Material indefiniteness is rejected, never repaired.
    The returned matrix is the effective matrix used in every calculation.
    """
    s = np.asarray(covariance, dtype=np.float64)
    if s.ndim != 2 or s.shape[0] == 0 or s.shape[0] != s.shape[1]:
        raise ValueError("covariance must be a nonempty square matrix")
    if n is not None and s.shape != (n, n):
        raise ValueError("weights and covariance dimensions disagree")
    if not np.isfinite(s).all():
        raise ValueError("covariance must be finite")
    scale = float(np.max(np.abs(s)))
    tol = 100 * s.shape[0] * np.finfo(float).eps * scale
    if np.max(np.abs(s - s.T)) > tol:
        raise ValueError("covariance must be symmetric")
    s = s / 2 + s.T / 2
    eigenvalues, eigenvectors = np.linalg.eigh(s)
    if eigenvalues[0] < -tol:
        raise ValueError("covariance must be positive semidefinite")
    if eigenvalues[0] < 0:
        s = (eigenvectors * np.maximum(eigenvalues, 0)) @ eigenvectors.T
    return s


def risk(weights, covariance):
    w = validate_weights(weights)
    s = covariance_matrix(covariance, w.size)
    sw = s @ w
    v = float(w @ sw)
    if not np.isfinite(v):
        raise ValueError("variance overflowed")
    # A PSD quadratic form can be tiny negative from final dot-product roundoff.
    v = max(v, 0.0)
    sigma = float(np.sqrt(v))
    if sigma == 0:
        return Risk(v, sigma, None, None)
    gradient = sw / sigma
    return Risk(v, sigma, gradient, w * gradient)


def dollar_gradient(holdings, covariance):
    """Derivative wrt adding dollars, including the changing total denominator."""
    h = _vector(holdings, "holdings")
    w = weights_from_dollars(h)
    result = risk(w, covariance)
    if result.gradient is None:
        raise ValueError("volatility derivative is undefined at zero volatility")
    return (result.gradient - float(w @ result.gradient)) / h.sum()


def simple_returns(adjusted_prices):
    """Complete aligned positive price matrix; adjustment semantics are external."""
    p = np.asarray(adjusted_prices, dtype=np.float64)
    if p.ndim != 2 or p.shape[0] < 2 or p.shape[1] == 0:
        raise ValueError("prices require at least two rows and one asset")
    if not np.isfinite(p).all() or np.any(p <= 0):
        raise ValueError("prices must be finite and strictly positive; no imputation")
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        r = p[1:] / p[:-1] - 1.0
    if not np.isfinite(r).all():
        raise ValueError("return calculation overflowed")
    return r


def sample_covariance(returns):
    r = np.asarray(returns, dtype=np.float64)
    if r.ndim != 2 or r.shape[0] < 2 or r.shape[1] == 0:
        raise ValueError("at least two complete return observations are required")
    if not np.isfinite(r).all() or np.any(r < -1):
        raise ValueError("simple returns must be finite and at least -1")
    centered = r - r.mean(axis=0)
    return covariance_matrix(centered.T @ centered / (r.shape[0] - 1))


def shrink_covariance(covariance, alpha):
    """Fixed-alpha scaled-identity shrinkage, NOT a Ledoit-Wolf alpha estimator."""
    s = covariance_matrix(covariance)
    if not np.isfinite(alpha) or not 0 <= alpha <= 1:
        raise ValueError("alpha must lie in [0, 1]")
    target = np.trace(s) / s.shape[0] * np.eye(s.shape[0])
    return (1 - alpha) * s + alpha * target


def shrinkage_sensitivity(weights, covariance, alpha):
    """d sigma / d alpha, holding the base covariance and its target fixed."""
    w = validate_weights(weights)
    s = covariance_matrix(covariance, w.size)
    shrunk = shrink_covariance(s, alpha)
    result = risk(w, shrunk)
    if result.volatility == 0:
        raise ValueError("volatility derivative is undefined at zero volatility")
    target = np.trace(s) / s.shape[0] * np.eye(s.shape[0])
    return float(w @ (target - s) @ w) / (2 * result.volatility)


def purchase_bounds(holdings, budget, caps):
    """Return x upper bounds for sum(x)=budget; fail when no feasible purchase exists.

    caps are maximum POST-contribution weights. Cash is excluded in this model.
    """
    h = _vector(holdings, "holdings")
    c = _vector(caps, "caps")
    if h.shape != c.shape or np.any(h < 0) or np.any(c < 0) or np.any(c > 1):
        raise ValueError("invalid holdings or concentration bounds")
    if not np.isfinite(budget) or budget < 0:
        raise ValueError("budget must be finite and nonnegative")
    total = h.sum() + budget
    if not np.isfinite(total) or total <= 0:
        raise ValueError("post-contribution total must be finite and positive")
    upper = c * total - h
    # Strict feasibility in the reference. Solver residual tolerances are separate.
    if np.any(upper < 0) or upper.sum() < budget:
        raise ValueError("infeasible: current holdings exceed a cap or capacity < budget")
    return upper
