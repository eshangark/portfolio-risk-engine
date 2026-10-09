# 6. References and glossary

Sources consulted on 2026-10-08. Documentation is mutable; recheck when implementing integrations. Entries distinguish material actually consulted from full proofs not yet reviewed.

1. **MOSEK, Portfolio Optimization Cookbook**, [chapter 2](https://docs.mosek.com/portfolio-cookbook/markowitz.html), and [chapter 9](https://docs.mosek.com/portfolio-cookbook/risk_parity.html). Consulted portfolio formulation and Euler attribution. Our contribution-only allocation is a project-specific specialization.
2. **Olivier Ledoit and Michael Wolf (2004)**, “A well-conditioned estimator for large-dimensional covariance matrices,” *Journal of Multivariate Analysis* 88(2), 365–411, [DOI 10.1016/S0047-259X(03)00096-4](https://www.sciencedirect.com/science/article/pii/S0047259X03000964). Publisher abstract and indexed author-paper introduction consulted for motivation and scope of asymptotic covariance-loss claims. Full proof review remains pending; author-hosted PDF retrieval was unsuccessful. No theorem from the unread proof is claimed as newly verified.
3. **scikit-learn**, [LedoitWolf API](https://scikit-learn.org/stable/modules/generated/sklearn.covariance.LedoitWolf.html). Consulted the scaled-identity formula and centering contract. Planned independent estimator baseline; normalization and version-specific behavior must be tested during milestone 4.
4. **Atılım Güneş Baydin, Barak A. Pearlmutter, Alexey Andreyevich Radul, Jeffrey Mark Siskind (2018)**, “Automatic Differentiation in Machine Learning: a Survey,” *JMLR* 18(153), 1–43. [Publisher record](https://www.jmlr.org/beta/papers/v18/17-468.html), [paper](https://jmlr.org/papers/volume18/17-468/17-468.pdf). Consulted section 3, reverse traversal and accumulation. Its title does not imply machine learning is part of our project.
5. **Neal Parikh and Stephen Boyd (2014)**, “Proximal Algorithms,” *Foundations and Trends in Optimization* 1(3), 127–239. [Author-hosted paper](https://web.stanford.edu/~boyd/papers/pdf/prox_algs.pdf). Consulted projected gradient as proximal gradient for a set indicator; project-specific capped-simplex derivation is provided in chapter 3.
6. **PyTorch**, [Gradcheck mechanics](https://docs.pytorch.org/docs/2.14/notes/gradcheck.html). Consulted central finite differences and analytical comparison. Reference tests do not use PyTorch.
7. **pybind11**, [official documentation](https://pybind11.readthedocs.io/en/stable/). Consulted C++/Python integration overview; binding ownership and build-system details require implementation-stage review.
8. **Alpaca**, [Market Data API overview](https://docs.alpaca.markets/us/docs/about-market-data-api) and [historical bars endpoint](https://docs.alpaca.markets/us/reference/stockbars). Consulted feed/access distinctions, pagination and adjustment options. Data entitlement and display/redistribution terms are not yet validated.
9. **Streamlit**, [Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud), [privacy/sharing](https://docs.streamlit.io/deploy/streamlit-community-cloud/share-your-app), and [dependencies](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies). Consulted private-app allowance and Linux dependency mechanism. No hosted build has been performed.

## Glossary

| Term | Meaning here |
| --- | --- |
| Covariance | Expected product of centered returns |
| PSD | Every quadratic form is nonnegative |
| Eigenvalue | Variance scaling along an eigenvector direction |
| Conditioning | Sensitivity of a numerical problem to input perturbations |
| Shrinkage | Blend an estimate with a structured target |
| Gradient | Vector of unconstrained coordinate derivatives |
| Directional derivative | Local change along a specified direction |
| Adjoint | Derivative of the output with respect to an intermediate node |
| Tape | Stored computational graph and intermediate values |
| Projection | Nearest feasible point in the chosen norm |
| KKT conditions | Feasibility, stationarity, multiplier signs and complementarity |
| Residual | Quantified violation of a constraint or optimality condition |
| Annualization | Conversion under declared time-aggregation assumptions |
| Sensitivity | Change under specified perturbations, not a confidence interval |
