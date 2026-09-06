"""Plot the two-parameter motivation profiles produced by profile_motivation.py."""
import json
import pathlib

import matplotlib.pyplot as plt
import numpy as np


def load(motivation):
    return json.load(open(pathlib.Path("results") / f"motivation_profile_{motivation}.json"))


profiles = [load("h0"), load("hminus")]
values = np.array([[p["grid"][i]["norm"] for i in range(49)] for p in profiles])
vmin, vmax = values.min(), values.max()
fig, axes = plt.subplots(1, 2, figsize=(8.0, 3.6), sharex=True, sharey=True,
                         constrained_layout=True)
for ax, profile, z in zip(axes, profiles, values):
    matrix = z.reshape((7, 7))
    image = ax.imshow(matrix, origin="lower", aspect="auto", cmap="viridis",
                      extent=[profile["time_gap_grid"][0], profile["time_gap_grid"][-1],
                              profile["v0_grid"][0], profile["v0_grid"][-1],],
                      vmin=vmin, vmax=vmax)
    best = profile["best"]
    ax.plot(best["time_gap"], best["desired_speed"], "o", ms=6, mfc="none",
            mec="white", mew=1.5)
    ax.plot(0.833, 1.55, "x", ms=6, color="white", mew=1.5)
    ax.set_title("$h^0$" if profile["motivation"] == "h0" else "$h^-$")
    ax.set_xlabel("time gap $T$ [s]")
axes[0].set_ylabel("desired speed $v_0$ [m/s]")
fig.colorbar(image, ax=axes, label="normalized residual norm")
fig.savefig("motivation_profile.png", dpi=220)
