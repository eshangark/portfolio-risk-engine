# 1. Definitions, prerequisites, and risk estimation

## Practical question

How much dispersion does a fixed portfolio have under an estimated covariance model, and which assumptions enter that estimate?

For asset $i$, a simple one-period return is $r_{t,i}=P^*_{t,i}/P^*_{t-1,i}-1$. Here $P^*$ denotes a positive, consistently adjusted historical price series whose economic interpretation has been checked. This notation alone does not establish that dividends are reinvested. Current holdings require a separate unadjusted valuation price.

Let $r_t\in\mathbb R^n$, $w\in\mathbb R^n$, $w_i\ge0$ and $\mathbf1^Tw=1$. Returns and weights are dimensionless. If $h_i$ are dollar holdings, $V=\sum_i h_i>0$ and $w_i=h_i/V$. Covariance is in squared-return units for a declared period; volatility is in return units for the same period.

Expectation is a probability-weighted average. Variance $\operatorname{Var}(X)=E[(X-E[X])^2]$ measures squared deviations around it. Covariance $\operatorname{Cov}(X,Y)=E[(X-E[X])(Y-E[Y])]$ measures joint deviations. Correlation divides covariance by the product of nonzero standard deviations. A zero-variance variable has no defined correlation coefficient under this formula.

## Portfolio quadratic form

With fixed weights, $r_p=w^Tr$. Expanding the square gives

$$\operatorname{Var}(r_p)=E\left[\left(\sum_i w_i(r_i-E[r_i])\right)^2\right]
=\sum_i\sum_jw_iw_j\Sigma_{ij}=w^T\Sigma w.$$

Thus $\sigma(w)=\sqrt{w^T\Sigma w}$. Covariance is symmetric and positive semidefinite (PSD): $a^T\Sigma a=\operatorname{Var}(a^Tr)\ge0$ for every real $a$. The spectral theorem writes $\Sigma=Q\Lambda Q^T$; PSD means nonnegative eigenvalues. Eigenvalues measure variance along orthogonal directions, not individual asset risks.

Singularity means some direction has zero variance under this model. For positive-definite $\Sigma$, the spectral condition number is $\lambda_{max}/\lambda_{min}$; a large ratio warns that inversion can amplify perturbations. Risk evaluation needs matrix multiplication, not inversion. Singularity is therefore valid and must not be rejected simply because a Cholesky factorization fails. See [MOSEK's portfolio formulation](https://docs.mosek.com/portfolio-cookbook/markowitz.html).

## Sample estimator and normalization

For $T\ge2$ aligned return rows, $\bar r=T^{-1}\sum_t r_t$ and centered matrix $X\in\mathbb R^{T\times n}$:

$$S=\frac{1}{T-1}X^TX.$$

This uses the sample normalization; under independent identically distributed rows with finite covariance it is unbiased. Rows of market data need not meet those assumptions. Since $a^TSa=\|Xa\|^2/(T-1)$, this construction preserves PSD. Centering implies $\operatorname{rank}(S)\le\min(n,T-1)$. Pairwise deletion with different date sets need not preserve PSD; the product must use a common set of complete daily returns.

Example with three return rows $(.01,.02),(-.01,0),(0,-.02)$ has zero mean and

$$S=\begin{pmatrix}.0001&.0001\\.0001&.0004\end{pmatrix}.$$

The reference independently matches this result and NumPy's `cov(..., ddof=1)`.

## Shrinkage and its precise status

For a PSD estimate $S$, define $\mu=\operatorname{tr}(S)/n$ and

$$S_\alpha=(1-\alpha)S+\alpha\mu I,\qquad 0\le\alpha\le1.$$

It is PSD as a convex combination of PSD matrices. If $\alpha>0$ and $\mu>0$, all eigenvalues $(1-\alpha)\lambda_i+\alpha\mu$ are positive. This improves conditioning but introduces a structured bias toward equal variances and zero covariance; it is not a guarantee of better future allocation.

**Implemented:** a user-specified $\alpha$ for valid model-parameter sensitivity. **Chosen for milestone 4:** the Ledoit–Wolf scaled-identity estimator, motivated by its estimated shrinkage coefficient and study of covariance loss as dimension and sample size grow together. Its optimality criterion is not realized portfolio returns. See [original paper](https://www.sciencedirect.com/science/article/pii/S0047259X03000964) and [implementation contract](https://scikit-learn.org/stable/modules/generated/sklearn.covariance.LedoitWolf.html).

Use scikit-learn as an independent baseline, record its estimated coefficient, and explicitly reconcile its empirical covariance normalization with the $T-1$ baseline. Do not label arbitrary fixed shrinkage Ledoit–Wolf. Shrink only the risky-asset block if an explicit cash sleeve is later added.

## Annualization and interpretation

For an additive $K$-period return sum, covariance equals $K\Sigma_d$ only if cross-period covariance terms vanish and period covariances are identical. With serial dependence the omitted cross terms matter. Annual volatility $\sqrt{252}\sigma_d$ is a convention under these assumptions, not the exact variance of compounded annual simple returns. Display both period and multiplier. The example in chapter 2 is already annual and must not be annualized again.

This is a constant-weight risk estimate. A buy-and-hold historical account has drifting weights; reproducing that path requires holdings evolution. Historical covariance estimates future risk only through a modeling assumption of relevant history. Compare predeclared windows (proposed: 63, 126, 252 completed common daily returns) and estimators, disclose effective sample sizes, and label the spread sensitivity rather than calibrated uncertainty.

Implementation: [reference.py](../../portfolio_risk/reference.py), functions `simple_returns`, `sample_covariance`, `shrink_covariance`, `risk`. Validation: [tests](../../tests/test_reference.py), including hand values, scaling, permutation, PSD rejection and singular cases. Dates, calendars and statistical estimation quality remain pending.
