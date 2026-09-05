"""Figure 7: time-averaged density maps (20–110 s), experiment vs simulations.
Simulation seeds are shown individually so that flowing and clogged runs stay distinct.
Usage: python3 plot_sc.py results/hermes.json results/joint.json"""
import json, pathlib, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import scenario_sc
from evaluate_sc import GRID

labels = {"hermes": "Hermes parameters", "joint": "joint calibration"}
panels = []
for f in sys.argv[1:]:
    d = json.load(open(f))
    if not panels:
        panels.append((f"experiment\nflow {d['exp']['flow']:.2f} /s, {d['exp']['crossed']} passed", d["exp"]["dmap"]))
    for i, r in enumerate(d["sim"]):
        if r["dmap"] is not None:
            panels.append((f"{labels.get(pathlib.Path(f).stem, pathlib.Path(f).stem)}, seed {i+1}\nflow {r['flow']:.2f} /s, {r['crossed']} passed", r["dmap"]))
geo = scenario_sc.geometry()
vmax = max(np.max(p) for _, p in panels)
n = len(panels); cols = 4; rows = int(np.ceil(n / cols))
fig, axes = plt.subplots(rows, cols, figsize=(4.0 * cols, 3.6 * rows), sharex=True, sharey=True)
axes = np.array(axes).ravel()
for ax, (title, dm) in zip(axes, panels):
    im = ax.pcolormesh(GRID[0], GRID[1], np.array(dm).T, cmap="magma_r", vmin=0, vmax=vmax)
    for ring in geo.interiors:
        ax.fill(*ring.xy, color="0.5")
    ax.set_title(title, fontsize=8.5); ax.set_aspect("equal")
for ax in axes[n:]: ax.axis("off")
for ax in axes[:n]: ax.set_xlabel("x [m]")
axes[0].set_ylabel("y [m]")
fig.colorbar(im, ax=axes.tolist(), shrink=0.7, label="time-averaged density [1/m$^2$]")
fig.savefig("semicircle.png", dpi=150, bbox_inches="tight"); print("fig7 ok")
