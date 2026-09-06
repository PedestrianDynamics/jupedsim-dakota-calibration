"""Plot the speed/time-gap and spacing motivation profiles."""
import json
import pathlib

import matplotlib.pyplot as plt
import numpy as np


def load(motivation):
    return json.load(open(pathlib.Path("results") / f"motivation_profile_{motivation}.json"))


profiles = [load("h0"), load("hminus")]
spacing = json.load(open(pathlib.Path("results") / "motivation_profile_spacing_hminus.json"))
values = [np.array([point["norm"] for point in profile["grid"]]).reshape((7, 7))
          for profile in profiles]
spacing_values = np.array([point["norm"] for point in spacing["grid"]]).reshape((7, 7))
fig, axes = plt.subplots(1, 3, figsize=(11.2, 3.6), constrained_layout=True)
for ax, profile, matrix in zip(axes[:2], profiles, values):
    image = ax.imshow(matrix, origin="lower", aspect="auto", cmap="viridis",
                      extent=[profile["time_gap_grid"][0], profile["time_gap_grid"][-1],
                              profile["v0_grid"][0], profile["v0_grid"][-1]],
                      vmin=7, vmax=30)
    best = profile["best"]
    ax.plot(best["time_gap"], best["desired_speed"], "o", ms=6, mfc="none",
            mec="white", mew=1.5)
    ax.plot(0.833, 1.55, "x", ms=6, color="white", mew=1.5)
    ax.set_title("$h^0$" if profile["motivation"] == "h0" else "$h^-$")
    ax.set_xlabel("time gap $T$ [s]")
axes[0].set_ylabel("desired speed $v_0$ [m/s]")
best = spacing["best"]
axes[2].imshow(spacing_values, origin="lower", aspect="auto", cmap="viridis",
               extent=[spacing["range_neighbor_grid"][0],
                       spacing["range_neighbor_grid"][-1],
                       spacing["radius_grid"][0], spacing["radius_grid"][-1]],
               vmin=7, vmax=30)
axes[2].plot(best["range_neighbor"], best["radius"], "o", ms=6, mfc="none",
             mec="white", mew=1.5)
axes[2].plot(0.09, 0.144, "x", ms=6, color="white", mew=1.5)
axes[2].set_title("$h^-$: spacing")
axes[2].set_xlabel("neighbor range [m]")
axes[2].set_ylabel("radius [m]")
fig.colorbar(image, ax=axes, label="normalized residual norm (clipped at 30)")
fig.savefig("motivation_profile.png", dpi=220)
