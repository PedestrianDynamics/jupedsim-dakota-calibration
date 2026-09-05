#!/usr/bin/env python3
"""Dakota driver for the Hermes bottleneck scenario.

Usage:  python3 driver.py params.in results.out
Env:    HERMES_WIDTHS   comma list of gap widths [m]      (default 2.4,3.6,5.0)
        JPS_N_SEEDS     replicates averaged per width     (default 1)
        HERMES_RESIDUALS=1  write sim - experiment instead of raw values
        JPS_WORKERS     parallel simulations inside one evaluation (default 9)
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

PARAMS = ["desired_speed", "radius", "time_gap", "strength_neighbor",
          "range_neighbor", "strength_geometry", "range_geometry"]
OBS = ["flow", "density", "speed"]


def read_params(path):
    out = {}
    for line in open(path):
        parts = line.split()
        if len(parts) == 2:
            out[parts[1]] = parts[0]
    return out


def one(width, seed, out_file, kwargs):
    try:
        scenario.run(width, seed, out_file, **kwargs)
        r = obs.compute(obs.load_simulation(out_file), width)
        if r["n_total"] < 20:
            return dict(flow=0.0, density=0.0, speed=0.0)
        return {k: float(r[k]) for k in OBS}
    except Exception as e:  # unphysical parameter combination: report as zero flow
        print(f"run failed (b={width}, seed={seed}): {e}", file=sys.stderr)
        return dict(flow=0.0, density=0.0, speed=0.0)


def main():
    params_file, results_file = sys.argv[1], sys.argv[2]
    p = read_params(params_file)
    kwargs = {k: float(p[k]) for k in PARAMS if k in p}
    widths = [float(w) for w in os.environ.get("HERMES_WIDTHS", "2.4,3.6,5.0").split(",")]
    n_seeds = int(os.environ.get("JPS_N_SEEDS", "1"))
    out_dir = pathlib.Path(params_file).resolve().parent
    jobs = [(w, s, str(out_dir / f"b{w}_s{s}.sqlite"), kwargs) for w in widths for s in range(1, n_seeds + 1)]
    with ProcessPoolExecutor(int(os.environ.get("JPS_WORKERS", "9"))) as ex:
        results = list(ex.map(one, *zip(*jobs)))
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
                fh.write(f"{val:.5f} {k}_{w:.1f}\n")


if __name__ == "__main__":
    main()
