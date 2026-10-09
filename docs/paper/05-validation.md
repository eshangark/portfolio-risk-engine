# 5. Numerical verification and reproducible results

## What was actually run

On 2026-10-08 (America/New_York), Python 3.12.14 / NumPy 2.3.5 on macOS arm64 ran all 13 reference tests successfully. This establishes the enumerated numerical properties on synthetic fixtures. It does not establish live-data quality, C++ correctness, optimizer convergence or forecasting ability.

From the repository root:

```sh
python -m unittest discover -s tests -v
python -m examples.two_asset --output work/two-asset.json
```

The checked-in [JSON report](../results/two-asset.json) contains parameters, synthetic data identity, source hashes and environment. It was produced before the initial project commit, so the source hashes identify the evaluated code. Later runs record a Git revision when available. A revision alone may not describe uncommitted changes; retain the hashes.

| Test family | Independent evidence |
| --- | --- |
| Two-asset risk | Hand expansion gives variance .01888 |
| Gradient and feasible transfer | Central differences over several step sizes |
| Dollar purchase | Perturb dollar holdings and recompute normalization |
| Single asset / perfect correlation | Closed-form volatility .2 / .16 |
| Attribution | Sum of contributions equals volatility |
| Permutation / covariance scaling | Consistent reordering and square-root scaling |
| Singular / nearly singular | Known valid matrices are accepted |
| Zero volatility | Value returned; standard gradient marked unavailable |
| Invalid inputs | Shape, nonfinite, weights, symmetry and PSD rejection |
| Sample covariance | Hand matrix and independent NumPy `cov` |
| Missing history | Incomplete arrays rejected; date handling pending |
| Shrinkage path | PSD endpoints and parameter finite differences |
| Allocation bounds | Feasible and impossible contribution examples |

## Tolerances and numerical interpretation

Use float64. Covariance validation tolerates asymmetry and negative eigenvalues only at $100n\epsilon_{mach}\max|S_{ij}|$. Symmetrize and clip negative eigenvalues only inside that allowance, then use the same effective matrix for risk and gradients. A materially indefinite matrix is rejected. This relative rule deliberately has no absolute floor that would hide errors at small covariance scales. The tests include a small-scale invalid matrix.

Normalization accepts a sum error of at most $10^{-12}$ and never silently renormalizes supplied weights. Dollar normalization is explicit. Hand-derived and algebraic checks use tight floating-point tolerances. Finite differences have truncation error $O(h^2)$ and cancellation error growing roughly like $O(\epsilon_{mach}/h)$. Step sweeps are more credible than one favorable step. Relative tolerances of $10^{-6}$ to $3\cdot10^{-6}$ cover the deliberately coarse largest steps; small absolute tolerances handle derivatives near zero. These thresholds are independent of future C++ results.

The use of central finite differences follows the methodology described by [PyTorch's gradcheck mechanics](https://docs.pytorch.org/docs/2.14/notes/gradcheck.html); PyTorch itself is not a dependency. No claim of uniform conditioning is made near zero volatility. Extreme overflow/underflow handling beyond current explicit checks remains a hardening task.

## Reproducible interpretation

The synthetic example gives volatility .1374045123, with contributions .1152800569 and .0221244554. The larger capital holding also has greater stand-alone variance and covariance exposure, explaining its disproportionate risk contribution. Fixed-alpha shrinkage changes model volatility from .1374045 at alpha zero to .1140175 at alpha one. This spread measures model dependence; it is not a confidence interval.

The script generates transfer comparisons for weight increments .001, .01 and .05, plus a new $100 purchase. Approximation error grows as the decision becomes less local. Compare both sign and magnitude before interpreting a derivative as a practical estimate.

## Pending empirical and engineering evidence

C++ analytical/AD/NumPy agreement; tape ownership/reset/shared-node tests; projection properties and established-solver residuals; stale responses, pagination and rate limits; known-action adjustment checks; UI tasks and deployment; multi-window real-data sensitivity; and numerical benchmarks remain pending.

For future chronological evaluation, choose parameters using information available through cutoff $t$, then evaluate over a subsequent interval. Do not choose windows using their future performance. Record point-in-time universe limitations and provider revisions; currently adjusted histories can themselves incorporate later corporate actions. Evaluate variance calibration and allocation stability separately from profitability.

Benchmark only after correctness. Compare equivalent computations to vectorized NumPy, separate binding overhead from kernel time, record dimensions, compiler flags, BLAS/thread settings, CPU and repeated timings. A C++ implementation may have no speed advantage for small portfolios. No performance result is claimed yet.

## Comprehension questions

1. Why does a 60% capital holding contribute about 84% of volatility in the example?
2. Why is the derivative of a new dollar purchase $(g_j-\sigma)/V$ rather than $g_j/V$?
3. Why can a singular covariance be valid, and why does that complicate comparing optimizer weights?
4. Which assumptions justify square-root-of-time annualization, and what would serial dependence change?

Next milestone: package the C++ risk core, bind it to Python, compare with this reference on Linux, and complete a private hosted smoke test before building the custom tape.
