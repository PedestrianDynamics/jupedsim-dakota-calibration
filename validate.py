"""Run the calibrated parameters on all five widths (3 seeds) and compare with
the experiments. Calibrated widths: 2.4, 3.6, 5.0; held out: 3.0, 4.4.
Usage: python3 validate.py desired_speed radius time_gap strength_neighbor range_neighbor
"""
import json, pathlib, sys
from concurrent.futures import ProcessPoolExecutor
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import driver, observables as obs

HERE = pathlib.Path(__file__).parent
WIDTHS, SEEDS, CAL = [2.4, 3.0, 3.6, 4.4, 5.0], [1, 2, 3, 4, 5, 6], {2.4, 3.6, 5.0}

if __name__ == "__main__":
    kw = dict(zip(["desired_speed", "radius", "time_gap", "strength_neighbor", "range_neighbor"], map(float, sys.argv[1:6])))
    out = HERE / "validation"; out.mkdir(exist_ok=True)
    jobs = [(w, s, str(out / f"b{w}_s{s}.sqlite"), kw) for w in WIDTHS for s in SEEDS]
    with ProcessPoolExecutor(10) as ex:
        res = list(ex.map(driver.one, *zip(*jobs)))
    sim = {w: {k: [r[k] for (ww, _, _, _), r in zip(jobs, res) if ww == w] for k in obs_keys} for w in WIDTHS for obs_keys in [("flow", "density", "speed")]}
    exp = {float(k): v for k, v in json.load(open(HERE / "exp_observables.json")).items()}
    bl = json.load(open(HERE / "baseline/baseline.json"))
    base = {v["b"]: v["sim"] for v in bl.values()}
    json.dump({"params": kw, "sim": sim}, open(out / "validation.json", "w"), indent=1)

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
    labels = {"flow": "flow J [1/s]", "density": "density [1/m$^2$]", "speed": "speed [m/s]"}
    print(f"{'b':>4} {'':>4} | {'J_exp':>6} {'J_cal':>6} | {'rho_exp':>7} {'rho_cal':>7} | {'v_exp':>5} {'v_cal':>5}")
    for ax, k in zip(axes, labels):
        ax.plot(WIDTHS, [exp[w][k] for w in WIDTHS], "ko-", label="experiment")
        ax.plot(WIDTHS, [base[w][k] for w in WIDTHS], "s--", color="gray", label="CFSM defaults")
        m = [np.mean(sim[w][k]) for w in WIDTHS]; s = [np.std(sim[w][k], ddof=1) for w in WIDTHS]
        ax.errorbar(WIDTHS, m, yerr=s, fmt="^-", color="C3", capsize=3, label="CFSM calibrated")
        for w in WIDTHS:
            if w not in CAL: ax.axvline(w, color="C3", ls=":", lw=0.8)
        ax.set_xlabel("bottleneck width b [m]"); ax.set_ylabel(labels[k])
    for w in WIDTHS:
        tag = "cal" if w in CAL else "VAL"
        print(f"{w:4.1f} {tag:>4} | {exp[w]['flow']:6.2f} {np.mean(sim[w]['flow']):6.2f} | {exp[w]['density']:7.2f} {np.mean(sim[w]['density']):7.2f} | {exp[w]['speed']:5.2f} {np.mean(sim[w]['speed']):5.2f}")
    axes[0].legend(); axes[0].set_title("dotted: held-out widths")
    fig.tight_layout(); fig.savefig(HERE / "validation.png", dpi=150)
    for f in out.glob("*.sqlite"): f.unlink()
