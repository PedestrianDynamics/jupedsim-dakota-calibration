"""Evaluate one condition-specific parameter set with independent seeds.

Usage: python3 evaluate_motivation.py <label> <motivation> v0 radius time_gap
       strength_neighbor range_neighbor strength_geometry range_geometry
       [--seeds N]
"""
import json
import pathlib
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import driver_cq  # noqa: E402
import observables_cq as obs  # noqa: E402


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    n_seeds = int(sys.argv[sys.argv.index("--seeds") + 1]) if "--seeds" in sys.argv else 3
    label, motivation = args[:2]
    values = list(map(float, args[2:]))
    names = ["desired_speed", "radius", "time_gap", "strength_neighbor",
             "range_neighbor", "strength_geometry", "range_geometry"]
    params = dict(zip(names, values))
    runs = {n: r for n, r in obs.runs().items() if r["motivation"] == motivation}
    out = pathlib.Path("results")
    out.mkdir(exist_ok=True)
    jobs = [(rn, seed, str(out / f"{label}_{rn}_s{seed}.sqlite"), params)
            for rn in runs for seed in range(1, n_seeds + 1)]
    with ProcessPoolExecutor(int(sys.argv[sys.argv.index("--workers") + 1])
                             if "--workers" in sys.argv else 6) as ex:
        result = list(ex.map(driver_cq.one, *zip(*jobs)))

    table = {}
    for rn in runs:
        block = [r for (name, _, _, _), r in zip(jobs, result) if name == rn]
        table[rn] = {
            "exp": json.load(open("exp_observables_cq.json"))[rn],
            "sim": {k: float(np.mean([r[k] for r in block])) for k in driver_cq.OBS},
            "sim_std": {k: float(np.std([r[k] for r in block], ddof=1))
                        if n_seeds > 1 else 0.0 for k in driver_cq.OBS},
            "seeds": block,
        }
    json.dump({"label": label, "motivation": motivation, "params": params,
               "n_seeds": n_seeds, "runs": table},
              open(out / f"{label}.json", "w"), indent=1)
    for _, _, filename, _ in jobs:
        pathlib.Path(filename).unlink(missing_ok=True)
    print(f"wrote {out / f'{label}.json'} ({len(runs)} runs, {n_seeds} seeds)")
