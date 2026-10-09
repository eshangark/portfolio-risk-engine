"""Read-only Alpaca connection and numerical study. Credentials never appear in output."""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
from portfolio_risk.data import AlpacaData,DataError,prepare_history,completed_history_end
from portfolio_risk.estimation import estimate_covariance
from portfolio_risk.research import chronological_study


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--symbols',nargs='+',default=['SPY','BND'])
    parser.add_argument('--feed',choices=['iex','sip'],default='iex')
    parser.add_argument('--study',action='store_true')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    try:
        from portfolio_risk import _core
        provider=AlpacaData(os.getenv('ALPACA_API_KEY'),os.getenv('ALPACA_API_SECRET'),args.feed)
        now=pd.Timestamp(datetime.now(timezone.utc)); end=completed_history_end(now)
        start=(end-pd.Timedelta(days=1100 if args.study else 550)).normalize()
        history=provider.history(args.symbols,start,end)
        prepared=prepare_history(history,start,end,asof=now,min_observations=273 if args.study else 63)
        latest=provider.latest_prices(history.symbols,now)
        estimate=estimate_covariance(prepared.returns.iloc[-252:],'ledoit_wolf')
        weights=np.full(len(history.symbols),1/len(history.symbols))
        risk=_core.risk(weights,estimate.covariance,True)
        # Retain metadata and aggregate research output, not provider bar payloads.
        report={'symbols':history.symbols,'feed':args.feed,'dataset_sha256':prepared.identity,
            'metadata':prepared.metadata,'latest_session':prepared.latest_session,'rows':len(prepared.returns),
            'latest_price_checks':{s:{k:v for k,v in row.items() if k!='price'} for s,row in latest.items()},
            'hypothetical_equal_weight_volatility':risk['volatility'],'shrinkage':estimate.shrinkage,
            'live_connection_verified':True,'corporate_action_economics_verified':False}
        if args.study: report['study']=chronological_study(prepared.returns)
        text=json.dumps(report,indent=2,allow_nan=False)+'\n'
        if args.output:
            # Keep private results under an ignored work/ directory by default.
            if 'work' not in args.output.parts: raise DataError('Write live reports under an ignored work/ directory.')
            args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(text)
        print(text,end='')
    except (DataError,ValueError) as exc:
        print(f'Live validation stopped: {exc}',file=sys.stderr); return 1
    return 0

if __name__=='__main__': raise SystemExit(main())
