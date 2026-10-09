"""Reproducible synthetic exercise of the chronological research protocol."""
import argparse
import hashlib
import json
import platform
from pathlib import Path
import numpy as np
import pandas as pd
from portfolio_risk.research import chronological_study


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--output',type=Path); args=parser.parse_args()
    rng=np.random.default_rng(24109)
    loadings=np.array([[.012,.003],[.008,-.005],[.003,.009]])
    values=rng.normal(size=(504,2))@loadings.T+rng.normal(scale=.003,size=(504,3))
    returns=pd.DataFrame(values,index=pd.bdate_range('2024-01-01',periods=504),columns=['A','B','C'])
    report=chronological_study(returns)
    report.update({'data_identity':'synthetic-factor-returns-seed-24109; not market evidence',
        'data_sha256':hashlib.sha256(values.tobytes()).hexdigest(),'python':platform.python_version(),'numpy':np.__version__})
    text=json.dumps(report,indent=2,allow_nan=False)+'\n'
    if args.output: args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(text)
    print(json.dumps({'data_identity':report['data_identity'],'evaluations':len(report['results']),
        'mean_calibration_ratio':float(np.mean([r['calibration_ratio'] for r in report['results']])),
        'output':str(args.output)}))

if __name__=='__main__': main()
