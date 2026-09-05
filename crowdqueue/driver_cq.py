#!/usr/bin/env python3
"""Dakota driver for CrowdQueue runs.

Usage:  python3 driver_cq.py params.in results.out
Env:    CQ_RUNS      comma list of run names (e.g. 090_c_12_h0,270_c_34_h0)
        JPS_N_SEEDS  replicates averaged per run (default 1)
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
    """Returns the three observables plus a status:
    'ok'      every agent passed the gate within the 120 s cap,
    'clogged' the run did not empty within the cap (flow = passed / run time),
    'failed'  JuPedSim aborted (an agent was pushed through a wall); observables set to 0."""
    width = obs.runs()[run_name]["width"]
    try:
        scenario_cq.run(run_name, seed, out_file, **kwargs)
        tr = obs.load_simulation(out_file)
        r = obs.compute(tr, width)
        n_agents = int(tr.data["id"].nunique())
        status = "ok" if r["n_total"] >= n_agents else "clogged"
        return {**{k: float(r[k]) for k in OBS}, "status": status, "passed": r["n_total"], "agents": n_agents}
    except Exception as e:
        print(f"run failed ({run_name}, seed={seed}): {e}", file=sys.stderr)
        return dict(flow=0.0, density=0.0, speed=0.0, status="failed", passed=0, agents=0)


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
