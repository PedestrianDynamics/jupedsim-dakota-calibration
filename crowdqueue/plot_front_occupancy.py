"""Plot experiment and set-C front-area occupancy for paired 1.2 m runs."""
import json

import matplotlib.pyplot as plt


PAIRS = [
    ("24 people", "090_c_12_h0", "100_c_12_h-"),
    ("63 people", "110_c_12_h0", "120_c_12_h-"),
]
COLORS = {"h0": "#0072B2", "h-": "#D55E00"}


data = json.load(open("results/front_occupancy.json"))
fig, axes = plt.subplots(1, 2, figsize=(8.5, 3.5), constrained_layout=True)
for ax, (title, h0_run, hminus_run) in zip(axes, PAIRS):
    duration = 0.0
    for run, condition in ((h0_run, "h0"), (hminus_run, "h-")):
        experiment = data["experiment"][run]
        duration = max(duration, experiment["time"][-1])
        ax.step(experiment["time"], experiment["count"], where="post",
                color=COLORS[condition], lw=2, label=f"experiment {condition}")
        simulations = [record for record in data["simulation"]
                       if record["run"] == run and record["fit"] == "profile"]
        for index, record in enumerate(simulations):
            ax.step(record["time"], record["count"], where="post",
                    color=COLORS[condition], lw=0.9, alpha=0.45, ls="--",
                    label=f"profile fit {condition}, 3 seeds" if index == 0 else None)
    ax.set_title(title)
    ax.set_xlim(0, duration)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("time from first recorded frame [s]")
axes[0].set_ylabel("people in the 2.2 m² front area")
axes[1].legend(fontsize=7, ncol=2)
fig.savefig("front_occupancy.png", dpi=220)
