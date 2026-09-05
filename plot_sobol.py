"""Heatmap of total Sobol indices: parameter x observable, parsed from sobol/dakota.out."""
import pathlib, re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = pathlib.Path(__file__).parent
txt = (HERE / "sobol/dakota.out").read_text()
resp, params, main, total = [], [], [], []
for line in txt.splitlines():
    m = re.match(r"\s*(\S+) Sobol' indices:", line)
    if m:
        resp.append(m.group(1)); main.append([]); total.append([]); params = []
        continue
    row = line.split()
    if resp and len(row) == 3 and row[2] not in ("Main", "Total"):
        try:
            main[-1].append(float(row[0])); total[-1].append(float(row[1])); params.append(row[2])
        except ValueError:
            pass
main, total = np.array(main).T, np.array(total).T
fig, axes = plt.subplots(1, 2, figsize=(13, 4.2), sharey=True, gridspec_kw={"wspace": 0.08})
for ax, m, t in zip(axes, (main, total), ("main (first order)", "total")):
    im = ax.imshow(np.clip(m, 0, 1), cmap="Blues", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(resp)), resp, rotation=45, ha="right")
    for i in range(len(params)):
        for j in range(len(resp)):
            ax.text(j, i, f"{m[i, j]:.2f}", ha="center", va="center", fontsize=8, color="w" if m[i, j] > 0.5 else "k")
    ax.set_title(f"Sobol {t} indices")
axes[0].set_yticks(range(len(params)), params)
fig.colorbar(im, ax=axes, shrink=0.8)
fig.savefig(HERE / "sobol.png", dpi=150, bbox_inches="tight"); print("ok")
