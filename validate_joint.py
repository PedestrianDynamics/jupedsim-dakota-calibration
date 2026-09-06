"""Joint-calibration parameters (from joint/best_params.json) on all five Hermes widths, 3 seeds."""
import sys, json, pathlib
from concurrent.futures import ProcessPoolExecutor
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import driver

kw = json.load(open(pathlib.Path(__file__).parent.parent / "joint" / "best_params.json"))
W, S = [2.4, 3.0, 3.6, 4.4, 5.0], [1, 2, 3]

if __name__ == "__main__":
    out = pathlib.Path("validation"); out.mkdir(exist_ok=True)
    jobs = [(w, s, str(out / f"j_b{w}_s{s}.sqlite"), kw) for w in W for s in S]
    with ProcessPoolExecutor(6) as ex:
        res = list(ex.map(driver.one, *zip(*jobs)))
    exp = {float(k): v for k, v in json.load(open("exp_observables.json")).items()}
    sim = {w: {k: [r[k] for (ww, *_), r in zip(jobs, res) if ww == w] for k in ("flow", "density", "speed")} for w in W}
    json.dump({"params": kw, "sim": sim}, open(out / "validation_joint.json", "w"), indent=1)
    print(f"{'b':>4} | J_exp J_sim | rho_exp rho_sim | v_exp v_sim")
    for w in W:
        print(f"{w:4.1f} | {exp[w]['flow']:5.2f} {np.mean(sim[w]['flow']):5.2f} | {exp[w]['density']:7.2f} {np.mean(sim[w]['density']):7.2f} | {exp[w]['speed']:5.2f} {np.mean(sim[w]['speed']):5.2f}")
    for f in out.glob("j_*.sqlite"):
        f.unlink()
