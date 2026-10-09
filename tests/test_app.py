import unittest
from streamlit.testing.v1 import AppTest

class AppTests(unittest.TestCase):
    def test_synthetic_task(self):
        app=AppTest.from_file('app/streamlit_app.py',default_timeout=30).run()
        self.assertEqual(len(app.exception),0)
        self.assertEqual(app.metric[0].value,'13.74%')
        self.assertGreaterEqual(len(app.dataframe),2)
        app.slider[0].set_value(.4).run()
        self.assertEqual(len(app.exception),0)
        self.assertTrue(any('No feasible allocation' in e.value for e in app.error))
    def test_market_mode_requires_universe_confirmation(self):
        app=AppTest.from_file('app/streamlit_app.py',default_timeout=30).run()
        app.sidebar.radio[0].set_value('Alpaca market data').run()
        self.assertEqual(len(app.exception),0)
        self.assertTrue(any('Confirm the supported universe' in e.value for e in app.info))
if __name__=='__main__': unittest.main()
