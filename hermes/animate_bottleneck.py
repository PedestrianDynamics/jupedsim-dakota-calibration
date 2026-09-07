"""Animate one Hermes run, experiment beside simulation.

Both clocks are zeroed at the first crossing of the flow line, because the
experiment's tracking starts before the participants enter the camera window.

Left: the tracked experiment inside the camera window. Right: JuPedSim with
the calibrated set A (desired speed fixed at 1.55 m/s), seed 1, cropped to the
same window. The red line is the flow line across the gap and the blue box the
density and speed area. Illustration only; the numbers of the note come from
the scripts named in the README.

Usage: python3 animate_bottleneck.py [width] [out.gif]
"""
import pathlib
import sys

import matplotlib
import numpy as np
from PIL import Image

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, Rectangle  # noqa: E402

import observables as obs  # noqa: E402
import scenario  # noqa: E402

HERE = pathlib.Path(__file__).parent
SET_A = dict(desired_speed=1.55, radius=0.127, time_gap=0.811, strength_neighbor=2.09, range_neighbor=0.248)
STEP = 0.5          # seconds between animation frames
X_LO, X_HI = -2.5, 4.3   # camera window of the experiment, plus a margin
Y_LO, Y_HI = -3.0, 8.0


def first_crossing(traj):
    return traj.data[traj.data["y"] < obs.FLOW_LINE_Y]["frame"].min() / traj.frame_rate


def positions_at(traj, time):
    frame = int(round(time * traj.frame_rate))
    if frame < 0:
        return np.empty(0), np.empty(0)
    rows = traj.data[traj.data["frame"] == frame]
    return rows["x"].to_numpy(), rows["y"].to_numpy()


def passed_by(traj, time):
    frame = int(round(time * traj.frame_rate))
    below = traj.data[(traj.data["y"] < obs.FLOW_LINE_Y) & (traj.data["frame"] <= frame)]
    return below["id"].nunique()


def draw_panel(ax, width, title):
    half = width / 2
    for x0, x1 in ((X_LO, obs.GAP_CENTER - half), (obs.GAP_CENTER + half, X_HI)):
        ax.add_patch(Rectangle((x0, -0.5), x1 - x0, 1.0, facecolor="#bbbbbb", edgecolor="black", lw=0.8))
    ax.plot([obs.GAP_CENTER - half, obs.GAP_CENTER + half], [obs.FLOW_LINE_Y] * 2, color="#d62728", lw=1.5)
    xs, ys = zip(*obs.AREA.polygon.exterior.coords)
    ax.plot(xs, ys, color="#1f77b4", lw=1.2, ls="--")
    ax.set_xlim(X_LO, X_HI)
    ax.set_ylim(Y_LO, Y_HI)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title, fontsize=10)


def main(width, out_path):
    exp = obs.load_experiment(HERE.parent / "data" / f"ao-{int(width * 100)}-400.h5")
    sqlite = HERE / "results" / f"anim_b{width}.sqlite"
    sqlite.parent.mkdir(exist_ok=True)
    scenario.run(width, 1, str(sqlite), **SET_A)
    sim = obs.load_simulation(sqlite)
    # both clocks start at the first crossing of the flow line
    offsets = {id(exp): first_crossing(exp), id(sim): first_crossing(sim)}
    t_end = max(traj.data["frame"].max() / traj.frame_rate - offsets[id(traj)] for traj in (exp, sim))
    times = np.arange(-1.0, t_end + 1e-9, STEP)

    frames = []
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 6.0), dpi=80)
    for _ in range(3):
        fig.tight_layout(rect=(0, 0, 1, 0.94))
    for time in times:
        for ax, (traj, kind, colour) in zip(axes, ((exp, "experiment", "#0072b2"), (sim, "simulation, set A", "#009e73"))):
            ax.clear()
            draw_panel(ax, width, kind)
            local = time + offsets[id(traj)]
            x, y = positions_at(traj, local)
            for xi, yi in zip(x, y):
                ax.add_patch(Circle((xi, yi), 0.15, facecolor=colour, edgecolor="none", alpha=0.85))
            ax.set_xlabel(f"{passed_by(traj, local)} passed", fontsize=10)
        fig.suptitle(f"Hermes bottleneck, {width} m   t = {time:5.1f} s", fontsize=11)
        fig.canvas.draw()
        frames.append(np.asarray(fig.canvas.buffer_rgba())[..., :3].copy())  # type: ignore[attr-defined]
    plt.close(fig)
    images = [Image.fromarray(f).quantize(colors=64) for f in frames]
    images[0].save(out_path, save_all=True, append_images=images[1:], duration=int(STEP * 500), loop=0)
    sqlite.unlink(missing_ok=True)
    print(f"wrote {out_path} ({len(frames)} frames)")


if __name__ == "__main__":
    width = float(sys.argv[1]) if len(sys.argv) > 1 else 3.6
    main(width, sys.argv[2] if len(sys.argv) > 2 else "bottleneck.gif")
