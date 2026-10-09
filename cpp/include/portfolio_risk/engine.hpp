#pragma once
#include <Eigen/Core>
#include <optional>
#include <string>
#include "autodiff.hpp"
namespace portfolio_risk {
using Vector = Eigen::VectorXd;
using Matrix = Eigen::MatrixXd;
struct Risk {
    double variance, volatility;
    std::optional<Vector> gradient, contributions;
    double covariance_correction;
};
struct Allocation {
    Vector purchases, weights;
    double variance, baseline_variance, budget_residual, bound_violation;
    double projected_gradient_norm, scaled_projected_gradient_norm;
    int iterations;
    bool converged;
    std::string stopping_reason;
};
Matrix covariance(const Matrix&, std::size_t n, double* correction=nullptr);
Risk risk(const Vector&,const Matrix&,bool autodiff=false);
Vector dollar_gradient(const Vector&,const Matrix&);
double shrinkage_sensitivity(const Vector&,const Matrix&,double alpha);
Vector project_capped_simplex(const Vector&,const Vector&,double budget=1.0);
Allocation allocate(const Vector&,double budget,const Matrix&,const Vector& caps,
                    double tolerance=1e-9,int max_iterations=10000,bool autodiff=true);
}
