"""Deterministic C++ evidence report; run after installing the compiled package."""
import argparse
import hashlib
import json
import platform
from pathlib import Path
import numpy as np
from portfolio_risk import _core
from portfolio_risk.reference import risk, dollar_gradient

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--output',type=Path); args=parser.parse_args()
    w=np.array([.6,.4]); s=np.array([[.04,.006],[.006,.01]]); h=np.array([600.,400.])
    reference=risk(w,s); cpp=_core.risk(w,s,True); allocation=_core.allocate(h,200,s,[.6,.6])
    root=Path(__file__).resolve().parents[1]
    report={'data_identity':'synthetic-two-asset-v1; annual covariance; USD','python':platform.python_version(),
        'numpy':np.__version__,'engine':_core.__version__,'platform':platform.platform(),
        'source_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'cpp').rglob('*')) if p.is_file()},
        'cpp_autodiff':cpp,'reference_volatility':reference.volatility,
        'max_gradient_error':float(np.max(np.abs(cpp['gradient']-reference.gradient))),
        'max_dollar_gradient_error':float(np.max(np.abs(_core.dollar_gradient(h,s)-dollar_gradient(h,s)))),
        'allocation':allocation}
    text=json.dumps(report,indent=2,default=lambda x:x.tolist(),allow_nan=False)+'\n'
    print(text,end='')
    if args.output: args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(text)
if __name__=='__main__': main()
