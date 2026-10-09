import unittest
import numpy as np
import pandas as pd
from portfolio_risk.backtest import contribution_backtest


class BacktestTests(unittest.TestCase):
    def frame(self,values):
        return pd.DataFrame(values,index=pd.bdate_range('2020-01-01',periods=len(values)))

    def test_zero_return_cashflow_identity(self):
        report=contribution_backtest(self.frame(np.zeros((30,3))),window=10,interval=7)
        self.assertEqual(len(report['decisions']),3)
        self.assertAlmostEqual(report['total_contributions'],600)
        for name in ('optimized','equal_purchases'):
            self.assertAlmostEqual(report[name]['terminal_wealth'],1600)
            self.assertEqual(report[name]['time_weighted_return'],0)
            self.assertEqual(report[name]['max_drawdown'],0)

    def test_common_return_has_known_solution(self):
        report=contribution_backtest(self.frame(np.full((20,2),.01)),window=10,interval=5)
        expected=1200*1.01**10+200*1.01**5
        for name in ('optimized','equal_purchases'):
            self.assertAlmostEqual(report[name]['terminal_wealth'],expected,places=9)
            self.assertAlmostEqual(report[name]['time_weighted_return'],1.01**10-1,places=12)

    def test_no_lookahead_and_prefix_ledger(self):
        rng=np.random.default_rng(419); r=self.frame(rng.normal(scale=.01,size=(100,3)))
        first=contribution_backtest(r,window=30,interval=10)
        changed=r.copy(); changed.iloc[50:]*=2
        second=contribution_backtest(changed,window=30,interval=10)
        self.assertEqual(first['ledger'][:20],second['ledger'][:20])
        self.assertEqual(first['decisions'][:3],second['decisions'][:3])
        for row in first['decisions']:
            self.assertLess(pd.Timestamp(row['train_end']),pd.Timestamp(row['date']))
            self.assertAlmostEqual(sum(row['purchases']),200,places=7)
            self.assertGreaterEqual(min(row['purchases']),0)

    def test_invalid_returns_and_dates(self):
        for value in (-1,-2,np.nan,np.inf):
            r=self.frame(np.zeros((30,2))); r.iloc[-1,0]=value
            with self.assertRaises(ValueError): contribution_backtest(r,window=10)
        r=self.frame(np.zeros((30,2))); r.index=r.index[::-1]
        with self.assertRaises(ValueError): contribution_backtest(r,window=10)

    def test_unfinished_solver_suppresses_result(self):
        r=self.frame(np.zeros((30,2)))
        with self.assertRaisesRegex(ValueError,'did not converge'):
            contribution_backtest(r,window=10,allocator=lambda *args:{'converged':False})

    def test_wealth_overflow_is_rejected(self):
        values=np.zeros((20,2)); values[10:]=1e200
        with np.errstate(over='ignore',invalid='ignore'):
            with self.assertRaisesRegex(ValueError,'numerical domain'):
                contribution_backtest(self.frame(values),window=10)
