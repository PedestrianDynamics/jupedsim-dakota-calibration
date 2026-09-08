#!/usr/bin/env python3
"""Dakota driver for the Hermes bottleneck scenario.

Usage:  python3 driver.py params.in results.out
Env:    HERMES_WIDTHS   comma list of gap widths [m]      (default 2.4,3.6,5.0)
        JPS_N_SEEDS     replicates averaged per width     (default 1)
        HERMES_RESIDUALS=1  write sim - experiment instead of raw values
        HERMES_NORMALIZE=1  divide residuals by sigma = 6 % / 10 % / 10 % of the experiment value
        JPS_WORKERS     parallel simulations inside one evaluation (default 9)
        HERMES_STATUS_FILE  JSON audit file name (default evaluation_status.json)
Responses per width, in order: flow [1/s], density [1/m2], speed [m/s].
"""
import json
import os
import pathlib
import statistics
import sys
from concurrent.futures import ProcessPoolExecutor

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import observables as obs  # noqa: E402
import scenario  # noqa: E402
import space_state  # noqa: E402  (found through scenario's path insert)

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


def one(width, seed, out_file, kwargs):
    audit = dict(width=float(width), seed=int(seed), status="failed", n_crossed=0,
                 elapsed_time=None, error_type=None, error=None)
    try:
        elapsed = scenario.run(width, seed, out_file, **kwargs)
        r = obs.compute(obs.load_simulation(out_file), width)
        audit.update(status="completed" if r["n_total"] >= scenario.N_AGENTS else "incomplete",
                     n_crossed=int(r["n_total"]), elapsed_time=float(elapsed))
        values = {k: float(r[k]) for k in OBS}
        if r["n_total"] < 20:
            values = dict.fromkeys(OBS, 0.0)
        return {**values, "_audit": audit}
    except Exception as e:  # preserve Dakota's finite fallback and audit the failure
        audit.update(error_type=type(e).__name__, error=str(e)[:200])
        print(f"run failed (b={width}, seed={seed}): {e}", file=sys.stderr)
        return {**dict.fromkeys(OBS, 0.0), "_audit": audit}


def main():
    params_file, results_file = sys.argv[1], sys.argv[2]
    p = read_params(params_file)
    kwargs = {k: float(p[k]) for k in PARAMS if k in p}
    if space_state.from_params(p):  # space-awareness rule, only when all four parameters are present
        kwargs["state_rule"] = space_state.from_params(p)
    widths = [float(w) for w in os.environ.get("HERMES_WIDTHS", "2.4,3.6,5.0").split(",")]
    n_seeds = int(os.environ.get("JPS_N_SEEDS", "1"))
    out_dir = pathlib.Path(params_file).resolve().parent
    jobs = [(w, s, str(out_dir / f"b{w}_s{s}.sqlite"), kwargs) for w in widths for s in range(1, n_seeds + 1)]
    with ProcessPoolExecutor(int(os.environ.get("JPS_WORKERS", "9"))) as ex:
        results = list(ex.map(one, *zip(*jobs)))
    status_file = out_dir / os.environ.get("HERMES_STATUS_FILE", "evaluation_status.json")
    with open(status_file, "w") as fh:
        json.dump({"parameters": kwargs, "widths": widths,
                   "simulation_seeds": [s for _, s, _, _ in jobs],
                   "records": [r["_audit"] for r in results]}, fh, indent=1)
    for _, _, f, _ in jobs:
        pathlib.Path(f).unlink(missing_ok=True)

    exp = json.load(open(HERE / "exp_observables.json")) if os.environ.get("HERMES_RESIDUALS") else None
    with open(results_file, "w") as fh:
        for i, w in enumerate(widths):
            block = results[i * n_seeds:(i + 1) * n_seeds]
            for k in OBS:
                val = statistics.mean(r[k] for r in block)
                if exp:
                    val -= exp[f"{w:.1f}"][k]
                    if os.environ.get("HERMES_NORMALIZE"):
                        val /= REL_SIGMA[k] * exp[f"{w:.1f}"][k]
                fh.write(f"{val:.5f} {k}_{w:.1f}\n")


if __name__ == "__main__":
    main()
