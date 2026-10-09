import unittest
import numpy as np
import pandas as pd
from portfolio_risk.research import chronological_study


class ResearchTests(unittest.TestCase):
    def test_chronological_separation_and_future_invariance(self):
        rng=np.random.default_rng(45)
        r=pd.DataFrame(rng.normal(scale=.01,size=(90,3)),index=pd.bdate_range('2025-01-01',periods=90))
        a=chronological_study(r,windows=(20,40),horizon=10)
        changed=r.copy(); changed.iloc[40:]*=3
        b=chronological_study(changed,windows=(20,40),horizon=10)
        self.assertEqual(len(a['results']),20)
        for row in a['results']: self.assertLess(pd.Timestamp(row['train_end']),pd.Timestamp(row['test_start']))
        for first,second in zip(a['results'][:4],b['results'][:4]):
            np.testing.assert_array_equal(first['weights'],second['weights'])
            self.assertEqual(first['predicted_annual_variance'],second['predicted_annual_variance'])
            self.assertAlmostEqual(second['realized_annual_variance'],9*first['realized_annual_variance'])
    def test_bad_dates_fail(self):
        r=pd.DataFrame(np.ones((40,2)),index=pd.to_datetime(['2025-01-01']*40))
        with self.assertRaises(ValueError): chronological_study(r,windows=(20,),horizon=10)

if __name__=='__main__': unittest.main()
