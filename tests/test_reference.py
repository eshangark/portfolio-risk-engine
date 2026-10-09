import unittest
import numpy as np
from numpy.testing import assert_allclose
from portfolio_risk.reference import (
    risk, weights_from_dollars, dollar_gradient, simple_returns,
    sample_covariance, covariance_matrix, shrink_covariance,
    shrinkage_sensitivity, purchase_bounds,
)

S = np.array([[0.04, 0.006], [0.006, 0.01]])
W = np.array([0.6, 0.4])


class RiskTests(unittest.TestCase):
    def test_hand_worked_two_assets(self):
        out = risk(W, S)
        self.assertAlmostEqual(out.variance, 0.01888, places=14)
        self.assertAlmostEqual(out.volatility, np.sqrt(0.01888), places=14)
        assert_allclose(out.gradient, np.array([0.0264, 0.0076]) / np.sqrt(0.01888))
        assert_allclose(out.contributions.sum(), out.volatility, rtol=1e-13)

    def test_gradient_against_central_differences(self):
        analytical = risk(W, S).gradient
        # Independently evaluated unconstrained quadratic form, not normalized risk().
        for step in (1e-3, 1e-4, 1e-5, 1e-6):
            numeric = []
            for axis in np.eye(2):
                a, b = W + step * axis, W - step * axis
                numeric.append((np.sqrt(a @ S @ a) - np.sqrt(b @ S @ b)) / (2 * step))
            assert_allclose(numeric, analytical, rtol=2e-6, atol=1e-10)

    def test_transfer_and_purchase_derivatives(self):
        g = risk(W, S).gradient
        d = np.array([-1., 1.])
        for step in (1e-3, 1e-4, 1e-5):
            numeric = (risk(W + step*d, S).volatility - risk(W - step*d, S).volatility)/(2*step)
            assert_allclose(numeric, g @ d, rtol=3e-6)
        holdings = np.array([600., 400.])
        dg = dollar_gradient(holdings, S)
        for step in (1., .1, .01):
            for i, axis in enumerate(np.eye(2)):
                a = weights_from_dollars(holdings + step*axis)
                b = weights_from_dollars(holdings - step*axis)
                numeric = (risk(a,S).volatility-risk(b,S).volatility)/(2*step)
                assert_allclose(numeric, dg[i], rtol=3e-6, atol=1e-12)
        self.assertLess(dg[1], 0)

    def test_single_and_perfect_correlation(self):
        self.assertAlmostEqual(risk([1], [[.04]]).volatility, .2)
        a = np.array([.2, .1])
        out = risk(W, np.outer(a,a))
        self.assertAlmostEqual(out.volatility, .16)
        assert_allclose(out.gradient, a)

    def test_permutation_and_scaling(self):
        out = risk(W, S)
        rev = risk(W[::-1], S[::-1,::-1])
        assert_allclose(rev.contributions, out.contributions[::-1])
        assert_allclose(weights_from_dollars(W*1000), W)
        for factor in (1e-12, 252., 1e12):
            scaled = risk(W, S*factor)
            assert_allclose(scaled.volatility, np.sqrt(factor)*out.volatility)
            assert_allclose(scaled.gradient, np.sqrt(factor)*out.gradient)

    def test_zero_volatility_domain(self):
        out = risk(W, np.zeros((2,2)))
        self.assertEqual(out.volatility, 0)
        self.assertIsNone(out.gradient)
        self.assertIsNone(out.contributions)
        with self.assertRaises(ValueError):
            dollar_gradient([6,4], np.zeros((2,2)))
        with self.assertRaises(ValueError):
            shrinkage_sensitivity(W, np.zeros((2,2)), .5)

    def test_singular_and_nearly_singular(self):
        for delta in (0, 1e-12):
            s = np.array([[1., 1-delta], [1-delta, 1.]])
            assert_allclose(risk([.5,.5],s).variance, 1-delta/2)
        hedged = risk([.5,.5], [[1,-1],[-1,1]])
        self.assertEqual(hedged.volatility, 0)
        self.assertIsNone(hedged.gradient)

    def test_reject_invalid_weights_and_dimensions(self):
        for w in ([.6,.5], [-.1,1.1], [np.nan,0], [], [[.6,.4]], [1]):
            with self.subTest(w=w), self.assertRaises(ValueError):
                risk(w,S)
        for h in ([0,0], [-1,2], [np.inf,1]):
            with self.assertRaises(ValueError):
                weights_from_dollars(h)

    def test_reject_invalid_covariance(self):
        for s in ([[1,2],[2,1]], [[1,.1],[.2,1]], [[np.nan,0],[0,1]], [[1,2]], []):
            with self.subTest(s=s), self.assertRaises(ValueError):
                covariance_matrix(s)
        # Small scale must not hide a materially negative eigenvalue.
        with self.assertRaises(ValueError):
            covariance_matrix(np.diag([1e-15,-1e-16]))

    def test_sample_covariance_against_numpy_and_hand_value(self):
        r = np.array([[.01,.02],[-.01,0],[0,-.02]])
        expected = np.array([[.0001,.0001],[.0001,.0004]])
        assert_allclose(sample_covariance(r), expected, rtol=1e-13)
        assert_allclose(sample_covariance(r), np.cov(r,rowvar=False,ddof=1))
        self.assertEqual(sample_covariance(r[:,:1]).shape,(1,1))

    def test_prices_and_missing_observations(self):
        assert_allclose(simple_returns([[100,50],[110,45],[99,49.5]]),[[.1,-.1],[-.1,.1]])
        for p in ([[1,2]], [[1,np.nan],[2,3]], [[0,1],[2,3]], [[-1,2],[2,3]]):
            with self.assertRaises(ValueError):
                simple_returns(p)
        for r in ([[.1,.2]], [[np.nan,.2],[.1,.2]], [[-1.1,.2],[.1,.2]]):
            with self.assertRaises(ValueError):
                sample_covariance(r)

    def test_shrinkage_psd_endpoints_and_sensitivity(self):
        assert_allclose(shrink_covariance(S,0),S)
        assert_allclose(shrink_covariance(S,1),np.eye(2)*.025)
        for alpha in (0,.2,.5,1):
            self.assertGreaterEqual(np.linalg.eigvalsh(shrink_covariance(S,alpha))[0],0)
        for step in (1e-3,1e-4,1e-5):
            num = (risk(W,shrink_covariance(S,.5+step)).volatility-risk(W,shrink_covariance(S,.5-step)).volatility)/(2*step)
            assert_allclose(num,shrinkage_sensitivity(W,S,.5),rtol=1e-6)
        for alpha in (-.1,1.1,np.nan):
            with self.assertRaises(ValueError):
                shrink_covariance(S,alpha)

    def test_concentration_feasibility(self):
        assert_allclose(purchase_bounds([600,400],200,[.6,.6]),[120,320])
        for caps in ([.4,.6],[.6,.3],[1.1,.5]):
            with self.assertRaises(ValueError):
                purchase_bounds([600,400],200,caps)
        assert_allclose(purchase_bounds([600,400],0,[.6,.4]),[0,0])
        assert_allclose(purchase_bounds([0,0],100,[.5,.5]),[50,50])
        with self.assertRaises(ValueError):
            purchase_bounds([600,400],-1,[1,1])


if __name__ == "__main__":
    unittest.main()
