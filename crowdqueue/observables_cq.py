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
    """Agents present in the first frame: id -> (x, y)."""
    d = h5py.File(h5_file)["trajectory"][:]
    f0 = d[d["frame"] == d["frame"].min()]
    return {int(r["id"]): (float(r["x"]), float(r["y"])) for r in f0}


def arrivals(h5_file, fps=25.0):
    """Every tracked agent with the time and position of its first observation,
    relative to the first frame of the run: list of (t, x, y), sorted by t.
    In some runs a third of the participants enter the tracked corridor after the
    start; they must be injected, not dropped."""
    d = h5py.File(h5_file)["trajectory"][:]
    f0 = d["frame"].min(); out = []
    for i in np.unique(d["id"]):
        r = d[d["id"] == i]; k = np.argmin(r["frame"])
        out.append(((r["frame"][k] - f0) / fps, float(r["x"][k]), float(r["y"][k])))
    return sorted(out)


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
    # active-passage flow: slope of N(t) between the 10 % and 90 % crossings
    flow_active = (n[hi] - n[lo]) / (t[hi] - t[lo]) if t[hi] > t[lo] else 0.0
    t_first = t[n > 0][0] if (n > 0).any() else t[0]
    emptied = n_tot >= n_agents
    # throughput flow: everyone passed -> passed over first-to-last crossing;
    # not emptied -> passed over the time from first crossing to the end of the run
    t_last = t[n >= n_tot][0]
    flow_total = (n_tot - 1) / (t_last - t_first) if emptied and t_last > t_first else n_tot / max(t[-1] - t_first, 1e-6)
    # stall: longest interval without a crossing while agents remained upstream
    cross_t = t[np.r_[True, np.diff(n) > 0]][1:] if n_tot > 0 else np.array([])
    tail = np.r_[cross_t, t[-1]] if not emptied else cross_t
    max_gap = float(np.max(np.diff(tail))) if len(tail) > 1 else float(t[-1] - t_first)
    flow = flow_active if emptied else flow_total
    ma = area(width)
    density = pedpy.compute_classic_density(traj_data=traj, measurement_area=ma)
    speed_ind = pedpy.compute_individual_speed(traj_data=traj, frame_step=5, speed_calculation=pedpy.SpeedCalculation.BORDER_SINGLE_SIDED)
    speed = pedpy.compute_mean_speed_per_frame(traj_data=traj, individual_speed=speed_ind, measurement_area=ma)
    f_lo, f_hi = nt.index[lo], nt.index[hi]
    return {"flow": float(flow), "flow_active": float(flow_active), "flow_total": float(flow_total),
            "emptied": bool(emptied), "max_gap": max_gap, "n_agents": n_agents,
            "density": float(density.loc[f_lo:f_hi, "density"].mean()),
            "speed": float(speed.loc[f_lo:f_hi].mean()), "n_total": n_tot, "t": t, "n": n,
            "window": (float(t[lo]), float(t[hi]))}
