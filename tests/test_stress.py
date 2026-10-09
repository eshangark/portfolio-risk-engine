"""Adversarial projections and independently certified randomized convex solves."""
import unittest
import numpy as np
from numpy.testing import assert_allclose
from scipy import sparse
import osqp
from portfolio_risk import _core as core
from portfolio_risk import reference as ref


class StressTests(unittest.TestCase):
    def test_extreme_covariance_and_dollar_scales(self):
        s=np.array([[.04,.006],[.006,.01]]); w=np.array([.6,.4]); h=np.array([600.,400.])
        expected=ref.risk(w,s)
        for scale in (1e-200,1e-100,1.,1e100,1e200):
            for ad in (False,True):
                result=core.risk(w,s*scale,ad)
                assert_allclose(result['volatility']/np.sqrt(scale),expected.volatility,rtol=1e-10)
                assert_allclose(result['gradient']/np.sqrt(scale),expected.gradient,rtol=1e-10)
            assert_allclose(core.dollar_gradient(h*scale,s)*scale,ref.dollar_gradient(h,s),rtol=1e-10)
        s=np.array([[1,-.5],[-.5,1.]])
        r=core.risk([.1,.9],s,True)
        self.assertLess(r['contributions'][0],0)
        assert_allclose(sum(r['contributions']),r['volatility'],rtol=1e-12)
        for ad in (False,True):
            self.assertIsNone(core.risk([.5,.5],[[1,-1],[-1,1]],ad)['gradient'])

    def test_projection_extreme_dynamic_range(self):
        for magnitude in (1e20,1e100,1e300):
            assert_allclose(core.project_capped_simplex([0,magnitude,magnitude],[1,1,1],1),[0,.5,.5],atol=1e-13)
            assert_allclose(core.project_capped_simplex([0,magnitude],[1,1],1),[0,1],atol=1e-13)
            assert_allclose(core.project_capped_simplex([magnitude,0],[1,1],1),[1,0],atol=1e-13)
            assert_allclose(core.project_capped_simplex([-magnitude,0,magnitude],[1,1,.25],1),[0,.75,.25],atol=1e-13)
        assert_allclose(core.project_capped_simplex([0,0],[1e308,1e308],1),[.5,.5],atol=1e-13)
        for budget in (1e-200,1e-50,1e50,1e200):
            assert_allclose(core.project_capped_simplex([0,1e300],[budget,budget],budget)/budget,[0,1],atol=1e-13)

    def test_randomized_gradient_identities(self):
        rng=np.random.default_rng(93019)
        for n in (2,3,8,16):
            for _ in range(12):
                a=rng.normal(size=(n,n)); s=a@a.T/n; w=rng.dirichlet(np.ones(n))
                h=w*1000; direction=rng.normal(size=n); direction-=direction.mean()
                step=min(1e-5,.1*np.min(w)/(np.max(np.abs(direction))+1))
                analytical=ref.risk(w,s); ad=core.risk(w,s,True)
                assert_allclose(ad['gradient'],analytical.gradient,rtol=2e-10,atol=2e-12)
                assert_allclose(sum(ad['contributions']),ad['volatility'],rtol=1e-11)
                fd=(core.risk(w+step*direction,s)['volatility']-core.risk(w-step*direction,s)['volatility'])/(2*step)
                assert_allclose(fd,analytical.gradient@direction,rtol=1e-5,atol=1e-8)
                dg=core.dollar_gradient(h,s)
                assert_allclose(dg,ref.dollar_gradient(h,s),rtol=1e-10,atol=1e-13)
                self.assertLess(abs(dg@h),1e-10)
                p=rng.permutation(n)
                assert_allclose(core.risk(w[p],s[np.ix_(p,p)],True)['gradient'],ad['gradient'][p],rtol=1e-10)

    def test_randomized_solver_and_convex_certificate(self):
        rng=np.random.default_rng(74103)
        for n in (2,3,8):
            for rank in (1,n):
                for _ in range(4):
                    a=rng.normal(size=(n,rank)); s=a@a.T
                    s/=np.linalg.eigvalsh(s)[-1]
                    h=rng.uniform(1,100,size=n); budget=rng.uniform(20,200); lower=h/(h.sum()+budget)
                    caps=lower+rng.uniform(.05,.4,size=n)
                    caps=np.minimum(1,caps+max(0,1-caps.sum())/n+.01)
                    for ad in (False,True):
                        out=core.allocate(h,budget,s,caps,tolerance=1e-9,max_iterations=50000,autodiff=ad)
                        self.assertTrue(out['converged'])
                        w=out['weights']; self.assertLess(abs(w.sum()-1),2e-12)
                        self.assertLess(out['budget_residual_dollars'],1e-8)
                        self.assertLess(out['bound_violation'],2e-12)
                        # A linear minimization oracle yields a convex upper bound
                        # on suboptimality, independently of the PG stopping test.
                        gradient=2*s@w; v=lower.copy(); remaining=1-v.sum()
                        for j in np.argsort(gradient):
                            amount=min(remaining,caps[j]-v[j]); v[j]+=amount; remaining-=amount
                        gap=float(gradient@(w-v))
                        self.assertLess(gap,1e-7); self.assertGreater(gap,-1e-11)
                        solver=osqp.OSQP()
                        solver.setup(P=sparse.csc_matrix(2*s),q=np.zeros(n),
                            A=sparse.vstack([sparse.eye(n),np.ones((1,n))],format='csc'),
                            l=np.r_[lower,1],u=np.r_[caps,1],eps_abs=1e-10,eps_rel=1e-10,
                            max_iter=100000,verbose=False,polishing=True)
                        oracle=solver.solve(raise_error=True)
                        self.assertEqual(oracle.info.status_val,1)
                        assert_allclose(out['variance'],oracle.x@s@oracle.x,rtol=1e-7,atol=1e-9)
                        self.assertLessEqual(out['variance'],out['baseline_variance']+1e-12)
