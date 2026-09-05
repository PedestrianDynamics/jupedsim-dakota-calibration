"""Figure 8: the high-motivation run 020 (1.2 m, h+): observables vs time gap from the
1-D Dakota sweep (all other parameters at the CrowdQueue calibration), against the experiment."""
import json, pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
d = np.loadtxt("probe_hplus/probe_history.dat", skiprows=1, usecols=(2, 9, 10, 11))
exp = json.load(open("exp_observables_cq.json"))["020_c_12_h+"]
REL = {"flow": 0.06, "density": 0.10, "speed": 0.10}
o = d[np.argsort(d[:, 0])]
fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))
for ax, (i, k, lab) in zip(axes, [(1, "flow", "gate flow [1/s]"), (2, "density", "density [1/m$^2$]"), (3, "speed", "speed [m/s]")]):
    sim = exp[k] + o[:, i] * REL[k] * exp[k]  # residuals were normalised: sim = exp + r*sigma
    ax.axhspan(exp[k] * (1 - REL[k]), exp[k] * (1 + REL[k]), color="0.85", label="experiment ± sigma")
    ax.axhline(exp[k], color="k")
    ax.plot(o[:, 0], sim, "o-", ms=4, color="C1", label="simulation (3 seeds averaged)")
    ax.set_xlabel("time gap [s]"); ax.set_ylabel(lab); ax.set_ylim(bottom=0)
axes[0].legend(fontsize=8)
fig.suptitle("High-motivation run (1.2 m corridor, 11 people): no time gap reaches the measured flow without breaking density and speed", fontsize=10)
fig.tight_layout(); fig.savefig("hplus_sweep.png", dpi=150); print("fig8 ok")
