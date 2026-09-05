"""Semicircle: time-averaged density maps, experiment vs simulations.
Usage: python3 plot_sc.py results/hermes.json [results/crowdqueue_h0.json results/joint.json]"""
import json, pathlib, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import shapely, h5py
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import scenario_sc
from evaluate_sc import GRID

files = sys.argv[1:]
labels = {"hermes": "Hermes parameters", "crowdqueue_h0": "CrowdQueue parameters", "joint": "joint calibration"}
panels = [("experiment", json.load(open(files[0]))["exp"])]
for f in files:
    d = json.load(open(f)); valid = [r for r in d["sim"] if r["dmap"] is not None]
    if valid:
        panels.append((f"{labels.get(pathlib.Path(f).stem, pathlib.Path(f).stem)}\nflow {np.mean([r['flow'] for r in valid]):.2f} /s",
                       {"dmap": np.mean([r["dmap"] for r in valid], 0).tolist(), "flow": np.mean([r["flow"] for r in valid])}))
panels[0] = (f"experiment\nflow {panels[0][1]['flow']:.2f} /s", panels[0][1])
geo = scenario_sc.geometry()
vmax = max(np.max(p["dmap"]) for _, p in panels)
fig, axes = plt.subplots(1, len(panels), figsize=(4.2 * len(panels), 4.6), sharey=True)
for ax, (title, p) in zip(np.atleast_1d(axes), panels):
    im = ax.pcolormesh(GRID[0], GRID[1], np.array(p["dmap"]).T, cmap="magma_r", vmin=0, vmax=vmax)
    for ring in geo.interiors:
        ax.fill(*ring.xy, color="0.5")
    ax.set_title(title, fontsize=9); ax.set_aspect("equal"); ax.set_xlabel("x [m]")
np.atleast_1d(axes)[0].set_ylabel("y [m]")
fig.colorbar(im, ax=axes, shrink=0.8, label="time-averaged density [1/m$^2$], 20–110 s")
fig.savefig("semicircle.png", dpi=150, bbox_inches="tight"); print("ok")
