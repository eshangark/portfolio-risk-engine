"""End-to-end validated API costs including Python/C++ crossing and covariance checks."""
import argparse
import contextlib
import io
import json
import os
import platform
import subprocess
import time
from pathlib import Path
import numpy as np
from portfolio_risk import _core, reference


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--output',type=Path); args=parser.parse_args()
    rng=np.random.default_rng(903); rows=[]
    for n in (2,10,50):
        a=rng.normal(size=(n,n)); cov=a@a.T/n/100; w=np.full(n,1/n)
        expected=reference.risk(w,cov)
        for name,fn in [('numpy_validated',lambda:reference.risk(w,cov)),
                        ('cpp_analytical_validated',lambda:_core.risk(w,cov,False)),
                        ('cpp_ad_validated',lambda:_core.risk(w,cov,True))]:
            result=fn(); volatility=result.volatility if name.startswith('numpy') else result['volatility']
            np.testing.assert_allclose(volatility,expected.volatility,rtol=1e-10)
            for _ in range(5): fn()
            samples=[]
            for _ in range(7):
                start=time.perf_counter_ns()
                for _ in range(30): fn()
                samples.append((time.perf_counter_ns()-start)/30/1000)
            rows.append({'assets':n,'implementation':name,'median_microseconds':float(np.median(samples)),
                         'p10_microseconds':float(np.percentile(samples,10)),
                         'p90_microseconds':float(np.percentile(samples,90))})
    config=io.StringIO()
    with contextlib.redirect_stdout(config): np.show_config()
    compiler=subprocess.run(['c++','--version'],capture_output=True,text=True,check=False)
    report={'scope':'Validated risk APIs including covariance eigensolver, allocations and binding overhead; not isolated kernels',
        'seed':903,'warmup_calls':5,'repeats':7,'calls_per_repeat':30,
        'platform':platform.platform(),'processor':platform.processor(),'python':platform.python_version(),
        'numpy':np.__version__,'engine':_core.__version__,'compiler':compiler.stdout.splitlines()[0] if compiler.stdout else 'unavailable',
        'build':'CMake Release; compiler default Release flags; no custom fast-math',
        'thread_environment':{k:os.getenv(k) for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')},
        'numpy_config':config.getvalue(),'results':rows}
    text=json.dumps(report,indent=2,allow_nan=False)+'\n'; print(text,end='')
    if args.output: args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(text)

if __name__=='__main__': main()
