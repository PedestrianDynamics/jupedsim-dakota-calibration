"""Heatmap of total Sobol indices: parameter x observable, parsed from sobol/dakota.out."""
import pathlib, re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = pathlib.Path(__file__).parent
txt = (HERE / "sobol/dakota.out").read_text()
blocks = re.findall(r"(\S+) Sobol' indices:\s*\n\s*Main\s+Total\s*\n((?:\s*\S+\s+\S+\s+\S+\s*\n)+)", txt)
resp, params, main, total = [], None, [], []
for name, body in blocks:
    rows = [l.split() for l in body.strip().splitlines()]
    params = [r[2] for r in rows]
    resp.append(name); main.append([float(r[0]) for r in rows]); total.append([float(r[1]) for r in rows])
main, total = np.array(main).T, np.array(total).T
fig, axes = plt.subplots(1, 2, figsize=(13, 4.2))
for ax, m, t in zip(axes, (main, total), ("main (first order)", "total")):
    im = ax.imshow(np.clip(m, 0, 1), cmap="Blues", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(resp)), resp, rotation=45, ha="right"); ax.set_yticks(range(len(params)), params)
    for i in range(len(params)):
        for j in range(len(resp)):
            ax.text(j, i, f"{m[i, j]:.2f}", ha="center", va="center", fontsize=8, color="w" if m[i, j] > 0.5 else "k")
    ax.set_title(f"Sobol {t} indices")
fig.colorbar(im, ax=axes, shrink=0.8)
fig.savefig(HERE / "sobol.png", dpi=150, bbox_inches="tight"); print("ok")
