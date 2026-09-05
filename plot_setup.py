"""Measurement setup check: archive walkable area, trajectories, flow line, density area."""
import pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pedpy
import shapely
import observables as obs
import scenario

HERE = pathlib.Path(__file__).parent
fig, axes = plt.subplots(1, 2, figsize=(14, 8))
for ax, b in zip(axes, (2.4, 5.0)):
    f = HERE.parent / "data" / f"ao-{int(b*100)}-400.h5"
    traj = obs.load_experiment(f)
    wa_exp = pedpy.load_walkable_area_from_ped_data_archive_hdf5(f)
    line = pedpy.MeasurementLine([(obs.GAP_CENTER - b / 2, obs.FLOW_LINE_Y), (obs.GAP_CENTER + b / 2, obs.FLOW_LINE_Y)])
    pedpy.plot_measurement_setup(
        traj=traj, walkable_area=wa_exp, measurement_lines=[line], measurement_areas=[obs.AREA],
        axes=ax, traj_alpha=0.15, traj_width=0.3, ml_color="red", ml_width=3, ma_color="blue", ma_alpha=0.15, ma_line_color="blue")
    # simulation geometry (walls closed to the sides) as dashed outline
    sim_geo = scenario.geometry(b)
    for ring in [sim_geo.exterior, *sim_geo.interiors]:
        ax.plot(*ring.xy, "k--", lw=1)
    pts = np.array(scenario.waiting_positions(1, 0.2))
    ax.plot(pts[:, 0], pts[:, 1], ".", color="C2", ms=2.5, alpha=0.8, label="initial agents (sim)")
    ax.axvline(-2.2, color="gray", ls=":"); ax.axvline(4.0, color="gray", ls=":")
    ax.set_title(f"b = {b} m")
    ax.set_aspect("equal")
fig.suptitle("archive area (solid), simulation geometry (dashed), initial agents in the holding area (green), camera window (dotted), flow line (red), density area (blue)")
fig.tight_layout(); fig.savefig(HERE / "setup.png", dpi=130); print("ok")
