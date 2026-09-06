"""Profile radius and neighbor range on h- with v0 and T fixed at the h0 valley.

The fixed desired speed and time gap are Dakota's selected h0 profile point.
One deterministic seed is used per grid point; confirm the selected point with
independent seeds using evaluate_motivation.py.

Usage: python3 profile_spacing.py [--workers N]
"""
import argparse
import json
import pathlib
import sys
from concurrent.futures import ProcessPoolExecutor
from itertools import product

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import driver_cq  # noqa: E402
import observables_cq as obs  # noqa: E402
from parameter_io import best_parameters  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parent
RADIUS_GRID = np.linspace(0.10, 0.20, 7)
RANGE_NEIGHBOR_GRID = np.linspace(0.02, 0.40, 7)
SIGMA = {"flow": 0.06, "density": 0.10, "speed": 0.10}


def fixed_parameters():
    calibrated = best_parameters(ROOT / "calib_h0_s9" / "dakota.out")
    profile = best_parameters(ROOT / "motivation_profile_h0" / "dakota.out")
    return {
        "desired_speed": profile["desired_speed"],
        "time_gap": profile["time_gap"],
        "strength_neighbor": calibrated["strength_neighbor"],
        "strength_geometry": calibrated["strength_geometry"],
        "range_geometry": calibrated["range_geometry"],
    }


def evaluate(job):
    run_name, radius, neighbor_range, out_file, fixed = job
    params = dict(fixed, radius=float(radius), range_neighbor=float(neighbor_range))
    return driver_cq.one(run_name, 1, out_file, params)


def norm(records, expected):
    return float(np.sqrt(sum(
        ((record[key] - expected[record["run"]][key]) /
         (SIGMA[key] * expected[record["run"]][key])) ** 2
        for record in records for key in driver_cq.OBS
    )))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()

    out_dir = pathlib.Path("results")
    out_dir.mkdir(exist_ok=True)
    runs = [name for name, run in obs.runs().items() if run["motivation"] == "h-"]
    expected = json.load(open("exp_observables_cq.json"))
    fixed = fixed_parameters()
    points = list(product(enumerate(RADIUS_GRID), enumerate(RANGE_NEIGHBOR_GRID)))
    jobs = [
        (run_name, radius, neighbor_range,
         str(out_dir / f"spacing_hminus_{i}_{j}_{run_name}.sqlite"), fixed)
        for (i, radius), (j, neighbor_range) in points for run_name in runs
    ]

    with ProcessPoolExecutor(args.workers) as executor:
        records = list(executor.map(evaluate, jobs))

    grid = []
    for (i, radius), (j, neighbor_range) in points:
        block = [record for (run, _, _, file, _), record in zip(jobs, records)
                 if file.endswith(f"_{i}_{j}_{run}.sqlite")]
        grid.append({
            "radius": float(radius),
            "range_neighbor": float(neighbor_range),
            "norm": norm(block, expected),
            "status_counts": {
                status: sum(record["status"] == status for record in block)
                for status in sorted({record["status"] for record in block})
            },
        })
    best = min(grid, key=lambda point: point["norm"])
    result = {
        "motivation": "h-",
        "fixed_parameters": fixed,
        "seed": 1,
        "radius_grid": RADIUS_GRID.tolist(),
        "range_neighbor_grid": RANGE_NEIGHBOR_GRID.tolist(),
        "best": best,
        "grid": grid,
    }
    output = out_dir / "motivation_profile_spacing_hminus.json"
    json.dump(result, open(output, "w"), indent=1)
    for _, _, _, filename, _ in jobs:
        pathlib.Path(filename).unlink(missing_ok=True)
    print(f"wrote {output} (best norm {best['norm']:.3f})")


if __name__ == "__main__":
    main()
