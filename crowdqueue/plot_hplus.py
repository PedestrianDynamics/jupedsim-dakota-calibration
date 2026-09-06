"""Figure 8: high-motivation run 020: observables vs time gap, three seeds per point (explicit sweep)."""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
d = json.load(open("results/hplus_sweep.json")); exp = json.load(open("exp_observables_cq.json"))["020_c_12_h+"]
REL = {"flow": 0.06, "density": 0.10, "speed": 0.10}
fig, axes = plt.subplots(1, 3, figsize=(13, 3.9))
for ax, (k, lab) in zip(axes, [("flow", "gate flow [1/s]"), ("density", "density in corridor [1/m$^2$]"), ("speed", "speed in corridor [m/s]")]):
    ax.axhspan(exp[k] * (1 - REL[k]), exp[k] * (1 + REL[k]), color="0.85", label="experiment ± assumed uncertainty")
    ax.axhline(exp[k], color="k")
    for r in d["results"]:
        if k == "flow":
            # emptied runs: active-passage flow (filled); incomplete runs: throughput over the run (open), a different estimator
            v = r["flow_active"] if r["status"] == "emptied" else r["flow_total"]
        else:
            v = r[k]
        ax.plot(r["time_gap"], v, "o", ms=4, color="C1", mfc="C1" if r["status"] == "emptied" else "none")
    T = d["T"]
    m = [np.mean([r["flow_active"] if k == "flow" else r[k] for r in d["results"] if r["time_gap"] == t and r["status"] == "emptied"] or [np.nan]) for t in T]
    ax.plot(T, m, "-", color="C1", lw=1, label="mean over emptied seeds" + (" (active-passage flow)" if k == "flow" else ""))
    ax.set_xlabel("time gap [s]"); ax.set_ylabel(lab); ax.set_ylim(bottom=0)
axes[0].legend(fontsize=7.5)
axes[0].text(0.02, 0.02, "open markers: run not emptied, throughput over the run", transform=axes[0].transAxes, fontsize=7)
fig.suptitle("High-motivation run 020 (1.2 m corridor, 11 people): sweep of the time gap, other parameters at CrowdQueue set C", fontsize=10)
fig.tight_layout(); fig.savefig("hplus_sweep.png", dpi=150); print("fig8 ok")
