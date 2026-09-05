"""Observables for the CrowdQueue entrance (Wuppertal 2018), experiment and simulation.

Gate passage 0.5 m wide from y = -0.15 to -1.1 (archive coordinates), flow in -y.
Flow line at y = -0.6 inside the passage; density/speed area in the corridor
directly in front of the gate, x within the corridor, y in [0.5, 2.5].
"""
import pathlib
import re

import h5py
import numpy as np
import pedpy
import shapely

DATA = pathlib.Path(__file__).resolve().parent.parent / "data" / "crowdqueue"
EXCLUDE = {"010", "080", "200"}  # "trajectories are not corrected"


def runs():
    out = {}
    for f in sorted(DATA.glob("*.h5")):
        m = re.match(r"(\d+)_([cq])_(\d+)_(h[0+-])\.h5", f.name)
        if not m or m.group(1) in EXCLUDE:
            continue
        out[f.stem] = dict(file=f, id=m.group(1), priming=m.group(2), width=int(m.group(3)) / 10, motivation=m.group(4))
    return out


def geometry_wkt(h5_file):
    return h5py.File(h5_file).attrs["wkt_geometry"]


def initial_positions(h5_file):
    d = h5py.File(h5_file)["trajectory"][:]
    f0 = d[d["frame"] == d["frame"].min()]
    return {int(r["id"]): (float(r["x"]), float(r["y"])) for r in f0}


def load_experiment(h5_file):
    return pedpy.load_trajectory_from_ped_data_archive_hdf5(pathlib.Path(h5_file))


def load_simulation(sqlite_file):
    return pedpy.load_trajectory_from_jupedsim_sqlite(pathlib.Path(sqlite_file))


def area(width):
    hw = width / 2 - 0.05
    return pedpy.MeasurementArea([(-hw, 0.5), (hw, 0.5), (hw, 2.5), (-hw, 2.5)])


def compute(traj, width):
    line = pedpy.MeasurementLine([(-0.25, -0.6), (0.25, -0.6)])
    nt, _ = pedpy.compute_n_t(traj_data=traj, measurement_line=line)
    t, n = nt["time"].to_numpy(), nt["cumulative_pedestrians"].to_numpy()
    n_tot = int(n.max())
    n_agents = int(traj.data["id"].nunique())
    lo, hi = np.searchsorted(n, 0.1 * n_tot), np.searchsorted(n, 0.9 * n_tot)
    flow = (n[hi] - n[lo]) / (t[hi] - t[lo]) if t[hi] > t[lo] else 0.0
    if n_tot < n_agents:
        # clogged run: not everyone got through, so the flow is what passed over the whole run
        t_first = t[n > 0][0] if (n > 0).any() else t[0]
        flow = n_tot / max(t[-1] - t_first, 1e-6)
    ma = area(width)
    density = pedpy.compute_classic_density(traj_data=traj, measurement_area=ma)
    speed_ind = pedpy.compute_individual_speed(traj_data=traj, frame_step=5, speed_calculation=pedpy.SpeedCalculation.BORDER_SINGLE_SIDED)
    speed = pedpy.compute_mean_speed_per_frame(traj_data=traj, individual_speed=speed_ind, measurement_area=ma)
    f_lo, f_hi = nt.index[lo], nt.index[hi]
    return {"flow": float(flow), "density": float(density.loc[f_lo:f_hi, "density"].mean()),
            "speed": float(speed.loc[f_lo:f_hi].mean()), "n_total": n_tot, "t": t, "n": n}
