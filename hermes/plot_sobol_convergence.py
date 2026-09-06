"""Sobol convergence: indices from replicate runs (same N, different seeds) and
from increasing N. Figure: total index per parameter and observable vs N, with
the replicate spread at N = 40. Also prints a table for the article.
Usage: python3 plot_sobol_convergence.py  (reads sobol*/dakota.out)"""
import pathlib, re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = pathlib.Path(__file__).parent
RUNS = {"sobol": (40, 3), "sobol_N40_s11": (40, 11), "sobol_N40_s17": (40, 17), "sobol_N80_s3": (80, 3), "sobol_N160_s3": (160, 3)}


def parse(path):
    txt = path.read_text(); out = {}; resp = None
    for line in txt.splitlines():
        m = re.match(r"\s*(\S+) Sobol' indices:", line)
        if m:
            resp = m.group(1); out[resp] = {}; continue
        row = line.split()
        if resp and len(row) == 3 and row[2] not in ("Main", "Total"):
            try:
                out[resp][row[2]] = (float(row[0]), float(row[1]))
            except ValueError:
                pass
    return out


data = {}
for d, (N, seed) in RUNS.items():
    f = HERE / d / "dakota.out"
    if f.exists() and "Environment execution completed" in f.read_text():
        data[(N, seed)] = parse(f)
if not data:
    raise SystemExit("no finished runs")
params = ["desired_speed", "radius", "time_gap", "strength_neighbor", "range_neighbor"]
resp = ["flow_2.4", "density_2.4", "speed_2.4", "flow_3.6", "density_3.6", "speed_3.6", "flow_5.0", "density_5.0", "speed_5.0"]
Ns = sorted({N for N, _ in data})
fig, axes = plt.subplots(3, 3, figsize=(13, 9), sharex=True)
for ax, r in zip(axes.ravel(), resp):
    for j, p in enumerate(params):
        xs, ys, lo, hi = [], [], [], []
        for N in Ns:
            vals = [data[k][r][p][1] for k in data if k[0] == N]
            xs.append(N); ys.append(np.mean(vals)); lo.append(min(vals)); hi.append(max(vals))
        ax.errorbar(xs, ys, yerr=[np.array(ys) - lo, np.array(hi) - np.array(ys)], fmt="o-", ms=4, capsize=3, color=f"C{j}", label=p)
    ax.set_title(r, fontsize=10); ax.set_xscale("log", base=2); ax.set_xticks(Ns, [str(n) for n in Ns]); ax.set_ylim(-0.05, 1)
for ax in axes[-1]: ax.set_xlabel("base samples N (evaluations = 7N)")
for ax in axes[:, 0]: ax.set_ylabel("total Sobol index")
axes[0, 0].legend(fontsize=7)
fig.suptitle("Sobol total indices vs sample size; bars at N = 40 span three replicate seeds", fontsize=11)
fig.tight_layout(); fig.savefig(HERE / "sobol_convergence.png", dpi=150)
# table: at the largest N, total index with replicate range at N=40
Nmax = max(Ns)
print(f"total indices at N={Nmax} (range over replicates at N=40 in brackets)")
print(f"{'param':18s}" + "".join(f"{r:>18s}" for r in resp))
for p in params:
    cells = []
    for r in resp:
        big = np.mean([data[k][r][p][1] for k in data if k[0] == Nmax])
        reps = [data[k][r][p][1] for k in data if k[0] == 40]
        cells.append(f"{big:5.2f} [{min(reps):.2f}-{max(reps):.2f}]")
    print(f"{p:18s}" + "".join(f"{c:>18s}" for c in cells))
# first-order vs total consistency at largest N
viol = sum(1 for k in data if k[0] == Nmax for r in resp for p in params if data[k][r][p][0] > data[k][r][p][1] + 0.05)
print(f"first-order > total by more than 0.05 at N={Nmax}: {viol} of {9*5} cells")
