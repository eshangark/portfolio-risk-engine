"""Run from repository root: python -m examples.two_asset [--output FILE]."""
import argparse
import hashlib
import json
import platform
import subprocess
from pathlib import Path
import numpy as np
from portfolio_risk.reference import risk, dollar_gradient, weights_from_dollars, shrink_covariance


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    w = np.array([.6,.4])
    s = np.array([[.04,.006],[.006,.01]])  # Hypothetical annual covariance, not market data.
    out = risk(w,s)
    h = np.array([600.,400.])
    purchase = np.array([0.,100.])
    direction = np.array([-1.,1.])
    source = Path(__file__).resolve().parents[1] / "portfolio_risk/reference.py"
    try:
        revision = subprocess.check_output(["git","rev-parse","HEAD"],stderr=subprocess.DEVNULL,text=True).strip()
    except (OSError,subprocess.CalledProcessError):
        revision = "uncommitted; use source hashes"
    report = {
        "data_identity": "synthetic-two-asset-v1; annual covariance; USD",
        "git_revision": revision,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "example_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python": platform.python_version(), "numpy": np.__version__, "platform": platform.platform(),
        "weights": w.tolist(), "covariance": s.tolist(),
        "variance": out.variance, "volatility": out.volatility,
        "gradient": out.gradient.tolist(), "risk_contributions": out.contributions.tolist(),
        "risk_shares": (out.contributions/out.volatility).tolist(),
        "dollar_gradient": dollar_gradient(h,s).tolist(),
        "purchase_B_100": {"weights": weights_from_dollars(h+purchase).tolist(),
            "exact_change": risk(weights_from_dollars(h+purchase),s).volatility-out.volatility,
            "linear_change": float(dollar_gradient(h,s) @ purchase)},
        "transfers": [{"epsilon": e, "exact_change": risk(w+e*direction,s).volatility-out.volatility,
            "linear_change": float(e*(out.gradient @ direction))} for e in (.001,.01,.05)],
        "fixed_alpha_sensitivity": [{"alpha": a,"volatility": risk(w,shrink_covariance(s,a)).volatility}
                                     for a in (0,.25,.5,.75,1)],
    }
    rendered = json.dumps(report,indent=2,allow_nan=False)+"\n"
    print(rendered,end="")
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(rendered)


if __name__ == "__main__":
    main()
