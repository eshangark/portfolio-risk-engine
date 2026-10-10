# C++ numerical engine

C++17, Eigen3 and pybind11. The library implements PSD validation, risk and
attribution, an owned reverse-mode tape, dollar/shrinkage sensitivities,
capped-simplex projection and a contribution-only quadratic allocator.

The allocator uses post-contribution purchase fractions and spectral scaling;
its default gradient is computed through the tape. An analytical mode provides
an independent check. The Python reference implementation and stress tests
check gradients, feasibility, and agreement with an independent quadratic solver.

Native validation without Python:

```sh
cmake -S . -B build/native -DPORTFOLIO_BUILD_PYTHON=OFF -DPORTFOLIO_SANITIZERS=ON -DCMAKE_BUILD_TYPE=Debug
cmake --build build/native -j2
ctest --test-dir build/native --output-on-failure
```

Run these commands from the repository root. Cross-language tests compare
against NumPy, analytical formulas, finite differences and OSQP.
