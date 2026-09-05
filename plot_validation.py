"""Figure 5: experiment with acceptance band (6 % flow, 10 % density, 10 % speed),
default model, and calibrated model (mean and full range over 3 seeds)."""
import json, pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = pathlib.Path(__file__).parent
W, CAL = [2.4, 3.0, 3.6, 4.4, 5.0], {2.4, 3.6, 5.0}
REL = {"flow": 0.06, "density": 0.10, "speed": 0.10}
exp = {float(k): v for k, v in json.load(open(HERE / "exp_observables.json")).items()}
base = {v["b"]: v["sim"] for v in json.load(open(HERE / "baseline/baseline.json")).values()}
val = json.load(open(HERE / "validation/validation.json"))["sim"]
labels = {"flow": "flow J [1/s]", "density": "density [1/m$^2$]", "speed": "speed [m/s]"}
fig, axes = plt.subplots(1, 3, figsize=(14, 4.4))
for ax, k in zip(axes, labels):
    e = np.array([exp[w][k] for w in W])
    ax.fill_between(W, e * (1 - REL[k]), e * (1 + REL[k]), color="0.85", label="acceptance band (6 % flow, 10 % density, speed)")
    ax.plot(W, e, "ko-", label="experiment")
    ax.plot(W, [base[w][k] for w in W], "s--", color="gray", label="CFSM defaults")
    m = np.array([np.mean(val[str(w)][k]) for w in W]); lo = np.array([np.min(val[str(w)][k]) for w in W]); hi = np.array([np.max(val[str(w)][k]) for w in W])
    ax.errorbar(W, m, yerr=[m - lo, hi - m], fmt="^-", color="C3", capsize=3, label="CFSM calibrated (mean, min–max of 3 seeds)")
    for w in W:
        if w not in CAL: ax.axvline(w, color="C3", ls=":", lw=0.8)
    ax.set_xlabel("bottleneck width b [m]"); ax.set_ylabel(labels[k]); ax.set_ylim(bottom=0)
axes[0].set_title("dotted: held-out widths", fontsize=10); axes[1].legend(fontsize=7.5, loc="upper right")
fig.tight_layout(); fig.savefig(HERE / "validation.png", dpi=150); print("fig5 ok")
