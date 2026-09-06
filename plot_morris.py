"""Morris screening: mean |elementary effect| per parameter and observable,
computed from the sample table on trajectory pairs where no run failed."""
import pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = pathlib.Path(__file__).parent
import sys
SRC = sys.argv[1] if len(sys.argv) > 1 else "morris"
d = np.loadtxt(HERE / SRC / "morris_samples.dat", skiprows=1, usecols=range(2, 18))
names = ["desired_speed", "radius", "time_gap", "strength_neighbor", "range_neighbor", "strength_geometry", "range_geometry"]
resp = ["flow_2.4", "density_2.4", "speed_2.4", "flow_3.6", "density_3.6", "speed_3.6", "flow_5.0", "density_5.0", "speed_5.0"]
X, Y = d[:, :7], d[:, 7:]
rng = np.ptp(X, 0)
ee = np.full((7, 9), np.nan); cnt = np.zeros(7, int)
acc = [[[] for _ in resp] for _ in names]
for a in range(len(X) - 1):
    b = a + 1
    if b % 8 == 0 or (Y[a, [0, 3, 6]] == 0).any() or (Y[b, [0, 3, 6]] == 0).any():
        continue
    dx = X[b] - X[a]; i = int(np.argmax(np.abs(dx)))
    for j in range(9):
        acc[i][j].append(abs(Y[b, j] - Y[a, j]) / abs(dx[i] / rng[i]))
for i in range(7):
    cnt[i] = len(acc[i][0])
    for j in range(9):
        ee[i, j] = np.mean(acc[i][j])
# normalise per observable so columns are comparable
mu = ee / ee.max(0)
fig, ax = plt.subplots(figsize=(9, 4.4))
im = ax.imshow(mu, cmap="Oranges", vmin=0, vmax=1, aspect="auto")
ax.set_xticks(range(9), resp, rotation=45, ha="right")
ax.set_yticks(range(7), [f"{n}  (n={c})" for n, c in zip(names, cnt)])
for i in range(7):
    for j in range(9):
        ax.text(j, i, f"{mu[i, j]:.2f}", ha="center", va="center", fontsize=8, color="w" if mu[i, j] > 0.6 else "k")
ax.set_title("Morris screening: mean |elementary effect|, scaled to the strongest parameter per observable")
fig.colorbar(im, ax=ax, shrink=0.8)
fig.savefig(HERE / "morris.png", dpi=150, bbox_inches="tight"); print("ok")
