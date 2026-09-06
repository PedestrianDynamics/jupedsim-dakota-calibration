"""Seed-to-seed noise of the observables at default parameters (5 seeds x 3 widths)."""
import pathlib, sys
from concurrent.futures import ProcessPoolExecutor
import numpy as np
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import driver

if __name__ == "__main__":
    p = driver.read_params(HERE / "params.in"); kw = {k: float(p[k]) for k in driver.PARAMS}
    ws, seeds = [2.4, 3.6, 5.0], [1, 2, 3, 4, 5]
    jobs = [(w, s, str(HERE / f"b{w}_s{s}.sqlite"), kw) for w in ws for s in seeds]
    with ProcessPoolExecutor(3) as ex:
        rs = list(ex.map(driver.one, *zip(*jobs)))
    for f in HERE.glob("*.sqlite"): f.unlink()
    rows = np.array([[w, s, r["flow"], r["density"], r["speed"]] for (w, s, _, _), r in zip(jobs, rs)])
    np.savetxt(HERE / "noise.txt", rows, header="width seed flow density speed")
    for w in ws:
        x = rows[rows[:, 0] == w][:, 2:]
        print(f"b={w}: flow {x[:,0].mean():.2f}±{x[:,0].std(ddof=1):.2f}  density {x[:,1].mean():.2f}±{x[:,1].std(ddof=1):.2f}  speed {x[:,2].mean():.3f}±{x[:,2].std(ddof=1):.3f}")
