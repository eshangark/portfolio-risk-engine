"""C++ vs independent formulas, NumPy, finite differences and OSQP."""
import gc
import unittest
import numpy as np
from numpy.testing import assert_allclose
from scipy import sparse
import osqp
from portfolio_risk import _core as core
from portfolio_risk import reference as ref
S=np.array([[.04,.006],[.006,.01]])
W=np.array([.6,.4])

class EngineTests(unittest.TestCase):
    def test_cpp_matches_independent_reference(self):
        rng=np.random.default_rng(943)
        for n in (1,2,5,12):
            for rank in (1,n):
                a=rng.normal(size=(n,rank)); s=a@a.T/100; w=rng.dirichlet(np.ones(n))
                expected=ref.risk(w,s)
                for ad in (False,True):
                    actual=core.risk(w,s,autodiff=ad)
                    assert_allclose(actual['variance'],expected.variance,rtol=1e-10,atol=1e-13)
                    assert_allclose(actual['gradient'],expected.gradient,rtol=1e-9,atol=1e-11)
                    assert_allclose(sum(actual['contributions']),actual['volatility'],rtol=1e-10)
    def test_decision_and_parameter_gradients(self):
        h=np.array([600.,400.])
        assert_allclose(core.dollar_gradient(h,S),ref.dollar_gradient(h,S),rtol=1e-12)
        for a in (0,.25,.8,1):
            assert_allclose(core.shrinkage_sensitivity(W,S,a),ref.shrinkage_sensitivity(W,S,a),rtol=1e-12)
        for step in (1e-3,1e-4,1e-5):
            d=np.array([-1,1]); observed=(core.risk(W+step*d,S)['volatility']-core.risk(W-step*d,S)['volatility'])/(2*step)
            assert_allclose(observed,core.risk(W,S,True)['gradient']@d,rtol=3e-6)
    def test_tape_shared_reset_domains_and_ownership(self):
        t=core.Tape(); x=t.variable(3); q=x*x; y=q+q
        assert_allclose(t.gradient(y,[x]),[12]); assert_allclose(t.gradient(y,[x]),[12])
        z=t.variable(2); f=t.sqrt(y/z)
        assert_allclose(t.gradient(f,[x,z]),[1,-.75])
        del t; gc.collect(); self.assertEqual(y.value,18)
        t2=core.Tape(); other=t2.variable(2)
        with self.assertRaises(ValueError): _=x+other
        t2.clear()
        with self.assertRaises(ValueError): _=other.value
        zero=t2.variable(0)
        for op in (lambda:t2.sqrt(zero),lambda:zero/zero,lambda:t2.variable(float('nan'))):
            with self.assertRaises((ValueError,RuntimeError)): op()
    def test_zero_singular_invalid_inputs(self):
        for ad in (False,True):
            self.assertIsNone(core.risk(W,np.zeros((2,2)),ad)['gradient'])
            assert_allclose(core.risk(W,np.outer([.2,.1],[.2,.1]),ad)['volatility'],.16)
        for w,s in (([.5,.4],S),([-1,2],S),([1],S),(W,[[1,2],[2,1]]),(W,[[1,.1],[.2,1]]),(W,[[np.nan,0],[0,1]])):
            with self.assertRaises((ValueError,TypeError)): core.risk(w,s)
        with self.assertRaises((ValueError,RuntimeError)): core.dollar_gradient([0,0],S)
    def test_projection_properties(self):
        rng=np.random.default_rng(27)
        for n in (1,2,10):
            upper=np.full(n,2/n)
            for _ in range(10):
                z=rng.normal(size=n); x=core.project_capped_simplex(z,upper,1)
                assert_allclose(x.sum(),1,atol=1e-13)
                self.assertGreaterEqual(x.min(),0); self.assertLessEqual((x-upper).max(),1e-14)
                assert_allclose(core.project_capped_simplex(x,upper,1),x,atol=1e-13)
                feasible=core.project_capped_simplex(rng.normal(size=n),upper,1)
                self.assertLessEqual((z-x)@(feasible-x),1e-12)
        assert_allclose(core.project_capped_simplex([4,2],[.5,.5],0),[0,0])
        assert_allclose(core.project_capped_simplex([4,2],[.5,.5],1),[.5,.5])
        with self.assertRaises(ValueError): core.project_capped_simplex([0,0],[.1,.2],1)
    def test_allocator_against_osqp(self):
        rng=np.random.default_rng(120)
        for n,rank in ((2,2),(5,5),(5,2)):
            a=rng.normal(size=(n,rank)); s=a@a.T/100
            h=np.full(n,100.); b=200.; caps=np.full(n,min(1.,2/n)); total=h.sum()+b
            for use_ad in (False,True):
                actual=core.allocate(h,b,s,caps,tolerance=1e-10,max_iterations=20000,autodiff=use_ad)
                self.assertTrue(actual['converged']); self.assertLess(actual['scaled_projected_gradient_norm'],1e-10)
                self.assertLess(actual['budget_residual_dollars'],1e-8); self.assertLess(actual['bound_violation'],1e-10)
                solver=osqp.OSQP()
                solver.setup(P=sparse.csc_matrix(2*s),q=np.zeros(n),A=sparse.vstack([sparse.eye(n),sparse.csc_matrix(np.ones((1,n)))],format='csc'),
                             l=np.r_[h/total,1],u=np.r_[caps,1],eps_abs=1e-10,eps_rel=1e-10,verbose=False,polishing=True,max_iter=100000)
                expected=solver.solve(raise_error=True)
                self.assertIn(expected.info.status_val,(1,2))
                assert_allclose(actual['variance'],expected.x@s@expected.x,rtol=1e-7,atol=1e-10)
                self.assertLessEqual(actual['variance'],actual['baseline_variance']+1e-12)
    def test_allocator_special_cases(self):
        assert_allclose(core.allocate([600,400],0,S,[.6,.4])['purchases'],[0,0])
        self.assertTrue(core.allocate([600,400],200,np.zeros((2,2)),[1,1])['converged'])
        out=core.allocate([600,400],200,S,[.6,.6]); assert_allclose(out['purchases'],[0,200],atol=1e-5)
        for caps in ([.4,.6],[.6,.3]):
            with self.assertRaises(ValueError): core.allocate([600,400],200,S,caps)
        limited=core.allocate([0,0],100,S,[1,1],max_iterations=1,tolerance=1e-15)
        self.assertFalse(limited['converged']); self.assertEqual(limited['stopping_reason'],'iteration_limit')

if __name__=='__main__': unittest.main()
