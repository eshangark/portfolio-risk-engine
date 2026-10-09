# 2. Differentiation and a worked example

## From calculus to decisions

For a fixed symmetric $\Sigma$, expand $(w+\delta)^T\Sigma(w+\delta)$ to obtain

$$v(w+\delta)=v(w)+2\delta^T\Sigma w+\delta^T\Sigma\delta.$$

Therefore $\nabla v=2\Sigma w$. Applying the scalar chain rule to $\sqrt v$ yields

$$g=\nabla_w\sigma=\frac{\Sigma w}{\sigma},\qquad \sigma>0.$$

The derivative is with respect to unconstrained coordinates even though valid portfolios lie on a simplex. A feasible first-order direction $d$ must satisfy $\mathbf1^Td=0$ and remain inside nonnegativity bounds. A transfer from A to B has $d=e_B-e_A$, so

$$\sigma(w+\epsilon d)-\sigma(w)=\epsilon(g_B-g_A)+O(\epsilon^2).$$

At a boundary a feasible direction may allow only one sign of $\epsilon$. Do not confuse this derivative with increasing B while holding all other weights fixed.

## Risk attribution

Volatility is homogeneous of degree one for positive scalings. Euler's identity gives $w^Tg=\sigma$; directly,

$$\sum_i RC_i=\sum_i w_i\frac{(\Sigma w)_i}{\sigma}
=\frac{w^T\Sigma w}{\sigma}=\sigma.$$

$RC_i$ has the same units as volatility. Capital share $w_i$ and risk share $RC_i/\sigma$ answer different questions. Contributions can be negative, even in a long-only portfolio, if covariance gives a sufficiently strong hedge; they are an attribution, not independent stand-alone risks. The attribution framework is described in [MOSEK's risk budgeting chapter](https://docs.mosek.com/portfolio-cookbook/risk_parity.html).

## New cash changes the denominator

For dollar holdings $h$, $H=\sum_i h_i>0$, and $w=h/H$:

$$\frac{\partial w_i}{\partial h_j}=\frac{\delta_{ij}-w_i}{H},\qquad
\frac{\partial\sigma}{\partial h_j}=\frac{g_j-w^Tg}{H}=\frac{g_j-\sigma}{H}.$$

The units are volatility per dollar. This derivative includes the effect on all weights. Adding dollars proportionally to every existing holding leaves weights unchanged: $h^T\nabla_h\sigma=0$. A transfer of $b$ dollars keeps total wealth constant and instead has derivative $b(g_B-g_A)/H$.

For a fixed contribution $B$ fully distributed through purchases $x$, the feasible total is constant: $w(x)=(h+x)/(V+B)$. Its objective gradient in purchase coordinates is $2\Sigma(h+x)/(V+B)^2$. Off the budget constraint, that fixed-denominator extension is a computational definition, not the normalization for arbitrary additional wealth. Both give the same directional derivative along feasible transfers of purchases.

## Hand-worked example

Take $w=(.6,.4)$ and annual $\Sigma=\begin{pmatrix}.04&.006\\.006&.01\end{pmatrix}$. The asset volatilities are .2 and .1; the implied correlation is $.006/(.2\cdot.1)=.3$.

$$\Sigma w=(.0264,.0076),\quad
v=.6^2(.04)+2(.6)(.4)(.006)+.4^2(.01)=.01888.$$

Thus $\sigma=0.1374045123$, $g=(.1921334282,.0553111384)$, and $RC=(.1152800569,.0221244554)$. A accounts for 83.8983% of total volatility attribution despite holding 60% of capital.

A transfer of one percentage point of portfolio weight from A to B has linear change $-.0013682229$ and exact change $-.0013611369$ in volatility units. Multiply by 100 to express volatility percentage points: approximately $-.13682$ versus $-.13611$.

Start with $h=(600,400)$ dollars and buy $100$ of B using new cash. Weights become $(600/1100,500/1100)$. Exact volatility change is $-.0072425026$ versus the local dollar approximation $-.0082093374$. A 10% wealth increase is large enough that the approximation error is visible. The conclusion concerns percentage-return volatility; dollar risk can increase when invested wealth grows.

## Sensitivity to a valid covariance path

Keep base $S$, target $F=\mu I$, and weights fixed. On $S_\alpha=(1-\alpha)S+\alpha F$:

$$\frac{\partial\sigma}{\partial\alpha}=\frac{w^T(F-S)w}{2\sigma}.$$

Only $\alpha\in[0,1]$ is admitted. At endpoints use admissible one-sided perturbations for checks. This derivative does not differentiate the estimated Ledoit–Wolf coefficient with respect to data. Changing a single correlation arbitrarily can destroy PSD; use model-valid paths instead.

## Proposed custom reverse mode

Store an owned tape of nodes with values, adjoints and parent indices. Evaluate operations forward; initialize output adjoint to one; traverse backward and add local-chain-rule contributions to parents. For $z=u v$, accumulate $\bar u\mathrel{+}=\bar z v$ and $\bar v\mathrel{+}=\bar z u$. Addition, subtraction, multiplication, division and square root suffice initially. If $u=v$, both edge contributions must accumulate. This is the core distinction from overwriting a gradient.

A tape owns node storage; handles carry tape identity and generation to reject cross-tape mixing or use after reset. Reverse passes must zero previous adjoints. Repeated evaluation must update values before using local derivatives; the first implementation may rebuild the graph per calculation. Division by zero, square root of negative values and nonfinite values fail explicitly. At zero volatility return the value and mark its usual derivative unavailable, even when a special constant-zero model admits a derivative.

AD evaluates derivatives of the implemented arithmetic graph up to floating-point effects; it does not cure statistical model error. The closed-form volatility gradient is simple and remains an independent oracle. AD supplies implementation depth and handles composed normalization and parameter paths. See [Baydin et al., section 3](https://jmlr.org/papers/volume18/17-468/17-468.pdf).

Implemented: `risk`, `dollar_gradient`, `shrinkage_sensitivity` in [reference.py](../../src/portfolio_risk/reference.py). Checks: analytical hand values, identities and multiple finite-difference step sizes in [tests](../../tests/test_reference.py). Custom tape, memory checks and cross-language comparisons are pending.
