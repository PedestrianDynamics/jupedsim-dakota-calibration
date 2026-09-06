"""Experiment vs default-parameter simulation: N(t) curves and J(b)."""
import glob, json, pathlib, re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import observables as obs

HERE = pathlib.Path(__file__).parent
DATA = HERE.parent / "data"
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
cols = plt.cm.viridis([0, .25, .5, .75, 1.0])
for c, f in zip(cols, sorted(glob.glob(str(DATA / "ao-*.h5")))):
    k = re.search(r"ao-(\d+)-", f).group(1); b = int(k) / 100
    e = obs.compute(obs.load_experiment(f), b)
    s = obs.compute(obs.load_simulation(HERE / "baseline" / f"sim_{k}.sqlite"), b)
    ax[0].plot(e["t"] - e["t"][e["n"] > 0][0], e["n"], color=c, label=f"b = {b} m")
    ax[0].plot(s["t"] - s["t"][s["n"] > 0][0], s["n"], color=c, ls="--")
ax[0].set_xlabel("time since first crossing [s]"); ax[0].set_ylabel("N crossed")
ax[0].set_title("N(t): experiment (solid) vs CFSM defaults (dashed)"); ax[0].legend(fontsize=8)
bl = json.load(open(HERE / "baseline/baseline.json"))
bs = sorted(v["b"] for v in bl.values())
for key, m, lab in (("exp", "o-", "experiment"), ("sim", "s--", "CFSM defaults")):
    ax[1].plot(bs, [next(v[key]["flow"] for v in bl.values() if v["b"] == b) for b in bs], m, label=lab)
ax[1].set_xlabel("bottleneck width b [m]"); ax[1].set_ylabel("flow J [1/s]"); ax[1].set_title("Flow vs width"); ax[1].legend()
fig.tight_layout(); fig.savefig(HERE / "baseline.png", dpi=150); print("ok")
