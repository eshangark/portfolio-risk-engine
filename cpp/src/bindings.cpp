#include <pybind11/pybind11.h>
#include <pybind11/eigen.h>
#include <pybind11/stl.h>
#include <pybind11/operators.h>
#include "portfolio_risk/engine.hpp"
namespace py=pybind11;
namespace pr=portfolio_risk;
PYBIND11_MODULE(_core,m) {
    m.doc()="C++17 portfolio risk, reverse-mode differentiation and constrained allocation";
    m.attr("__version__")="0.3.0";
    py::class_<pr::ad::Variable>(m,"Variable")
        .def_property_readonly("value",&pr::ad::Variable::value)
        .def(py::self+py::self).def(py::self-py::self).def(py::self*py::self).def(py::self/py::self);
    py::class_<pr::ad::Tape,std::shared_ptr<pr::ad::Tape>>(m,"Tape")
        .def(py::init(&pr::ad::Tape::create))
        .def("variable",&pr::ad::Tape::variable).def("sqrt",&pr::ad::Tape::sqrt)
        .def("gradient",&pr::ad::Tape::gradient).def("clear",&pr::ad::Tape::clear)
        .def_property_readonly("size",&pr::ad::Tape::size);
    m.def("risk",[](const pr::Vector& w,const pr::Matrix& s,bool autodiff) {
        auto r=pr::risk(w,s,autodiff); py::dict d;
        d["variance"]=r.variance; d["volatility"]=r.volatility;
        d["gradient"]=r.gradient?py::cast(*r.gradient):py::none();
        d["contributions"]=r.contributions?py::cast(*r.contributions):py::none();
        d["covariance_correction"]=r.covariance_correction;
        return d;
    },py::arg("weights"),py::arg("covariance"),py::arg("autodiff")=false);
    m.def("dollar_gradient",&pr::dollar_gradient);
    m.def("shrinkage_sensitivity",&pr::shrinkage_sensitivity);
    m.def("project_capped_simplex",&pr::project_capped_simplex,py::arg("point"),py::arg("upper"),py::arg("budget")=1.0);
    m.def("allocate",[](const pr::Vector& h,double b,const pr::Matrix& s,const pr::Vector& caps,double tol,int limit,bool ad) {
        pr::Allocation r;
        { py::gil_scoped_release release; r=pr::allocate(h,b,s,caps,tol,limit,ad); }
        py::dict d;
        d["purchases"]=r.purchases; d["weights"]=r.weights; d["variance"]=r.variance;
        d["baseline_variance"]=r.baseline_variance; d["improvement"]=r.baseline_variance-r.variance;
        d["budget_residual_dollars"]=r.budget_residual; d["bound_violation"]=r.bound_violation;
        d["projected_gradient_norm"]=r.projected_gradient_norm;
        d["scaled_projected_gradient_norm"]=r.scaled_projected_gradient_norm;
        d["iterations"]=r.iterations; d["converged"]=r.converged; d["stopping_reason"]=r.stopping_reason;
        return d;
    },py::arg("holdings"),py::arg("budget"),py::arg("covariance"),py::arg("caps"),
      py::arg("tolerance")=1e-9,py::arg("max_iterations")=10000,py::arg("autodiff")=true);
}
