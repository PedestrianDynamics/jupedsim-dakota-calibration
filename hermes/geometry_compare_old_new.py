"""Old vs new archive polygons for the Hermes 2009 bottleneck runs: occupancy of head
positions with the archive boards (grey) and the nominal b_Exit edges (red dashed)."""
import pathlib
import sys
import h5py
import matplotlib
import numpy as np
import shapely
matplotlib.use("Agg")
import matplotlib.pyplot as plt
# usage: python3 geometry_compare_old_new.py <dir with the 2026-09-06 files> <dir with the 2026-09-08 files>
OLD, NEW = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
SP = pathlib.Path(__file__).resolve().parent.parent / "figures"
RUNS = [("ao-240-400", 2.4), ("ao-300-400", 3.0), ("ao-360-400", 3.6), ("ao-440-400", 4.4), ("ao-500-400", 5.0)]
GAP_CENTER, BAND = 0.9, 0.5

def gap(wkt):
    poly = shapely.from_wkt(wkt); xs = sorted(x for h in poly.interiors for x in (np.asarray(h.coords)[:, 0].min(), np.asarray(h.coords)[:, 0].max()))
    return poly, xs[1], xs[2]

fig, axes = plt.subplots(2, 5, figsize=(22, 9.5), sharey=True, gridspec_kw=dict(width_ratios=[4.3, 4.9, 5.6, 6.4, 6.9]))
for row, (label, src) in enumerate((("archive files downloaded 2026-09-06", OLD), ("archive files downloaded 2026-09-08", NEW))):
    for i, (run, b) in enumerate(RUNS):
        h = h5py.File(src / f"{run}.h5"); d = h["trajectory"][:]; x, y = d["x"], d["y"]
        poly, wl, wr = gap(h.attrs["wkt_geometry"]); nl, nr = GAP_CENTER - b / 2, GAP_CENTER + b / 2
        ax = axes[row, i]
        m = (y > -1.5) & (y < 2.5) & (x > nl - 1) & (x < nr + 1)
        ax.hist2d(x[m], y[m], bins=[np.arange(nl - 1, nr + 1.001, 0.04), np.arange(-1.5, 2.501, 0.04)], cmap="Greys", cmin=1)
        for hole in poly.interiors:
            hx, hy = np.asarray(hole.coords).T; ax.fill(hx, hy, color="k", alpha=0.25, lw=0); ax.plot(hx, hy, "k-", lw=1)
        for n_ in (nl, nr):
            ax.plot([n_, n_], [-BAND, BAND], "r--", lw=2)
        ax.annotate(f"x1 = {wl:.2f}", (wl, -BAND), xytext=(-4, -12), textcoords="offset points", ha="right", fontsize=9)
        ax.annotate(f"x2 = {wr:.2f}", (wr, -BAND), xytext=(4, -12), textcoords="offset points", ha="left", fontsize=9)
        flag = "" if abs((wr - wl) - b) < 1e-6 else "   (mismatch)"
        ax.set_title(f"{run}: b_Exit = {b} m\nwkt_geometry gap = {wr - wl:.2f} m{flag}", fontsize=10, color="k" if not flag else "C3")
        ax.set_aspect("equal"); ax.set_xlim(nl - 1, nr + 1)
        if row == 1: ax.set_xlabel("x [m]")
    axes[row, 0].set_ylabel(f"{label}\n\ny [m]", fontsize=11)
axes[0, 0].plot([], [], "k-", label="boards from wkt_geometry"); axes[0, 0].plot([], [], "r--", label="nominal b_Exit edges, centred at x = 0.9")
axes[0, 0].legend(loc="lower left", fontsize=8)
fig.suptitle("Hermes 2009 bottleneck (doi:10.34735/ped.2009.6): wkt_geometry vs. b_Exit, head-position occupancy from the trajectories (identical in both downloads)", fontsize=12)
fig.tight_layout(); fig.savefig(SP / "hermes_geometry_old_vs_new.png", dpi=130); print("ok")
