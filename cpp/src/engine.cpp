#include "portfolio_risk/engine.hpp"
#include <Eigen/Eigenvalues>
#include <algorithm>
#include <limits>

namespace portfolio_risk {
namespace {
void finite_vector(const Vector& v) {
    if (v.size()==0 || !v.allFinite()) throw std::invalid_argument("expected nonempty finite vector");
}
void weights(const Vector& w) {
    finite_vector(w);
    if (w.minCoeff()<0 || std::abs(w.sum()-1)>1e-12)
        throw std::invalid_argument("weights must be nonnegative and sum to one");
}
ad::Variable quadratic(const std::vector<ad::Variable>& w,const Matrix& s) {
    auto tape=w[0].owner;
    auto sum=tape->variable(0);
    for (Eigen::Index i=0;i<s.rows();++i)
        for (Eigen::Index j=0;j<s.cols();++j)
            sum=sum+w[i]*w[j]*tape->variable(s(i,j));
    return sum;
}
Vector to_vector(const std::vector<double>& x) {
    return Eigen::Map<const Vector>(x.data(),static_cast<Eigen::Index>(x.size()));
}
Vector ad_variance_gradient(const Vector& w,const Matrix& s) {
    auto tape=ad::Tape::create(); std::vector<ad::Variable> inputs;
    for (double v:w) inputs.push_back(tape->variable(v));
    return to_vector(tape->gradient(quadratic(inputs,s),inputs));
}
}
Matrix covariance(const Matrix& input,std::size_t n,double* correction) {
    if (input.rows()==0 || input.rows()!=input.cols() || input.rows()!=static_cast<Eigen::Index>(n) || !input.allFinite())
        throw std::invalid_argument("covariance dimensions or values invalid");
    const double scale=input.cwiseAbs().maxCoeff();
    const double tol=100*input.rows()*std::numeric_limits<double>::epsilon()*scale;
    if ((input-input.transpose()).cwiseAbs().maxCoeff()>tol)
        throw std::invalid_argument("covariance is not symmetric");
    Matrix s=input/2+input.transpose()/2;
    Eigen::SelfAdjointEigenSolver<Matrix> eigen(s);
    if(eigen.info()!=Eigen::Success) throw std::runtime_error("covariance eigensolver failed");
    if(eigen.eigenvalues().minCoeff() < -tol) throw std::invalid_argument("covariance is not PSD");
    if(eigen.eigenvalues().minCoeff()<0)
        s=eigen.eigenvectors()*eigen.eigenvalues().cwiseMax(0).asDiagonal()*eigen.eigenvectors().transpose();
    if(correction) *correction=(s-input).norm();
    return s;
}
Risk risk(const Vector& w,const Matrix& input,bool autodiff) {
    weights(w); double correction=0; Matrix s=covariance(input,w.size(),&correction);
    const Vector sw=s*w;
    const double v=std::max(0.0,w.dot(sw));
    if(!std::isfinite(v)) throw std::overflow_error("nonfinite variance");
    const double sigma=std::sqrt(v);
    if(sigma==0) return {v,0,std::nullopt,std::nullopt,correction};
    Vector g;
    if(autodiff) {
        auto tape=ad::Tape::create(); std::vector<ad::Variable> inputs;
        for(double x:w) inputs.push_back(tape->variable(x));
        g=to_vector(tape->gradient(tape->sqrt(quadratic(inputs,s)),inputs));
    } else g=sw/sigma;
    return {v,sigma,g,(w.array()*g.array()).matrix(),correction};
}
Vector dollar_gradient(const Vector& h,const Matrix& input) {
    finite_vector(h); const double total=h.sum();
    if(h.minCoeff()<0 || !std::isfinite(total) || total<=0)
        throw std::invalid_argument("holdings require finite positive total and no shorts");
    Matrix s=covariance(input,h.size());
    if(risk(h/total,s).volatility==0) throw std::domain_error("zero volatility derivative unavailable");
    auto tape=ad::Tape::create(); std::vector<ad::Variable> inputs,normalized;
    auto denominator=tape->variable(0);
    for(double x:h) { inputs.push_back(tape->variable(x)); denominator=denominator+inputs.back(); }
    for(const auto& x:inputs) normalized.push_back(x/denominator);
    return to_vector(tape->gradient(tape->sqrt(quadratic(normalized,s)),inputs));
}
double shrinkage_sensitivity(const Vector& w,const Matrix& input,double alpha) {
    weights(w); Matrix s=covariance(input,w.size());
    if(!std::isfinite(alpha)||alpha<0||alpha>1) throw std::invalid_argument("alpha outside [0,1]");
    const double mu=s.trace()/s.rows();
    auto tape=ad::Tape::create(); auto a=tape->variable(alpha); auto one=tape->variable(1);
    auto q=tape->variable(0);
    for(Eigen::Index i=0;i<s.rows();++i) for(Eigen::Index j=0;j<s.cols();++j) {
        auto entry=(one-a)*tape->variable(s(i,j))+a*tape->variable(i==j?mu:0);
        q=q+tape->variable(w[i]*w[j])*entry;
    }
    return tape->gradient(tape->sqrt(q),{a})[0];
}
Vector project_capped_simplex(const Vector& z,const Vector& upper,double budget) {
    finite_vector(z); finite_vector(upper);
    if(z.size()!=upper.size()||upper.minCoeff()<0||!std::isfinite(budget)||budget<0||!std::isfinite(upper.sum()))
        throw std::invalid_argument("invalid projection bounds or budget");
    const double capacity=upper.sum();
    if(capacity<budget) throw std::invalid_argument("infeasible capped simplex");
    if(budget==0) return Vector::Zero(z.size());
    if(capacity==budget) return upper;
    // Shift and rescale before bisection, keeping interval arithmetic bounded.
    const double scale=std::max({z.cwiseAbs().maxCoeff(),upper.maxCoeff(),budget});
    Vector zs=z/scale, us=upper/scale;
    const double b=budget/scale;
    double lo=(zs-us).minCoeff(), hi=zs.maxCoeff();
    Vector x;
    for(int k=0;k<160;++k) {
        double mid=lo+(hi-lo)/2;
        x=(zs.array()-mid).max(0).min(us.array());
        if(x.sum()>b) lo=mid; else hi=mid;
    }
    x=((zs.array()-(lo+(hi-lo)/2)).max(0).min(us.array())*scale).matrix();
    // Remove the last few ulps of budget residual without violating the box.
    double residual=budget-x.sum();
    for(Eigen::Index i=0;i<x.size() && residual!=0;++i) {
        double delta=std::clamp(residual,-x[i],upper[i]-x[i]);
        x[i]+=delta; residual=budget-x.sum();
    }
    return x;
}
Allocation allocate(const Vector& h,double budget,const Matrix& input,const Vector& caps,
                    double tolerance,int max_iterations,bool autodiff) {
    finite_vector(h); finite_vector(caps);
    if(h.size()!=caps.size()||h.minCoeff()<0||caps.minCoeff()<0||caps.maxCoeff()>1||
       !std::isfinite(budget)||budget<0||!std::isfinite(tolerance)||tolerance<=0||max_iterations<1)
        throw std::invalid_argument("invalid allocation inputs");
    const double total=h.sum()+budget;
    if(!std::isfinite(total)||total<=0) throw std::invalid_argument("positive total wealth required");
    Matrix s=covariance(input,h.size()); Vector lower=h/total, upper=caps-lower;
    const double b=budget/total;
    const double eps=1e-12;
    if(upper.minCoeff() < -eps || upper.sum() < b-eps) throw std::invalid_argument("infeasible concentration bounds");
    upper=upper.cwiseMax(0);
    if(upper.sum()<b) throw std::invalid_argument("insufficient capacity at floating-point precision");
    // Optimize post-contribution weights; y is the incremental weight vector.
    Vector y=project_capped_simplex(Vector::Constant(h.size(),b/h.size()),upper,b);
    const double baseline=(lower+y).dot(s*(lower+y));
    Eigen::SelfAdjointEigenSolver<Matrix> eigen(s);
    const double spectral=eigen.eigenvalues().maxCoeff();
    Matrix scaled=s;
    if(spectral>0) scaled/=spectral;
    double scaled_residual=0; bool converged=false; int iterations=0;
    auto grad=[&](const Vector& w)->Vector {
        return autodiff?ad_variance_gradient(w,scaled):(2*scaled*w).eval();
    };
    if(budget==0 || spectral==0) { converged=true; }
    else for(int k=0;k<max_iterations;++k) {
        Vector next=project_capped_simplex((y-.5*grad(lower+y)).eval(),upper,b);
        scaled_residual=2*(y-next).norm();
        if(scaled_residual<=tolerance) { converged=true; break; }
        y=next; ++iterations;
    }
    if(spectral>0 && budget>0) {
        scaled_residual=2*(y-project_capped_simplex((y-.5*grad(lower+y)).eval(),upper,b)).norm();
        converged=scaled_residual<=tolerance;
    }
    Vector w=lower+y, x=total*y;
    const double violation=std::max({0.0,-x.minCoeff(),(w-caps).maxCoeff()});
    // Diagnostics distinguish dollar budget residual from dimensionless weight bounds.
    return {x,w,w.dot(s*w),baseline,std::abs(x.sum()-budget),violation,
            spectral*scaled_residual,scaled_residual,iterations,converged,
            converged?"projected_gradient_tolerance":"iteration_limit"};
}
}
