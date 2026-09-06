#!/usr/bin/env python3
"""Dakota driver for CrowdQueue runs.

Usage:  python3 driver_cq.py params.in results.out
Env:    CQ_RUNS      comma list of run names (e.g. 090_c_12_h0,270_c_34_h0)
        JPS_N_SEEDS  replicates averaged per run (default 1)
        CQ_STATUS_FILE  JSON audit file name (default evaluation_status.json)
        CQ_RESIDUALS=1  write (sim - exp) / sigma per observable, sigma = 6 % flow,
                        10 % density, 10 % speed of the experiment value
Responses per run, in order: flow, density, speed.
"""
import json
import os
import pathlib
import statistics
import sys
from concurrent.futures import ProcessPoolExecutor

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import observables_cq as obs  # noqa: E402
import scenario_cq  # noqa: E402

PARAMS = ["desired_speed", "radius", "time_gap", "strength_neighbor",
          "range_neighbor", "strength_geometry", "range_geometry"]
OBS = ["flow", "density", "speed"]
REL_SIGMA = {"flow": 0.06, "density": 0.10, "speed": 0.10}


def read_params(path):
    out = {}
    for line in open(path):
        parts = line.split()
        if len(parts) == 2:
            out[parts[1]] = parts[0]
    return out


def one(run_name, seed, out_file, kwargs):
    """Simulate one run with one seed and return a complete record:
    observables, measurement window, expected (tracked) and injected population,
    completion status and, for failures, the exception category.
    Status: 'emptied'      every expected agent passed the gate within the 120 s cap,
            'not emptied'  not everyone passed, discharge continued to the end,
            'stalled'      not everyone passed and there was a >= 20 s interval without a crossing,
            'failed'       the simulation raised; see 'error_type' and 'error'."""
    run = obs.runs()[run_name]
    expected = len(obs.arrivals(run["file"]))  # every tracked participant
    rec = dict(run=run_name, seed=seed, expected=expected, injected=0, dropped=0,
               flow=0.0, density=0.0, speed=0.0, flow_active=0.0, flow_total=0.0, max_gap=0.0,
               passed=0, window=None, status="failed", error_type=None, error=None, nt=[[], []])
    try:
        rec["dropped"] = scenario_cq.run(run_name, seed, out_file, **kwargs)
        tr = obs.load_simulation(out_file)
        r = obs.compute(tr, run["width"])
        rec["injected"] = r["n_agents"]
        emptied = r["n_total"] >= expected and rec["dropped"] == 0
        rec.update({k: float(r[k]) for k in OBS}, flow_active=r["flow_active"], flow_total=r["flow_total"],
                   max_gap=r["max_gap"], passed=r["n_total"], window=list(r["window"]),
                   status="emptied" if emptied else ("stalled" if r["max_gap"] >= 20.0 else "not emptied"),
                   nt=[list(map(float, r["t"][::5])), list(map(int, r["n"][::5]))])
    except Exception as e:  # keep the category: a wall violation is a model failure, anything else is a pipeline error
        rec["error_type"] = type(e).__name__
        rec["error"] = str(e)[:120]
        print(f"run failed ({run_name}, seed={seed}): {type(e).__name__}: {e}", file=sys.stderr)
    return rec


def main():
    params_file, results_file = sys.argv[1], sys.argv[2]
    p = read_params(params_file)
    kwargs = {k: float(p[k]) for k in PARAMS if k in p}
    run_names = os.environ["CQ_RUNS"].split(",")
    n_seeds = int(os.environ.get("JPS_N_SEEDS", "1"))
    out_dir = pathlib.Path(params_file).resolve().parent
    jobs = [(rn, s, str(out_dir / f"{rn}_s{s}.sqlite"), kwargs) for rn in run_names for s in range(1, n_seeds + 1)]
    with ProcessPoolExecutor(int(os.environ.get("JPS_WORKERS", "10"))) as ex:
        results = list(ex.map(one, *zip(*jobs)))
    status_file = out_dir / os.environ.get("CQ_STATUS_FILE", "evaluation_status.json")
    with open(status_file, "w") as fh:
        json.dump({"parameters": kwargs, "runs": run_names,
                   "simulation_seeds": [s for _, s, _, _ in jobs],
                   "records": results}, fh, indent=1)
    for _, _, f, _ in jobs:
        pathlib.Path(f).unlink(missing_ok=True)
    exp = json.load(open(HERE / "exp_observables_cq.json")) if os.environ.get("CQ_RESIDUALS") else None
    with open(results_file, "w") as fh:
        for i, rn in enumerate(run_names):
            block = results[i * n_seeds:(i + 1) * n_seeds]
            for k in OBS:
                val = statistics.mean(r[k] for r in block)
                if exp:
                    val = (val - exp[rn][k]) / (REL_SIGMA[k] * exp[rn][k])
                fh.write(f"{val:.5f} {k}_{rn}\n")


if __name__ == "__main__":
    main()
