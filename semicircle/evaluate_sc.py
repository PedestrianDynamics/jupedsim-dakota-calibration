"""Simulate the semicircle run with a parameter set (N seeds); compare entrance flow
and time-averaged density map with the experiment.
Usage: python3 evaluate_sc.py <label> v0 radius time_gap strength_n range_n strength_g range_g [--seeds N]"""
import json, pathlib, sys
from concurrent.futures import ProcessPoolExecutor
import h5py, numpy as np, pedpy
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import scenario_sc

LINE = pedpy.MeasurementLine([(-1.85, -0.45), (-0.15, -0.45)])
GRID = (np.arange(-4.0, 4.01, 0.5), np.arange(-0.5, 4.51, 0.5))
WINDOW = (20.0, 110.0)  # s, jam phase


def density_map(df, fps):
    d = df[(df.frame / fps >= WINDOW[0]) & (df.frame / fps <= WINDOW[1])]
    n_frames = d.frame.nunique()
    H, _, _ = np.histogram2d(d.x, d.y, bins=GRID)
    return H / n_frames / 0.25  # persons per m2, time-averaged


def flow(traj):
    nt, _ = pedpy.compute_n_t(traj_data=traj, measurement_line=LINE)
    t, n = nt["time"].to_numpy(), nt["cumulative_pedestrians"].to_numpy()
    m = (t >= WINDOW[0]) & (t <= WINDOW[1])
    return (n[m][-1] - n[m][0]) / (t[m][-1] - t[m][0]), int(n.max())


def one(seed, out, kw):
    try:
        left = scenario_sc.run(seed, out, **kw)
    except RuntimeError as e:  # model pushed an agent through a wall: the run is invalid
        return dict(flow=float("nan"), crossed=0, not_placed=-1, dmap=None, error=str(e)[:80])
    tr = pedpy.load_trajectory_from_jupedsim_sqlite(pathlib.Path(out))
    J, n = flow(tr)
    return dict(flow=float(J), crossed=n, not_placed=left, dmap=density_map(tr.data, tr.frame_rate).tolist())


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    n_seeds = int(sys.argv[sys.argv.index("--seeds") + 1]) if "--seeds" in sys.argv else 3
    label = args[0]
    kw = dict(zip(["desired_speed", "radius", "time_gap", "strength_neighbor", "range_neighbor", "strength_geometry", "range_geometry"], map(float, args[1:])))
    out = pathlib.Path("results"); out.mkdir(exist_ok=True)
    exp = pedpy.load_trajectory_from_ped_data_archive_hdf5(scenario_sc.DATA)
    Je, ne = flow(exp); dm_e = density_map(exp.data, exp.frame_rate)
    with ProcessPoolExecutor(n_seeds) as ex:
        res = list(ex.map(one, range(1, n_seeds + 1), [str(out / f"{label}_s{s}.sqlite") for s in range(1, n_seeds + 1)], [kw] * n_seeds))
    Js = [r["flow"] for r in res if r["dmap"] is not None]
    fails = [r.get("error") for r in res if r["dmap"] is None]
    print(f"{label}: experiment flow {Je:.2f} /s ({ne} crossed); simulation {np.mean(Js) if Js else float('nan'):.2f} ± {np.std(Js, ddof=1) if len(Js) > 1 else 0:.2f} /s over {len(Js)} valid seeds, crossed {[r['crossed'] for r in res]}, failed runs: {fails}")
    json.dump({"params": kw, "exp": {"flow": Je, "crossed": ne, "dmap": dm_e.tolist()}, "sim": res}, open(out / f"{label}.json", "w"))
    for f in out.glob("*.sqlite"): f.unlink()
