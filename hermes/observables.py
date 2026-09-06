"""Observables shared by experiment and simulation (Hermes 2009 bottleneck).

Coordinates: gap centred at x = 0.9, walls occupy |y| < 0.5, flow in -y.
"""
import pathlib

import numpy as np
import pedpy

GAP_CENTER = 0.9
FLOW_LINE_Y = 0.0
# density/speed box directly in front of the bottleneck, inside the camera window
AREA = pedpy.MeasurementArea([(-0.5, 0.6), (2.3, 0.6), (2.3, 2.6), (-0.5, 2.6)])


def load_experiment(h5_file):
    return pedpy.load_trajectory_from_ped_data_archive_hdf5(pathlib.Path(h5_file))


def load_simulation(sqlite_file):
    return pedpy.load_trajectory_from_jupedsim_sqlite(pathlib.Path(sqlite_file))


def compute(traj, gap_width):
    """Return dict: steady flow J [1/s], mean density [1/m2], mean speed [m/s],
    plus the N(t) curve (t, n) at the bottleneck line."""
    half = gap_width / 2
    line = pedpy.MeasurementLine([(GAP_CENTER - half, FLOW_LINE_Y), (GAP_CENTER + half, FLOW_LINE_Y)])
    nt, _ = pedpy.compute_n_t(traj_data=traj, measurement_line=line)
    t = nt["time"].to_numpy()
    n = nt["cumulative_pedestrians"].to_numpy()
    n_tot = n.max()
    # steady state: between 10 % and 90 % of all crossings
    lo, hi = np.searchsorted(n, 0.1 * n_tot), np.searchsorted(n, 0.9 * n_tot)
    flow = (n[hi] - n[lo]) / (t[hi] - t[lo])

    density = pedpy.compute_classic_density(traj_data=traj, measurement_area=AREA)
    speed_ind = pedpy.compute_individual_speed(traj_data=traj, frame_step=5, speed_calculation=pedpy.SpeedCalculation.BORDER_SINGLE_SIDED)
    speed = pedpy.compute_mean_speed_per_frame(traj_data=traj, individual_speed=speed_ind, measurement_area=AREA)
    # jam window: same steady-state frames as the flow
    f_lo, f_hi = nt.index[lo], nt.index[hi]
    rho = density.loc[f_lo:f_hi, "density"].mean()
    v = speed.loc[f_lo:f_hi].mean()
    return {"flow": flow, "density": rho, "speed": v, "t": t, "n": n, "n_total": int(n_tot), "window": (float(t[lo]), float(t[hi]))}
