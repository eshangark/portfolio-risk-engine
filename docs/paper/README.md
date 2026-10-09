# Portfolio risk, sensitivity, and constrained allocation

**Living technical paper — foundation edition, 2026-10-08.**

This paper studies a chain of questions: what is being measured, how is it estimated, how does it change under a decision, and which decisions minimize the stated objective? Mathematical correctness and empirical dependability are different claims. We test the former now and will investigate the latter with versioned data later.

## Reading order

1. [Definitions, prerequisites, and risk estimation](01-risk.md)
2. [Differentiation and a worked example](02-differentiation.md)
3. [Constrained allocation](03-optimization.md)
4. [Architecture and data methodology](04-architecture.md)
5. [Numerical verification and reproducible results](05-validation.md)
6. [References and glossary](06-references.md)

**Established theory:** quadratic risk, chain rule, homogeneous-function attribution, PSD shrinkage paths, convex quadratic optimization. **Implemented:** the Python reference and offline tests linked in each chapter. **Proposed:** C++/autodiff/optimizer, provider integration, estimated shrinkage, hosted app and empirical studies. **Measured:** only the synthetic results in chapter 5 and their checked-in JSON artifact. No speed, forecast, or market-performance result is claimed.

Related work informs the project without replacing its research questions: MOSEK describes portfolio modeling and risk attribution; Ledoit–Wolf addresses covariance estimation under dimensionality; Baydin et al. explains AD; Parikh–Boyd provides the proximal framework behind projected gradient. This project contributes an educational implementation and evidence trail, not a new estimator or optimization theorem.
