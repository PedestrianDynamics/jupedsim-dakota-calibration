"""CrowdQueue: experiment vs simulation per run, grouped by motivation.
Usage: python3 plot_cq.py results/transfer_hermes.json results/calib_h0.json [results/probe.json]"""
import json, pathlib, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

files = sys.argv[1:]
labels = {"transfer_hermes": "Hermes parameters (transfer)", "calib_h0": "calibrated on h0", "probe_hminus": "h0 params, time gap refit on h-"}
obs = [("flow", "gate flow [1/s]"), ("density", "density in corridor [1/m$^2$]"), ("speed", "speed in corridor [m/s]")]
fig, axes = plt.subplots(2, 3, figsize=(15, 8), sharex="col")
for row, mot in enumerate(["h0", "h-"]):
    for col, (k, lab) in enumerate(obs):
        ax = axes[row, col]
        for j, f in enumerate(files):
            d = json.load(open(f)); runs = {n: r for n, r in d["runs"].items() if r["exp"]["motivation"] == mot}
            names = sorted(runs, key=lambda n: (runs[n]["exp"]["width"], n))
            x = np.arange(len(names))
            if j == 0:
                ax.bar(x, [runs[n]["exp"][k] for n in names], color="0.8", label="experiment")
            ax.errorbar(x + 0.1 * (j - (len(files) - 1) / 2), [runs[n]["sim"][k] for n in names], yerr=[runs[n]["sim_std"][k] for n in names],
                        fmt="o", ms=5, capsize=2, label=labels.get(pathlib.Path(f).stem, pathlib.Path(f).stem))
            ax.set_xticks(x, [f"{runs[n]['exp']['width']:.1f} m\n{n[:3]}" for n in names], fontsize=7)
        ax.set_ylabel(lab); ax.set_title(f"motivation {mot}"); ax.set_ylim(bottom=0)
axes[0, 0].legend(fontsize=8)
fig.suptitle("CrowdQueue 0.5 m gate: experiment (bars) vs Collision Free Speed model (points, 3 seeds)")
fig.tight_layout(); fig.savefig("crowdqueue.png", dpi=150); print("ok")
