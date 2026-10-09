#include "portfolio_risk/engine.hpp"
#include <cmath>
#include <iostream>
#include <stdexcept>
using namespace portfolio_risk;
void require(bool condition) { if(!condition) throw std::runtime_error("native test failed"); }
int main() {
    auto t=ad::Tape::create(); auto x=t->variable(3); auto shared=x*x; auto y=shared+shared;
    require(t->gradient(y,{x})[0]==12); require(t->gradient(y,{x})[0]==12);
    t->clear(); bool stale=false; try { x.value(); } catch(const std::invalid_argument&) { stale=true; }
    require(stale);
    // A handle keeps the underlying tape alive after the user's tape reference ends.
    auto keeper=ad::Tape::create()->variable(7); require(keeper.value()==7);
    Matrix s(2,2); s<<.04,.006,.006,.01; Vector w(2); w<<.6,.4;
    require(std::abs(risk(w,s,true).variance-.01888)<1e-14);
    Vector h(2); h<<600,400; Vector caps(2); caps<<.6,.6;
    auto solution=allocate(h,200,s,caps);
    require(solution.converged); require(solution.budget_residual<1e-8);
    require(solution.bound_violation<1e-10); require(solution.variance<=solution.baseline_variance+1e-12);
    std::cout<<"native tape, risk and allocation checks passed\n";
}
