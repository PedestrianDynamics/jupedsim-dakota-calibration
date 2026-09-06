"""Plots from the Dakota tabular outputs in v2/."""
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
V2 = HERE.parent

# --- 1. Sobol indices + sample cloud ---------------------------------------
sob = np.loadtxt(V2 / "sobol/sobol_samples.dat", skiprows=1, usecols=(2, 3, 4, 5))
names = ["desired_speed", "door_width", "sim_seed"]
main = [0.0388, 0.9233, -0.0122]
total = [0.0801, 0.9537, 0.0094]

fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
x = np.arange(3)
ax[0].bar(x - 0.18, main, 0.36, label="main")
ax[0].bar(x + 0.18, total, 0.36, label="total")
ax[0].set_xticks(x, names)
ax[0].set_ylabel("Sobol index")
ax[0].set_title("Sensitivity of evacuation time (500 runs)")
ax[0].axhline(0, color="k", lw=0.5)
ax[0].legend()
sc = ax[1].scatter(sob[:, 1], sob[:, 3], c=sob[:, 0], cmap="viridis", s=12)
ax[1].set_xlabel("door width [m]")
ax[1].set_ylabel("evacuation time [s]")
ax[1].set_title("LHS samples")
fig.colorbar(sc, ax=ax[1], label="desired speed [m/s]")
fig.tight_layout()
fig.savefig(HERE / "sobol.png", dpi=150)

# --- 2. misfit maps + EGO path --------------------------------------------
g = np.loadtxt(V2 / "grid/grid.dat", skiprows=1, usecols=range(2, 10))
v, r = np.unique(g[:, 0]), np.unique(g[:, 1])
w = np.array([0.86] * 3 + [400] * 3)


def norm(cols, wts):
    return np.sqrt((g[:, cols] ** 2 * wts).sum(1)).reshape(len(r), len(v))


maps = [
    ("evacuation time only", norm(slice(2, 5), 0.86)),
    ("door flow only", norm(slice(5, 8), 400)),
    ("both, weighted", norm(slice(2, 8), w)),
]
ego = np.loadtxt(V2 / "calib_ego/calib_history.dat", skiprows=1, usecols=(2, 3))

fig, axes = plt.subplots(1, 3, figsize=(14, 4.4), sharey=True)
for ax, (title, m) in zip(axes, maps):
    cf = ax.contourf(v, r, m, levels=20, cmap="magma_r")
    ax.contour(v, r, m, levels=[2, 4, 8], colors="w", linewidths=0.6)
    ax.plot(1.15, 0.17, "c*", ms=14, label="truth")
    ax.set_xlabel("desired speed [m/s]")
    ax.set_title(f"weighted residual norm: {title}")
    fig.colorbar(cf, ax=ax, shrink=0.85)
axes[0].set_ylabel("agent radius [m]")
axes[2].plot(ego[:, 0], ego[:, 1], "w.-", lw=0.7, ms=5, alpha=0.7, label="EGO evaluations")
axes[2].plot(1.26, 0.176, "go", ms=9, mfc="none", mew=2, label="EGO best")
axes[2].legend(loc="lower left", fontsize=8)
fig.tight_layout()
fig.savefig(HERE / "misfit.png", dpi=150)
print("wrote", HERE / "sobol.png", HERE / "misfit.png")
