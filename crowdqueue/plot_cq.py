"""Figure 6: CrowdQueue, experiment vs simulation per run, individual seeds.
Marker: filled = run emptied within 120 s; open = clogged (not everyone passed,
flow = passed / run time); x = JuPedSim aborted (agent pushed through a wall).
Usage: python3 plot_cq.py results/transfer_hermes_B.json results/calib_h0_s9.json results/joint.json"""
import json, pathlib, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

files = sys.argv[1:]
labels = {"transfer_hermes": "Hermes set A (transfer, no fit)", "transfer_hermes_B": "Hermes set B (transfer, no fit)", "calib_h0_s9": "calibrated on CrowdQueue h0 (set C)", "calib_h0": "CrowdQueue set D", "joint": "joint calibration"}
CAL = {"090_c_12_h0", "110_c_12_h0", "170_q_12_h0", "190_q_34_h0", "270_c_34_h0", "030_c_56_h0", "150_q_56_h0"}
obs = [("flow", "gate flow [1/s]"), ("density", "density in corridor [1/m$^2$]"), ("speed", "speed in corridor [m/s]")]
data = [json.load(open(f)) for f in files]
fig, axes = plt.subplots(2, 3, figsize=(15, 8.5))
for row, mot in enumerate(["h0", "h-"]):
    runs = {n: r for n, r in data[0]["runs"].items() if r["exp"]["motivation"] == mot}
    names = sorted(runs, key=lambda n: (runs[n]["exp"]["width"], n))
    x = np.arange(len(names))
    for col, (k, lab) in enumerate(obs):
        ax = axes[row, col]
        ax.bar(x, [runs[n]["exp"][k] for n in names], color="0.85", label="experiment")
        for j, d in enumerate(data):
            off = 0.22 * (j - (len(data) - 1) / 2)
            for i, n in enumerate(names):
                for s in d["runs"][n]["seeds"]:
                    st = s["status"]
                    mk = {"emptied": "o", "not emptied": "o", "stalled": "s", "failed": "x"}[st]
                    ax.plot(i + off, s[k], marker=mk, ms=5, mew=1.2, color=f"C{j}",
                            mfc=f"C{j}" if st == "emptied" else "none", ls="none")
        ax.set_xticks(x, [f"{runs[n]['exp']['width']:.1f} m\n{n[:3]}{'*' if n in CAL else ''}" for n in names], fontsize=6.5)
        ax.set_ylabel(lab); ax.set_title(f"motivation {mot}" + ("  (* = used in calibration)" if mot == "h0" else ""), fontsize=10); ax.set_ylim(bottom=0)
handles = [plt.Rectangle((0, 0), 1, 1, color="0.85", label="experiment")]
handles += [Line2D([], [], marker="o", color=f"C{j}", ls="none", label=labels[pathlib.Path(f).stem]) for j, f in enumerate(files)]
handles += [Line2D([], [], marker="o", color="k", mfc="k", ls="none", label="filled circle: emptied within 120 s"),
            Line2D([], [], marker="o", color="k", mfc="none", ls="none", label="open circle: not emptied, discharge continuing"),
            Line2D([], [], marker="s", color="k", mfc="none", ls="none", label="open square: stalled (≥ 20 s without a crossing)"),
            Line2D([], [], marker="x", color="k", ls="none", label="x: aborted, agent pushed through a wall")]
fig.legend(handles=handles, loc="lower center", ncol=4, fontsize=8, frameon=False, bbox_to_anchor=(0.5, -0.01))
fig.suptitle("CrowdQueue 0.5 m gate: experiment (bars) vs Collision Free Speed model, one marker per seed (3 seeds)", fontsize=11)
fig.tight_layout(rect=(0, 0.08, 1, 1)); fig.savefig("crowdqueue.png", dpi=150); print("fig6 ok")
