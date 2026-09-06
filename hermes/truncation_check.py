"""Does losing the last 100 written frames (6 s) change the Hermes observables?
For each width and two parameter sets: simulate with the closed writer, then make a
copy of the trajectory with the last 100 frames deleted and compute both."""
import pathlib, shutil, sqlite3, sys, json
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import scenario, observables as obs

SETS = {"defaults": dict(), "set A": dict(desired_speed=1.55, radius=0.12749, time_gap=0.81118, strength_neighbor=2.0872, range_neighbor=0.24816)}
W = [2.4, 3.6, 5.0]


def job(name, w):
    out = pathlib.Path("trunc"); out.mkdir(exist_ok=True)
    f = out / f"{name.replace(' ', '_')}_{w}.sqlite"; g = out / f"{name.replace(' ', '_')}_{w}_trunc.sqlite"
    scenario.run(w, 1, str(f), **SETS[name])
    shutil.copy(f, g)
    con = sqlite3.connect(g); fmax = con.execute("select max(frame) from trajectory_data").fetchone()[0]
    con.execute("delete from trajectory_data where frame > ?", (fmax - 100,)); con.execute("delete from frame_data where frame > ?", (fmax - 100,)); con.commit(); con.close()
    a = obs.compute(obs.load_simulation(f), w); b = obs.compute(obs.load_simulation(g), w)
    return dict(set=name, width=w, full=dict(n=a["n_total"], window=[round(x, 1) for x in a["window"]], flow=a["flow"], density=a["density"], speed=a["speed"]),
                trunc=dict(n=b["n_total"], window=[round(x, 1) for x in b["window"]], flow=b["flow"], density=b["density"], speed=b["speed"]))


if __name__ == "__main__":
    jobs = [(n, w) for n in SETS for w in W]
    with ProcessPoolExecutor(6) as ex:
        res = list(ex.map(job, *zip(*jobs)))
    json.dump(res, open("truncation_check.json", "w"), indent=1)
    print(f"{'set':9s} {'b':>4} | crossings full/trunc | window full -> trunc | flow | density | speed  (relative change)")
    for r in res:
        a, b = r["full"], r["trunc"]
        print(f"{r['set']:9s} {r['width']:4.1f} | {a['n']:3d} / {b['n']:3d} | {a['window']} -> {b['window']} | {b['flow']/a['flow']-1:+.1%} | {b['density']/a['density']-1:+.1%} | {b['speed']/a['speed']-1:+.1%}")
    shutil.rmtree("trunc")
