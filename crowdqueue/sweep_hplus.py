"""Explicit time-gap sweep for the high-motivation run 020 (3 seeds per point),
all other parameters as given on the command line: python3 sweep_hplus.py radius strength_n range_n strength_g range_g"""
import json, pathlib, sys
from concurrent.futures import ProcessPoolExecutor
import driver_cq
T = [0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0, 1.2, 1.5, 2.0]
if __name__ == "__main__":
    r, sn, rn, sg, rg = map(float, sys.argv[1:6])
    out = pathlib.Path("results"); out.mkdir(exist_ok=True)
    jobs = [("020_c_12_h+", s, str(out / f"hp_{t}_{s}.sqlite"), dict(desired_speed=1.55, radius=r, time_gap=t, strength_neighbor=sn, range_neighbor=rn, strength_geometry=sg, range_geometry=rg)) for t in T for s in (1, 2, 3)]
    with ProcessPoolExecutor(6) as ex:
        res = list(ex.map(driver_cq.one, *zip(*jobs)))
    json.dump({"T": T, "seeds": [1, 2, 3], "results": [{"time_gap": j[3]["time_gap"], "seed": j[1], **{k: v for k, v in x.items() if k != "nt"}} for j, x in zip(jobs, res)]}, open(out / "hplus_sweep.json", "w"), indent=1)
    for f in out.glob("hp_*.sqlite"): f.unlink()
    print("sweep done")
