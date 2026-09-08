"""Two-panel explainer for the Morris screening: a sketch of one-at-a-time
trajectories for two parameters, and the real mu* / sigma scatter for the flow
at 3.6 m from the twenty-trajectory run (morris_r20)."""
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = pathlib.Path(__file__).parent
SRC = sys.argv[1] if len(sys.argv) > 1 else "morris_r20"
names = ["desired_speed", "radius", "time_gap", "strength_neighbor", "range_neighbor", "strength_geometry", "range_geometry"]
labels = ["desired speed", "radius", "time gap", "neighbor strength", "neighbor range", "wall strength", "wall range"]
RESP = 3  # flow_3.6
d = np.loadtxt(HERE / SRC / "morris_samples.dat", skiprows=1, usecols=range(2, 18))
X, Y = d[:, :7], d[:, 7:]
rng = np.ptp(X, 0)
acc = [[] for _ in names]
for a in range(len(X) - 1):
    b = a + 1
    if b % 8 == 0 or (Y[a, [0, 3, 6]] == 0).any() or (Y[b, [0, 3, 6]] == 0).any():
        continue  # trajectory boundary, or a step whose end failed
    dx = X[b] - X[a]
    i = int(np.argmax(np.abs(dx)))
    acc[i].append((Y[b, RESP] - Y[a, RESP]) / (dx[i] / rng[i]))
mu_star = np.array([np.mean(np.abs(e)) for e in acc])
sigma = np.array([np.std(e) for e in acc])

fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(11, 4.2), gridspec_kw=dict(width_ratios=[1, 1.15]))

# left: sketch, two parameters, four grid levels (partitions = 3), three paths
r_lv = np.linspace(0.12, 0.25, 4)
t_lv = np.linspace(0.10, 1.20, 4)
for r in r_lv:
    ax0.axvline(r, color="0.85", lw=0.8, zorder=0)
for t in t_lv:
    ax0.axhline(t, color="0.85", lw=0.8, zorder=0)
paths = [  # (start radius level, start time-gap level, first move, radius step, time-gap step, colour, aborted)
    (0, 3, "t", +2, -2, "C0", False),
    (3, 0, "t", -2, +2, "C1", True),
]
for ir, it, first, dr, dt, c, aborted in paths:
    p0 = np.array([r_lv[ir], t_lv[it]])
    if first == "t":
        p1 = np.array([r_lv[ir], t_lv[it + dt]]); p2 = np.array([r_lv[ir + dr], t_lv[it + dt]])
    else:
        p1 = np.array([r_lv[ir + dr], t_lv[it]]); p2 = np.array([r_lv[ir + dr], t_lv[it + dt]])
    for a, b in ((p0, p1), (p1, p2)):
        ax0.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="-|>", color=c, lw=2, shrinkA=5, shrinkB=5))
    ax0.plot(*p0, "o", color=c, ms=8, mec="k", zorder=3)
    ax0.plot(*p1, "o", color=c, ms=8, mec="k", zorder=3)
    if aborted:
        ax0.plot(*p2, "x", color="k", ms=11, mew=2.5, zorder=4)
        ax0.annotate("second step of path 2:\nrun aborted, step discarded", p2, xytext=(0, -10), textcoords="offset points", ha="center", va="top", fontsize=8.5)
    else:
        ax0.plot(*p2, "o", color=c, ms=8, mec="k", zorder=3)
ax0.annotate("path 1: random start", (r_lv[0], t_lv[3]), xytext=(0, 8), textcoords="offset points", fontsize=8.5, ha="center", va="bottom", color="C0")
ax0.annotate("path 2: another\nrandom start", (r_lv[3], t_lv[0]), xytext=(-10, 0), textcoords="offset points", fontsize=8.5, ha="right", va="center", color="C1")
ax0.annotate("only the time gap changes:\n$\\Delta$flow / $\\Delta$time gap\n= one elementary effect", (r_lv[0], t_lv[3] - 0.2), xytext=(10, 0),
             textcoords="offset points", fontsize=8.5, va="center", color="C0")
ax0.annotate("only the radius changes", ((r_lv[0] + r_lv[2]) / 2, t_lv[1]), xytext=(0, -14), textcoords="offset points",
             fontsize=8.5, ha="center", color="C0")
ax0.annotate("one path = one step\nper parameter", (r_lv[2], t_lv[1]), xytext=(8, 0), textcoords="offset points", fontsize=8.5, va="center", color="C0")
ax0.set_xlim(0.105, 0.265); ax0.set_ylim(-0.02, 1.32)
ax0.set_xticks(r_lv, [f"{v:.2f}" for v in r_lv]); ax0.set_yticks(t_lv, [f"{v:.2f}" for v in t_lv])
ax0.set_xlabel("radius [m]"); ax0.set_ylabel("time gap [s]")
ax0.set_title("Sketch: two paths through a two-parameter box", fontsize=10)

# right: real result
ax1.scatter(mu_star, sigma, s=55, color="C1", ec="k", zorder=3)
for x, y, lab in zip(mu_star, sigma, labels):
    off = (-8, -12) if lab == "neighbor range" else (6, 4)
    ax1.annotate(lab, (x, y), xytext=off, textcoords="offset points", fontsize=9, ha="right" if lab == "neighbor range" else "left")
lim = max(mu_star.max(), sigma.max()) * 1.15
ax1.plot([0, lim], [0, lim], color="0.75", lw=0.8, ls="--")
ax1.set_xlim(0, lim); ax1.set_ylim(0, lim)
ax1.text(0.03, 0.03, "negligible", transform=ax1.transAxes, fontsize=9, color="0.4")
ax1.text(0.97, 0.03, "influential, uniform effect", transform=ax1.transAxes, fontsize=9, color="0.4", ha="right")
ax1.text(0.97, 0.94, "influential, effect depends\non the other parameters", transform=ax1.transAxes, fontsize=9, color="0.4", ha="right", va="top")
ax1.set_xlabel("mean change of the flow at 3.6 m per step, over the twenty paths  [1/s]")
ax1.set_ylabel("standard deviation of that change  [1/s]")
ax1.set_title("Result: twenty real paths, seven parameters", fontsize=10)
fig.tight_layout()
fig.savefig(HERE / "morris_sketch.png", dpi=150)
print("ok", dict(zip(names, np.round(mu_star, 2))), dict(zip(names, np.round(sigma, 2))))
