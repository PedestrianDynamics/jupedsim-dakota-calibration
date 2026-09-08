"""Check the Hermes 2009 archive geometry (wkt_geometry in the HDF5 files) against
the nominal bottleneck width b_Exit and against the trajectories themselves.

Writes figures/geometry_check_*.png and prints the numbers used in
hermes/geometry_check.md.
"""
import json
import pathlib

import h5py
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import shapely

matplotlib.use("Agg")
ROOT = pathlib.Path(__file__).resolve().parent.parent
FIG = ROOT / "figures"
RUNS = [("ao-240-400", 2.4), ("ao-300-400", 3.0), ("ao-360-400", 3.6), ("ao-440-400", 4.4), ("ao-500-400", 5.0)]
GAP_CENTER = 0.9
BAND = 0.5  # boards occupy |y| < 0.5


def archive_gap(wkt):
    """Return (left wall x, right wall x) of the gap read from the archive polygon holes."""
    poly = shapely.from_wkt(wkt)
    holes = [np.asarray(h.coords) for h in poly.interiors]
    xs = sorted(x for h in holes for x in (h[:, 0].min(), h[:, 0].max()))
    # holes: left board [xs[0], xs[1]], right board [xs[2], xs[3]]
    return xs[1], xs[2], (xs[0], xs[3])


def load(run):
    h = h5py.File(ROOT / "data" / f"{run}.h5")
    d = h["trajectory"][:]
    return d["x"], d["y"], h.attrs["wkt_geometry"]


def envelope(x, y, ylo, yhi, q=0.5):
    m = (y > ylo) & (y < yhi)
    if m.sum() < 50:
        return np.nan, np.nan
    return np.percentile(x[m], q), np.percentile(x[m], 100 - q)


