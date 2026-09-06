"""Profile desired speed and time gap with the other set-C parameters fixed.

This is deliberately a small, transparent alternative to a seven-parameter
EGO fit.  The grid uses one deterministic simulation seed per point; the
minimum can then be checked with independent seeds using evaluate_motivation.py.

Usage: python3 profile_motivation.py h0 [--workers N]
"""
import argparse
import json
import pathlib
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import driver_cq  # noqa: E402
import observables_cq as obs  # noqa: E402


STATIC = {
    "radius": 0.144,
    "strength_neighbor": 9.41,
    "range_neighbor": 0.09,
    "strength_geometry": 2.60,
    "range_geometry": 0.032,
}
V0_GRID = np.linspace(0.8, 1.8, 7)
T_GRID = np.linspace(0.1, 1.2, 7)
SIGMA = {"flow": 0.06, "density": 0.10, "speed": 0.10}


def evaluate(job):
    run_name, v0, time_gap, out_file = job
    params = dict(STATIC, desired_speed=float(v0), time_gap=float(time_gap))
    return driver_cq.one(run_name, 1, out_file, params)


def norm(records, expected):
    return float(np.sqrt(sum(
        ((record[k] - expected[record["run"]][k]) /
         (SIGMA[k] * expected[record["run"]][k])) ** 2
        for record in records for k in driver_cq.OBS
    )))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("motivation", choices=("h0", "h-"))
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()

    out_dir = pathlib.Path("results")
    out_dir.mkdir(exist_ok=True)
    runs = [name for name, run in obs.runs().items()
            if run["motivation"] == args.motivation]
    expected = json.load(open("exp_observables_cq.json"))
    jobs = []
    for i, v0 in enumerate(V0_GRID):
        for j, time_gap in enumerate(T_GRID):
            for run_name in runs:
                jobs.append((run_name, v0, time_gap,
                             str(out_dir / f"profile_{args.motivation}_{i}_{j}_{run_name}.sqlite")))

    with ProcessPoolExecutor(args.workers) as executor:
        records = list(executor.map(evaluate, jobs))

    grid = []
    for i, v0 in enumerate(V0_GRID):
        for j, time_gap in enumerate(T_GRID):
            block = [r for (run, _, _, file), r in zip(jobs, records)
                     if file.endswith(f"_{i}_{j}_{run}.sqlite")]
            grid.append({
                "desired_speed": float(v0),
                "time_gap": float(time_gap),
                "norm": norm(block, expected),
                "status_counts": {
                    status: sum(r["status"] == status for r in block)
                    for status in sorted({r["status"] for r in block})
                },
            })
    best = min(grid, key=lambda point: point["norm"])
    result = {
        "motivation": args.motivation,
        "fixed_parameters": STATIC,
        "seed": 1,
        "v0_grid": V0_GRID.tolist(),
        "time_gap_grid": T_GRID.tolist(),
        "best": best,
        "grid": grid,
    }
    output = out_dir / f"motivation_profile_{args.motivation.replace('-', 'minus')}.json"
    json.dump(result, open(output, "w"), indent=1)
    for _, _, _, filename in jobs:
        pathlib.Path(filename).unlink(missing_ok=True)
    print(f"wrote {output} (best norm {best['norm']:.3f})")


if __name__ == "__main__":
    main()
