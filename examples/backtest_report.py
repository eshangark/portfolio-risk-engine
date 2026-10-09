"""Seeded multi-regime stress simulation, explicitly not observed market data."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from portfolio_risk.backtest import contribution_backtest


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--output',type=Path); args=parser.parse_args()
    rng=np.random.default_rng(91026); blocks=[]
    for scale,correlation in ((.008,.2),(.025,.8),(.012,-.15),(.018,.5)):
        covariance=scale**2*((1-correlation)*np.eye(4)+correlation*np.ones((4,4)))
        blocks.append(rng.multivariate_normal(np.full(4,.0002),covariance,size=252))
    returns=pd.DataFrame(np.vstack(blocks),index=pd.bdate_range('2020-01-01',periods=1008),columns=list('ABCD'))
    report=contribution_backtest(returns)
    report['data_identity']='Synthetic four-regime Gaussian returns, seed 91026; not market evidence'
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('ledger','decisions')},allow_nan=False))


if __name__=='__main__': main()