def main():
    rows = []
    fig_h, axes_h = plt.subplots(1, 5, figsize=(22, 5), sharey=True, gridspec_kw=dict(width_ratios=[4.3, 4.9, 5.6, 6.4, 6.9]))
    fig_x, axes_x = plt.subplots(5, 1, figsize=(9, 12), sharex=True)
    fig_e, axes_e = plt.subplots(1, 5, figsize=(20, 5), sharey=True)
    for i, (run, b) in enumerate(RUNS):
        x, y, wkt = load(run)
        wl, wr, boards = archive_gap(wkt)
        nl, nr = GAP_CENTER - b / 2, GAP_CENTER + b / 2
        inband = (np.abs(y) < BAND)
        xmin, xmax = x[inband].min(), x[inband].max()
        p05, p995 = envelope(x, y, -BAND, BAND)
        rows.append(dict(run=run, b_exit=b, archive_left=wl, archive_right=wr, archive_width=round(wr - wl, 3),
                         archive_center=round((wl + wr) / 2, 3), nominal_left=nl, nominal_right=nr,
                         boards_extent=[float(boards[0]), float(boards[1])],
                         traj_xmin=round(float(xmin), 3), traj_xmax=round(float(xmax), 3),
                         traj_p05=round(float(p05), 3), traj_p995=round(float(p995), 3),
                         traj_envelope_width=round(float(xmax - xmin), 3), traj_envelope_center=round(float((xmax + xmin) / 2), 3),
                         clearance_archive=[round(float(xmin - wl), 3), round(float(wr - xmax), 3)],
                         clearance_nominal=[round(float(xmin - nl), 3), round(float(nr - xmax), 3)]))

        # (a) occupancy around the gap with both geometries
        ax = axes_h[i]
        m = (y > -1.5) & (y < 2.5) & (x > wl - 1) & (x < wr + 1)
        ax.hist2d(x[m], y[m], bins=[np.arange(wl - 1, wr + 1.001, 0.04), np.arange(-1.5, 2.501, 0.04)], cmap="Greys", cmin=1)
        poly = shapely.from_wkt(wkt)
        for hole in poly.interiors:
            hx, hy = np.asarray(hole.coords).T
            ax.fill(hx, hy, color="k", alpha=0.25, lw=0)
            ax.plot(hx, hy, "k-", lw=1)
        for n_ in (nl, nr):
            ax.plot([n_, n_], [-BAND, BAND], "r--", lw=2)
        ax.annotate(f"x1 = {wl:.2f}", (wl, -BAND), xytext=(-4, -12), textcoords="offset points", ha="right", fontsize=9)
        ax.annotate(f"x2 = {wr:.2f}", (wr, -BAND), xytext=(4, -12), textcoords="offset points", ha="left", fontsize=9)
        ax.set_title(f"{run}: b_Exit = {b} m\narchive gap x2 - x1 = {wr - wl:.2f} m")
        ax.set_xlabel("x [m]"); ax.set_aspect("equal"); ax.set_xlim(wl - 1, wr + 1)
    axes_h[0].set_ylabel("y [m]")
    axes_h[0].plot([], [], "k-", label="archive WKT boards"); axes_h[0].plot([], [], "r--", label="nominal b_Exit edges")
    axes_h[0].legend(loc="lower left", fontsize=8)
    fig_h.tight_layout(); fig_h.savefig(FIG / "geometry_check_occupancy.png", dpi=130); plt.close(fig_h)

    # (b) x histogram of head positions inside the board band
    for i, (run, b) in enumerate(RUNS):
        x, y, wkt = load(run)
        wl, wr, _ = archive_gap(wkt)
        nl, nr = GAP_CENTER - b / 2, GAP_CENTER + b / 2
        ax = axes_x[i]
        ax.hist(x[np.abs(y) < BAND], bins=np.arange(-2.5, 4.01, 0.02), color="0.6")
        for xx in (wl, wr):
            ax.axvline(xx, color="k", lw=1.5, label="archive wall" if xx == wl else None)
        for xx in (nl, nr):
            ax.axvline(xx, color="r", ls="--", lw=1.5, label="nominal b_Exit edge" if xx == nl else None)
        ax.set_ylabel("frames"); ax.set_title(f"{run}: b_Exit {b} m, archive {wr - wl:.2f} m", fontsize=10, loc="left")
    axes_x[0].legend(fontsize=8); axes_x[-1].set_xlabel("x [m]  (head positions with |y| < 0.5)")
    fig_x.tight_layout(); fig_x.savefig(FIG / "geometry_check_xhist.png", dpi=130); plt.close(fig_x)

    # (c) envelope of head positions as a function of y (0.25 m slices)
    edges = np.arange(-2, 4.01, 0.25)
    for i, (run, b) in enumerate(RUNS):
        x, y, wkt = load(run)
        wl, wr, _ = archive_gap(wkt)
        nl, nr = GAP_CENTER - b / 2, GAP_CENTER + b / 2
        ax = axes_e[i]
        lo, hi = zip(*[envelope(x, y, a, c, q=0.0) for a, c in zip(edges[:-1], edges[1:])])
        yc = (edges[:-1] + edges[1:]) / 2
        ax.plot(lo, yc, "C0.-", label="min/max x per y slice"); ax.plot(hi, yc, "C0.-")
        ax.plot([wl, wl], [-BAND, BAND], "k-", lw=2, label="archive walls"); ax.plot([wr, wr], [-BAND, BAND], "k-", lw=2)
        ax.plot([nl, nl], [-BAND, BAND], "r--", lw=2, label="nominal edges"); ax.plot([nr, nr], [-BAND, BAND], "r--", lw=2)
        ax.axhspan(-BAND, BAND, color="0.9", zorder=0)
        ax.set_title(f"{run} (b_Exit {b} m)"); ax.set_xlabel("x [m]"); ax.grid(alpha=0.3)
    axes_e[0].set_ylabel("y [m]"); axes_e[0].legend(fontsize=8)
    fig_e.tight_layout(); fig_e.savefig(FIG / "geometry_check_envelope.png", dpi=130); plt.close(fig_e)

    # (d) widths summary
    fig, ax = plt.subplots(figsize=(7, 4.5))
    bs = [r["b_exit"] for r in rows]
    ax.plot(bs, bs, "r--", label="nominal b_Exit")
    ax.plot(bs, [r["archive_width"] for r in rows], "ks", label="archive WKT gap")
    for r in rows:
        ax.annotate(f"{r['archive_width']:.2f}", (r["b_exit"], r["archive_width"]), xytext=(4, -12), textcoords="offset points", fontsize=8)
    ax.set_xlabel("nominal b_Exit [m]"); ax.set_ylabel("width [m]"); ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(FIG / "geometry_check_widths.png", dpi=130); plt.close(fig)

    json.dump(rows, open(ROOT / "results" / "geometry_check.json", "w"), indent=1)
    for r in rows:
        print(f"{r['run']}  b={r['b_exit']}  archive [{r['archive_left']:.2f},{r['archive_right']:.2f}] w={r['archive_width']:.2f} c={r['archive_center']:.3f} boards {r['boards_extent']} | traj x [{r['traj_xmin']:.2f},{r['traj_xmax']:.2f}] w={r['traj_envelope_width']:.2f} c={r['traj_envelope_center']:.2f} | clearance archive {r['clearance_archive']} nominal {r['clearance_nominal']}")


if __name__ == "__main__":
    main()
