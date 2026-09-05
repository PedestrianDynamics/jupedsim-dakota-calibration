"""Simulate every usable CrowdQueue run with one parameter set (N seeds) and
tabulate against the experiment.  Usage:
  python3 evaluate_cq.py <label> v0 radius time_gap strength_n range_n [strength_g range_g] [--seeds N]
Writes results/<label>.json and prints the table."""
import json, pathlib, sys
from concurrent.futures import ProcessPoolExecutor
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import driver_cq, observables_cq as obs

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    n_seeds = int(sys.argv[sys.argv.index("--seeds") + 1]) if "--seeds" in sys.argv else 3
    label, vals = args[0], list(map(float, args[1:]))
    names = ["desired_speed", "radius", "time_gap", "strength_neighbor", "range_neighbor", "strength_geometry", "range_geometry"]
    kw = dict(zip(names, vals))
    runs = obs.runs(); exp = json.load(open("exp_observables_cq.json"))
    out = pathlib.Path("results"); out.mkdir(exist_ok=True)
    jobs = [(rn, s, str(out / f"{rn}_s{s}.sqlite"), kw) for rn in runs for s in range(1, n_seeds + 1)]
    with ProcessPoolExecutor(10) as ex:
        res = list(ex.map(driver_cq.one, *zip(*jobs)))
    table = {}
    print(f"{'run':14s} w   mot |  J_exp  J_sim |  rho_exp rho_sim |  v_exp  v_sim")
    for rn in runs:
        block = [r for (n, _, _, _), r in zip(jobs, res) if n == rn]
        sim = {k: float(np.mean([b[k] for b in block])) for k in ("flow", "density", "speed")}
        sd = {k: float(np.std([b[k] for b in block], ddof=1)) if n_seeds > 1 else 0.0 for k in sim}
        table[rn] = {"exp": exp[rn], "sim": sim, "sim_std": sd, "seeds": block}
        e = exp[rn]
        print(f"{rn:14s} {e['width']:.1f} {e['motivation']:3s} | {e['flow']:6.2f} {sim['flow']:6.2f} | {e['density']:7.2f} {sim['density']:7.2f} | {e['speed']:6.2f} {sim['speed']:6.2f}")
    json.dump({"params": kw, "runs": table}, open(out / f"{label}.json", "w"), indent=1)
    for f in out.glob("*.sqlite"): f.unlink()
