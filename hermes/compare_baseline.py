"""Experiment observables for all runs + one default-parameter simulation each."""
import glob, json, pathlib, re, sys, time
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import observables as obs
import scenario

DATA = pathlib.Path(__file__).parent.parent / "data"
RUNS = {re.search(r"ao-(\d+)-", f).group(1): f for f in sorted(glob.glob(str(DATA / "ao-*.h5")))}


def sim_job(b, out):
    scenario.run(b, seed=1, out_file=out)
    return out


if __name__ == "__main__":
    out_dir = pathlib.Path(__file__).parent / "baseline"; out_dir.mkdir(exist_ok=True)
    t0 = time.time()
    with ProcessPoolExecutor(5) as ex:
        sims = dict(zip(RUNS, ex.map(sim_job, [int(k) / 100 for k in RUNS], [str(out_dir / f"sim_{k}.sqlite") for k in RUNS])))
    print(f"5 baseline sims in {time.time()-t0:.0f} s")
    table = {}
    print(f"{'b[m]':>5} | {'J_exp':>6} {'J_sim':>6} | {'rho_exp':>7} {'rho_sim':>7} | {'v_exp':>5} {'v_sim':>5} | N_exp N_sim")
    for k, f in RUNS.items():
        b = int(k) / 100
        e = obs.compute(obs.load_experiment(f), b)
        s = obs.compute(obs.load_simulation(sims[k]), b)
        table[k] = {"b": b, "exp": {x: e[x] for x in ("flow", "density", "speed", "n_total")}, "sim": {x: s[x] for x in ("flow", "density", "speed", "n_total")}}
        print(f"{b:5.1f} | {e['flow']:6.2f} {s['flow']:6.2f} | {e['density']:7.2f} {s['density']:7.2f} | {e['speed']:5.2f} {s['speed']:5.2f} | {e['n_total']:5d} {s['n_total']:5d}")
    json.dump(table, open(out_dir / "baseline.json", "w"), indent=1)
