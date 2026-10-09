import unittest
import numpy as np
import pandas as pd
import requests
from numpy.testing import assert_allclose
from portfolio_risk.data import AlpacaData,History,DataError,prepare_history,utc,completed_history_end
from portfolio_risk.adjustments import audit_event
from portfolio_risk.estimation import estimate_covariance

class Response:
    def __init__(self,payload,status=200,headers=None): self.payload=payload; self.status_code=status; self.headers=headers or {}
    def json(self): return self.payload
class Session:
    def __init__(self,responses): self.responses=iter(responses); self.calls=[]
    def get(self,*args,**kwargs):
        self.calls.append((args,kwargs)); response=next(self.responses)
        if isinstance(response,Exception): raise response
        return response

class DataTests(unittest.TestCase):
    def test_pagination_cache_and_adjustments(self):
        session=Session([Response({'bars':{'A':[{'t':'2026-10-01T04:00:00Z','c':10}]},'next_page_token':'p2'}),Response({'bars':{'B':[{'t':'2026-10-01T04:00:00Z','c':20}]}})])
        provider=AlpacaData('test','test',session=session,clock=lambda:1)
        first=provider.history(['A','B'],'2026-10-01T00:00Z','2026-10-08T00:00Z')
        self.assertEqual(first.adjustment,'all'); self.assertEqual(len(session.calls),2)
        self.assertEqual(session.calls[1][1]['params']['page_token'],'p2')
        cached=provider.history(['A','B'],'2026-10-01T00:00Z','2026-10-08T00:00Z')
        self.assertEqual(cached,first)
        cached.bars['A'].clear()
        self.assertEqual(len(provider.history(['A','B'],'2026-10-01T00:00Z','2026-10-08T00:00Z').bars['A']),1)
    def test_refresh_detects_old_revisions_and_removed_rows(self):
        before=[{'t':'2026-10-01T04:00Z','c':100},{'t':'2026-10-02T04:00Z','c':102}]
        after=[{'t':'2026-10-01T04:00Z','c':50},{'t':'2026-10-05T04:00Z','c':53}]
        p=AlpacaData('test','test',session=Session([Response({'bars':{'A':before}}),Response({'bars':{'A':after}})]))
        args=(['A'],'2026-10-01T00:00Z','2026-10-08T00:00Z')
        p.history(*args); updated=p.history(*args,force_refresh=True)
        self.assertEqual([updated.refresh[k] for k in ('added','removed','revised')],[1,1,1])
        self.assertEqual(updated.bars['A'],after)
    def test_event_economics(self):
        self.assertTrue(audit_event(100,50,50,50,new_shares_per_old=2)['matches_declared_event'])
        self.assertTrue(audit_event(100,99,99,99,cash_per_old_share=1)['matches_declared_event'])
        self.assertFalse(audit_event(100,50,100,50,new_shares_per_old=2)['matches_declared_event'])
        # Backward price adjustment is not generally exactly a cash-wealth return.
        self.assertFalse(audit_event(100,100,99,100,cash_per_old_share=1,tolerance=1e-6)['matches_declared_event'])
    def test_invalid_timestamps_and_pagination(self):
        for value in ('NaT','2026-10-08'):
            with self.assertRaises(DataError): utc(value)
        repeated=Response({'bars':{},'next_page_token':'same'})
        with self.assertRaises(DataError):
            AlpacaData('test','test',session=Session([repeated,repeated])).history(['A'],'2026-10-01T00:00Z','2026-10-08T00:00Z')
        self.assertEqual(completed_history_end('2026-10-08T18:00Z'),pd.Timestamp('2026-10-08T17:45Z'))
    def test_bounded_retries_and_entitlement(self):
        sleeps=[]; session=Session([Response({},429,{'Retry-After':'2'}),Response({'bars':{}})])
        provider=AlpacaData('test','test',session=session,sleep=sleeps.append)
        provider.history(['A'],'2026-10-01T00:00Z','2026-10-08T00:00Z'); self.assertEqual(sleeps,[2])
        for responses in ([Response({},403)],[requests.Timeout()]*4):
            with self.assertRaises(DataError): AlpacaData('test','test',session=Session(responses),sleep=lambda x:None).history(['A'],'2026-10-01T00:00Z','2026-10-08T00:00Z')
    def test_no_gap_bridging_and_completed_sessions(self):
        dates=['2026-10-01','2026-10-02','2026-10-05','2026-10-06','2026-10-07','2026-10-08']
        bars={s:[{'t':d+'T04:00:00Z','c':100+i} for i,d in enumerate(dates)] for s in ['A','B']}
        del bars['B'][2]
        h=History(('A','B'),bars,'iex','all','2026-10-08T22:00Z')
        p=prepare_history(h,'2026-10-01T00:00Z','2026-10-08T23:00Z',asof='2026-10-08T22:00Z',min_observations=2)
        self.assertEqual(p.dropped_return_dates,('2026-10-05','2026-10-06'))
        self.assertEqual(len(p.returns),3)
        # Before today's close, today's bar must be excluded even if returned.
        q=prepare_history(h,'2026-10-01T00:00Z','2026-10-08T23:00Z',asof='2026-10-08T18:00Z',min_observations=2)
        self.assertEqual(q.latest_session,'2026-10-07')
        bars['A'].pop()
        with self.assertRaises(DataError): prepare_history(h,'2026-10-01T00:00Z','2026-10-08T23:00Z',asof='2026-10-08T22:00Z',min_observations=2)
    def test_stale_recent_price(self):
        payload={'trades':{'A':{'p':100,'t':'2026-10-08T15:00:00Z'}}}
        p=AlpacaData('test','test',session=Session([Response(payload)]))
        self.assertTrue(p.latest_prices(['A'],now='2026-10-08T18:00Z')['A']['stale'])
    def test_estimator_normalization_and_shrinkage(self):
        r=np.array([[.01,.02],[-.01,0],[0,-.02]])
        sample=estimate_covariance(r,annualization=1)
        assert_allclose(sample.covariance,np.cov(r,rowvar=False,ddof=1))
        fitted=estimate_covariance(r,'ledoit_wolf',annualization=1)
        empirical=np.cov(r,rowvar=False,ddof=0); mu=np.trace(empirical)/2
        assert_allclose(fitted.covariance,(1-fitted.shrinkage)*empirical+fitted.shrinkage*mu*np.eye(2))
        self.assertGreaterEqual(np.linalg.eigvalsh(fitted.covariance).min(),0)
        self.assertEqual(fitted.normalization,'T')
if __name__=='__main__': unittest.main()
