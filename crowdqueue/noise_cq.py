"""Seed noise of CrowdQueue observables (5 seeds x 3 runs) at given parameters."""
import pathlib
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import driver_cq

kw = dict(desired_speed=1.55, radius=0.1275, time_gap=0.8112, strength_neighbor=2.087, range_neighbor=0.2482)
runs, seeds = ["270_c_34_h0", "030_c_56_h0", "230_q_23_h0"], range(1, 6)

if __name__ == "__main__":
    pathlib.Path("noise").mkdir(exist_ok=True)
    jobs = [(r, s, f"noise/{r}_s{s}.sqlite", kw) for r in runs for s in seeds]
    with ProcessPoolExecutor(5) as ex:
        res = list(ex.map(driver_cq.one, *zip(*jobs)))
    for r in runs:
        x = np.array([[v["flow"], v["density"], v["speed"]] for (n, *_), v in zip(jobs, res) if n == r])
        m, s = x.mean(0), x.std(0, ddof=1)
        print(f"{r}: flow {m[0]:.2f}±{s[0]:.2f} ({s[0]/m[0]:.0%})  density {m[1]:.2f}±{s[1]:.2f} ({s[1]/m[1]:.0%})  speed {m[2]:.3f}±{s[2]:.3f} ({s[2]/m[2]:.0%})")
    for f in pathlib.Path("noise").glob("*.sqlite"):
        f.unlink()
