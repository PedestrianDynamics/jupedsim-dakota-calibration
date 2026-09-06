"""Animate the paired 63-person 1.2 m runs, experiment beside simulation.

Top row: baseline motivation (run 110), bottom row: low motivation (run 120).
Left: tracked experiment, right: JuPedSim at the condition-specific v0/T
profile point with the other parameters at set C, seed 1, replaying the
observed initial positions and arrivals. The rectangle is the 2.2 m² front
measurement area. Illustration only; the numbers of the note come from the
scripts named in the README.

Usage: python3 animate_motivation_pair.py [out.gif]
"""
import pathlib
import sys

import matplotlib
import numpy as np
import shapely
from PIL import Image

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, Polygon as MplPolygon  # noqa: E402

import observables_cq as obs  # noqa: E402
import scenario_cq  # noqa: E402
from evaluate_front_occupancy import condition_parameters  # noqa: E402

PAIR = [("110_c_12_h0", "h0"), ("120_c_12_h-", "h−")]
STEP = 0.4          # seconds between animation frames
T_END = 65.0
Y_LO, Y_HI = -2.0, 9.0


def corridor_polygon(run):
    geo = shapely.from_wkt(obs.geometry_wkt(run["file"]))
    half = run["width"] / 2 + 0.15
    clipped = geo.intersection(shapely.box(-half, -4.0, half, 12.0))
    parts = [g for g in getattr(clipped, "geoms", [clipped]) if g.geom_type == "Polygon"]
    return max(parts, key=lambda g: g.area)


def positions_at(traj, time):
    frame = int(round(time * traj.frame_rate))
    rows = traj.data[traj.data["frame"] == frame]
    return rows["x"].to_numpy(), rows["y"].to_numpy()


def passed_by(traj, time):
    frame = int(round(time * traj.frame_rate))
    below = traj.data[(traj.data["y"] < -0.6) & (traj.data["frame"] <= frame)]
    return below["id"].nunique()


def draw_panel(ax, poly, width, title):
    ax.add_patch(MplPolygon(np.asarray(poly.exterior.coords), closed=True,
                            facecolor="#f4f4f4", edgecolor="black", lw=1.2))
    hw = width / 2 - 0.05
    ax.add_patch(MplPolygon([(-hw, 0.5), (hw, 0.5), (hw, 2.5), (-hw, 2.5)], closed=True,
                            fill=False, edgecolor="#d55e00", lw=1.5, ls="--"))
    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(Y_LO, Y_HI)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title, fontsize=9)


def main(out_path):
    params = condition_parameters()
    runs = obs.runs()
    panels = []
    for run_name, label in PAIR:
        run = runs[run_name]
        sqlite = pathlib.Path("results") / f"anim_{run_name}.sqlite"
        scenario_cq.run(run_name, 1, str(sqlite), **params[run["motivation"]])
        panels.append((label, run, obs.load_experiment(run["file"]), obs.load_simulation(sqlite), sqlite))

    times = np.arange(0.0, T_END + 1e-9, STEP)
    frames = []
    fig, axes = plt.subplots(1, 4, figsize=(8.0, 6.4), dpi=80)
    # fix the panel positions once: tight_layout on equal-aspect axes converges
    # over several calls, so calling it per frame makes the panels drift
    for ax, (label, run, *_) in zip(axes, [p for p in panels for _ in (0, 1)]):
        draw_panel(ax, corridor_polygon(run), run["width"], f"{label}\nexperiment")
        ax.set_xlabel("00 in area\n00 passed", fontsize=9)
    fig.suptitle("placeholder", fontsize=11)
    for _ in range(3):
        fig.tight_layout(rect=(0, 0, 1, 0.96))
    for time in times:
        for row, (label, run, exp, sim, _) in enumerate(panels):  # noqa: B007
            poly = corridor_polygon(run)
            for col, (traj, kind, colour) in enumerate(((exp, "experiment", "#0072b2"), (sim, "simulation", "#009e73"))):
                ax = axes[2 * row + col]
                ax.clear()
                draw_panel(ax, poly, run["width"], f"{label}\n{kind}")
                x, y = positions_at(traj, time)
                for xi, yi in zip(x, y):
                    ax.add_patch(Circle((xi, yi), 0.15, facecolor=colour, edgecolor="none", alpha=0.85))
                in_area = int(np.sum((np.abs(x) < run["width"] / 2 - 0.05) & (y > 0.5) & (y < 2.5)))
                ax.set_xlabel(f"{in_area} in area\n{passed_by(traj, time)} passed", fontsize=9)
        fig.suptitle(f"CrowdQueue, 1.2 m corridor, 63 people   t = {time:5.1f} s", fontsize=11)
        fig.canvas.draw()
        frames.append(np.asarray(fig.canvas.buffer_rgba())[..., :3].copy())  # type: ignore[attr-defined]
    plt.close(fig)
    images = [Image.fromarray(f).quantize(colors=64) for f in frames]
    images[0].save(out_path, save_all=True, append_images=images[1:], duration=int(STEP * 500), loop=0)
    for *_, sqlite in panels:
        sqlite.unlink(missing_ok=True)
    print(f"wrote {out_path} ({len(frames)} frames)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "motivation_pair.gif")
