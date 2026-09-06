#!/usr/bin/env python3
"""Dakota calibration driver: residuals against measured evacuation times
and door flow rates.

Usage:  python3 driver_calib.py params.in results.out
Reads experiments.dat (door_width  t_measured  flow_measured per line), runs
each experiment with JPS_N_SEEDS replicate seeds in parallel, and writes the
residuals sim - measured: all evacuation times first, then all flows.
"""
import os
import pathlib
import statistics
import sys
from concurrent.futures import ProcessPoolExecutor

from driver import N_SEEDS, read_params, run

EXPERIMENTS = "experiments.dat"


def load_experiments():
    rows = [line.split() for line in open(EXPERIMENTS) if line.strip()]
    return [(float(w), float(t), float(j)) for w, t, j in rows]


def main():
    params_file, results_file = sys.argv[1], sys.argv[2]
    p = read_params(params_file)
    v0 = float(p["desired_speed"])
    radius = float(p.get("radius", 0.2))
    out_dir = pathlib.Path(params_file).resolve().parent
    experiments = load_experiments()

    jobs = [
        (v0, w, seed, out_dir / f"exp{i}", radius)
        for i, (w, _, _) in enumerate(experiments)
        for seed in range(1, N_SEEDS + 1)
    ]
    for i in range(len(experiments)):
        (out_dir / f"exp{i}").mkdir(exist_ok=True)
    with ProcessPoolExecutor(max_workers=int(os.environ.get("JPS_WORKERS", "10"))) as ex:
        results = list(ex.map(run, *zip(*jobs)))

    def mean_of(i, k):
        return statistics.mean(r[k] for r in results[i * N_SEEDS:(i + 1) * N_SEEDS])

    with open(results_file, "w") as f:
        for i, (_, t_meas, _) in enumerate(experiments):
            f.write(f"{mean_of(i, 0) - t_meas:.4f} residual_t_{i + 1}\n")
        for i, (_, _, j_meas) in enumerate(experiments):
            f.write(f"{mean_of(i, 1) - j_meas:.4f} residual_flow_{i + 1}\n")


if __name__ == "__main__":
    main()
