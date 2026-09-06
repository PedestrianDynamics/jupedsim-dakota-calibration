"""Figure 10: N(t) at the gate for three CrowdQueue runs, experiment vs simulation seeds,
to show the difference between active passage, slow discharge and a stall.
Usage: python3 plot_nt.py results/calib_h0_s9.json"""
import json, pathlib, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import observables_cq as o
d = json.load(open(sys.argv[1]))["runs"]
RUNS = ["090_c_12_h0", "110_c_12_h0", "030_c_56_h0"]
fig, axes = plt.subplots(1, 3, figsize=(14, 4))
for ax, rn in zip(axes, RUNS):
    r = o.runs()[rn]; e = o.compute(o.load_experiment(r["file"]), r["width"])
    ax.step(e["t"] - e["t"][e["n"] > 0][0], e["n"], "k-", lw=2, label="experiment")
    for s in d[rn]["seeds"]:
        t, n = np.array(s["nt"][0]), np.array(s["nt"][1])
        if len(t) == 0: continue
        t0 = t[n > 0][0] if (n > 0).any() else t[0]
        ax.step(t - t0, n, lw=1, label=f"seed: {s['status']}, gap {s['max_gap']:.0f} s")
    ax.set_title(f"run {rn[:3]}, {r['width']} m, {e['n_agents']} people", fontsize=10); ax.set_xlabel("time since first crossing [s]"); ax.legend(fontsize=7)
axes[0].set_ylabel("people passed the gate")
fig.suptitle("N(t) at the gate: experiment against three simulation seeds with the CrowdQueue calibration (set C)", fontsize=10)
fig.tight_layout(); fig.savefig("nt_curves.png", dpi=150); print("fig10 ok")
