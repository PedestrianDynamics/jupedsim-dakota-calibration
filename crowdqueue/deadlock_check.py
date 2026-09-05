"""Are the zero-flow seeds genuine deadlocks? Run 270_c_34_h0 with 5 seeds and report
crossings, elapsed simulated time and agents left."""
import pathlib, sys
import jupedsim as jps, shapely, numpy as np
import scenario_cq, observables_cq as obs
kw = dict(desired_speed=1.55, radius=0.1275, time_gap=0.8112, strength_neighbor=2.087, range_neighbor=0.2482)
pathlib.Path("noise").mkdir(exist_ok=True)
for seed in range(1, 6):
    f = f"noise/dl_{seed}.sqlite"
    t = scenario_cq.run("270_c_34_h0", seed, f, **kw)
    r = obs.compute(obs.load_simulation(f), 3.4)
    tr = obs.load_simulation(f).data
    last = tr[tr.frame == tr.frame.max()]
    print(f"seed {seed}: elapsed {t:.0f} s, crossed {r['n_total']}, agents left at end {len(last)}, flow {r['flow']:.2f}; stuck agents y-range [{last.y.min():.2f},{last.y.max():.2f}]" if len(last) else f"seed {seed}: elapsed {t:.0f} s, crossed {r['n_total']}, all out, flow {r['flow']:.2f}")
    pathlib.Path(f).unlink()
