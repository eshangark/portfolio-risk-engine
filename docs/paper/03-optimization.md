# 3. Constrained allocation

## Practical question and domain

Given nonnegative dollar holdings $h\in\mathbb R^n$, wealth $V=\mathbf1^Th$, contribution $B\ge0$, and $D=V+B>0$, distribute purchases $x$ without selling. Assume a fixed PSD covariance, continuous dollar amounts, full investment of $B$ and optional post-contribution caps $c_i\in[0,1]$.

$$\min_x f(x)=\frac{(h+x)^T\Sigma(h+x)}{D^2},\qquad
\mathbf1^Tx=B,\quad 0\le x_i\le u_i=c_iD-h_i.$$

The objective has squared-return units; $x$ and $u$ are dollars. The gradient has squared-return units per dollar:

$$\nabla f(x)=\frac{2\Sigma(h+x)}{D^2},\qquad
\nabla^2 f=\frac{2\Sigma}{D^2}\succeq0.$$

PSD curvature proves convexity: along every line the second derivative is nonnegative. The box intersected with the budget hyperplane is convex and compact when feasible. A continuous objective has a minimizer there. Strict positivity of curvature on nonzero feasible directions ensures uniqueness; singular covariance can instead produce many optimal allocations. Weight agreement is consequently an inadequate solver check.

## Feasibility before optimization

With upper bounds only, feasibility is equivalent to $u_i\ge0$ for all $i$ and $\sum_i u_i\ge B$. Necessity follows by summing upper bounds; sufficiency follows by filling nonnegative capacities until $B$ is used. An existing overweight asset may become permissible after dilution by the contribution. Evaluate $h_i\le c_i(V+B)$, not $h_i/V\le c_i$.

For $h=(600,400)$, $B=200$, and $c=(.6,.6)$, $u=(120,320)$ and the budget is feasible. Tightening the first cap to .4 makes its capacity $-120$, so no purchase-only solution exists. The reference implements these checks in [`purchase_bounds`](../../src/portfolio_risk/reference.py); floating-point residual tolerances for the actual solver remain a separate design choice.

## Proposed algorithm and projection

Projected gradient is scoped, transparent, and independently testable. Start from a feasible point and iterate

$$x^{k+1}=\Pi_C(x^k-\eta\nabla f(x^k)),\quad
C=\{x:0\le x\le u,\;\mathbf1^Tx=B\}.$$

For $L=2\lambda_{max}(\Sigma)/D^2>0$, use $0<\eta\le1/L$ as an initial fixed-step design. If $L=0$, every feasible point is optimal and no reciprocal step is formed. Projected gradient is the proximal-gradient method with an indicator of the feasible set; see [Parikh and Boyd, section 4.2](https://web.stanford.edu/~boyd/papers/pdf/prox_algs.pdf).

To project a trial point $z$, minimize $\frac12\|x-z\|^2$ over $C$. Stationarity with an equality multiplier $\tau$ and box clipping yields

$$x_i(\tau)=\min\{u_i,\max\{0,z_i-\tau\}\},\quad
\sum_i x_i(\tau)=B.$$

The sum is continuous and nonincreasing. For $0<B<\sum_i u_i$, bracket $\tau$ between $\min_i(z_i-u_i)$ and $\max_i z_i$, then bisect until the budget residual meets a documented scale-aware tolerance. The projected point is unique, though the multiplier need not be. Handle $B=0$ and $B=\sum_i u_i$ directly. Validate projection feasibility, idempotence, and the variational inequality $(z-\Pi_Cz)^T(y-\Pi_Cz)\le0$ for feasible $y$.

For numerical scale, the implementation may optimize purchase fractions $y=x/B$ when $B>0$; record this decision and transform derivatives and residuals consistently. Do not use a zero gradient or tiny objective improvement alone as a stopping certificate.

## Optimality and independent validation

For the original dollar problem, KKT stationarity is

$$\nabla f+\nu\mathbf1-\lambda+\gamma=0,$$

with nonnegative multipliers, feasibility, $\lambda_ix_i=0$ and $\gamma_i(x_i-u_i)=0$. For this convex quadratic on a polyhedron, an appropriate first-order variational inequality characterizes global optima. A convenient numerical diagnostic is

$$G_\eta(x)=\frac{x-\Pi_C(x-\eta\nabla f(x))}{\eta}.$$

It vanishes exactly at a constrained optimum. Report its norm together with budget residual, maximum bound violation, iteration count, stopping reason, objective and improvement against a named feasible baseline. Specify absolute and relative tolerances in units consistent with any scaling. Compare with an established QP solver (candidate: OSQP through CVXPY; selection and independent run pending), emphasizing objective and optimality residuals when solutions are nonunique.

The C++ solver will obtain the composed objective gradient through the tape and check it against the analytical expression above. Covariance is fixed within each solve. Repeat solves for different predeclared windows and covariance estimators; assess allocation movement and objective changes. No optimizer, convergence measurement, or solver agreement is claimed in this milestone.

Minimum estimated variance ignores expected return, investor objectives, tax, fees, execution and estimation error. It answers this explicit constrained mathematical question; it does not define the best personal investment portfolio.
