"""Compare CrowdQueue speed magnitude with gate-directed components.

The speed calculation deliberately mirrors :func:`observables_cq.compute`:
PedPy frame_step=5 and BORDER_SINGLE_SIDED are used, and only occupied frames
inside the 10--90 percent flow-crossing window are averaged.
"""
import argparse
import json
import pathlib
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pedpy  # noqa: E402
import shapely  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import driver_cq  # noqa: E402
import observables_cq as obs  # noqa: E402
from parameter_io import best_parameters  # noqa: E402


FRAME_STEP = 5
SPEED_SIGMA = 0.10
SEEDS = (1, 2, 3)
GATE_CENTER = np.array((0.0, -0.15))
STATIC_NAMES = (
    "radius",
    "strength_neighbor",
    "range_neighbor",
    "strength_geometry",
    "range_geometry",
)


def measurement_window(traj, width):
    """Return the exact frame window and occupied-frame mask used by compute."""
    line = pedpy.MeasurementLine([(-0.25, -0.6), (0.25, -0.6)])
    nt, _ = pedpy.compute_n_t(traj_data=traj, measurement_line=line)
    n = nt["cumulative_pedestrians"].to_numpy()
    n_tot = int(n.max())
    lo, hi = np.searchsorted(n, 0.1 * n_tot), np.searchsorted(n, 0.9 * n_tot)
    f_lo, f_hi = nt.index[lo], nt.index[hi]
    density = pedpy.compute_classic_density(
        traj_data=traj, measurement_area=obs.area(width)
    )
    density_window = density.loc[f_lo:f_hi, "density"]
    return f_lo, f_hi, density_window > 0


def directed_observables(traj, width):
    """Compute Cartesian and radial speed observables for one run."""
    baseline = obs.compute(traj, width)
    f_lo, f_hi, occupied = measurement_window(traj, width)

    individual = pedpy.compute_individual_speed(
        traj_data=traj,
        frame_step=FRAME_STEP,
        compute_velocity=True,
        speed_calculation=pedpy.SpeedCalculation.BORDER_SINGLE_SIDED,
    )
    combined = traj.data.merge(individual, on=["id", "frame"])
    inside = shapely.within(combined.point, obs.area(width).polygon)
    position = combined[["x", "y"]].to_numpy()
    to_gate = GATE_CENTER - position
    distance = np.linalg.norm(to_gate, axis=1)
    unit_to_gate = np.divide(
        to_gate,
        distance[:, None],
        out=np.zeros_like(to_gate),
        where=distance[:, None] > 0,
    )
    velocity = combined[["v_x", "v_y"]].to_numpy()
    radial = np.einsum("ij,ij->i", velocity, unit_to_gate)
    tangential = np.sqrt(np.maximum(combined["speed"].to_numpy() ** 2 - radial ** 2, 0.0))
    combined["v_radial"] = radial
    combined["v_tangent"] = tangential
    inside_data = combined.loc[inside]
    means_per_frame = inside_data.groupby("frame")[[
        "speed", "v_y", "v_radial", "v_tangent"
    ]].mean()
    frames = range(traj.data.frame.min(), traj.data.frame.max() + 1)
    means_per_frame = means_per_frame.reindex(frames, fill_value=0.0)
    window = means_per_frame.loc[f_lo:f_hi]
    means = window.loc[occupied].mean() if occupied.any() else window.mean() * 0.0
    magnitude = float(baseline["speed"])
    gate_speed = float(-means["v_y"])
    radial_speed = float(means["v_radial"])
    tangential_speed = float(means["v_tangent"])
    ratio = gate_speed / magnitude if magnitude else 0.0
    radial_ratio = radial_speed / magnitude if magnitude else 0.0
    return {
        "speed": magnitude,
        "v_gate": gate_speed,
        "ratio": ratio,
        "v_radial": radial_speed,
        "v_tangent": tangential_speed,
        "radial_ratio": radial_ratio,
        "window": list(baseline["window"]),
    }


def condition_parameters():
    calibrated = best_parameters(ROOT / "calib_h0_s9" / "dakota.out")
    static = {name: calibrated[name] for name in STATIC_NAMES}
    parameters = {}
    for motivation, directory in (("h0", "motivation_profile_h0"),
                                  ("h-", "motivation_profile_hminus")):
        profile = best_parameters(ROOT / directory / "dakota.out")
        parameters[motivation] = {
            **static,
            "desired_speed": profile["desired_speed"],
            "time_gap": profile["time_gap"],
        }
    return parameters


def experiment_record(run_name):
    run = obs.runs()[run_name]
    measured = directed_observables(obs.load_experiment(run["file"]), run["width"])
    return {
        "run": run_name,
        "width": run["width"],
        "motivation": run["motivation"],
        **measured,
    }


def simulate(job):
    run_name, seed, output, parameters = job
    run = obs.runs()[run_name]
    try:
        standard = driver_cq.one(run_name, seed, output, parameters)
        measured = directed_observables(obs.load_simulation(output), run["width"])
        return {
            "run": run_name,
            "seed": seed,
            "status": standard["status"],
            "dropped": standard["dropped"],
            **measured,
        }
    finally:
        pathlib.Path(output).unlink(missing_ok=True)


def aggregate_simulations(records):
    if not records:
        return None
    output = {
        key: float(np.mean([record[key] for record in records]))
        for key in ("speed", "v_gate", "v_radial", "v_tangent")
    }
    output["ratio"] = output["v_gate"] / output["speed"] if output["speed"] else 0.0
    output["radial_ratio"] = output["v_radial"] / output["speed"] if output["speed"] else 0.0
    output["std"] = {
        key: float(np.std([record[key] for record in records], ddof=1))
        for key in ("speed", "v_gate", "ratio", "v_radial", "v_tangent", "radial_ratio")
    }
    return output


def add_residuals(table, simulations):
    for row in table:
        simulation = simulations.get(row["run"])
        row["sim"] = simulation
        if simulation is None:
            row["resid_mag_sigma"] = None
            row["resid_directed_sigma"] = None
            row["resid_radial_sigma"] = None
            continue
        row["resid_mag_sigma"] = (
            simulation["speed"] - row["speed"]
        ) / (SPEED_SIGMA * row["speed"])
        row["resid_directed_sigma"] = (
            simulation["v_gate"] - row["v_gate"]
        ) / (SPEED_SIGMA * row["v_gate"])
        row["resid_radial_sigma"] = (
            simulation["v_radial"] - row["v_radial"]
        ) / (SPEED_SIGMA * row["v_radial"])


def norm_comparison(table, motivation, filename):
    confirm = json.load(open(ROOT / "results" / filename))
    by_run = {row["run"]: row for row in table if row["motivation"] == motivation}
    missing = sorted(
        run for run in confirm["runs"]
        if run not in by_run or by_run[run]["sim"] is None
    )
    if missing:
        return {"available": False, "missing_runs": missing}
    terms = {"magnitude": [], "directed": [], "radial": []}
    for run_name, record in confirm["runs"].items():
        for key in ("flow", "density"):
            residual = (
                (record["sim"][key] - record["exp"][key])
                / ({"flow": 0.06, "density": 0.10}[key] * record["exp"][key])
            )
            for values in terms.values():
                values.append(residual)
        row = by_run[run_name]
        terms["magnitude"].append(row["resid_mag_sigma"])
        terms["directed"].append(row["resid_directed_sigma"])
        terms["radial"].append(row["resid_radial_sigma"])
    norms = {name: float(np.linalg.norm(values)) for name, values in terms.items()}
    return {"available": True, "n_terms": len(terms["magnitude"]), **norms,
            "radial_change_vs_magnitude": norms["radial"] - norms["magnitude"],
            "radial_percent_change_vs_magnitude":
                100.0 * (norms["radial"] / norms["magnitude"] - 1.0)}


def make_figure(table, path):
    colors = {"h0": "#0072B2", "h-": "#D55E00", "h+": "#000000"}
    markers = {"h0": "o", "h-": "s", "h+": "D"}
    fig, (ax_radial, ax_tangent) = plt.subplots(
        1, 2, figsize=(7.0, 3.0), constrained_layout=True
    )

    for motivation in ("h0", "h-", "h+"):
        rows = [row for row in table if row["motivation"] == motivation]
        if not rows:
            continue
        widths = np.array([row["width"] for row in rows])
        ax_radial.scatter(
            widths,
            [row["radial_ratio"] for row in rows],
            color=colors[motivation],
            marker=markers[motivation],
            label=f"{motivation} experiment",
            s=26,
        )
        ax_tangent.scatter(
            widths,
            [row["v_tangent"] / row["speed"] for row in rows],
            color=colors[motivation],
            marker=markers[motivation],
            label=f"{motivation} experiment",
            s=26,
        )
        sim_rows = [row for row in rows if row["sim"] is not None]
        if sim_rows:
            ax_radial.errorbar(
                [row["width"] for row in sim_rows],
                [row["sim"]["radial_ratio"] for row in sim_rows],
                yerr=[row["sim"]["std"]["radial_ratio"] for row in sim_rows],
                color=colors[motivation],
                marker="^",
                linestyle="none",
                capsize=2,
                label=f"{motivation} simulation",
            )
            ax_tangent.scatter(
                [row["width"] for row in sim_rows],
                [row["sim"]["v_tangent"] / row["sim"]["speed"] for row in sim_rows],
                color=colors[motivation],
                marker="^",
                s=26,
                label=f"{motivation} simulation",
            )

    ax_radial.axhline(1.0, color="#666666", linewidth=0.8)
    ax_radial.set(
        xlabel="Corridor width (m)",
        ylabel="Radial speed / |v|",
        title="Goal-directed fraction",
    )
    ax_radial.set_ylim(bottom=0, top=1.1)
    ax_radial.legend(frameon=False, fontsize=7, ncol=2)
    ax_radial.spines[["top", "right"]].set_visible(False)

    ax_tangent.set(
        xlabel="Corridor width (m)",
        ylabel="|Tangential speed| / |v|",
        title="Non-goal-directed fraction",
    )
    ax_tangent.set_ylim(bottom=0)
    ax_tangent.spines[["top", "right"]].set_visible(False)
    fig.savefig(path, dpi=300)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--paired-only", action="store_true",
                        help="run only the paired 1.2 m and 5.6 m h0/h- simulations")
    args = parser.parse_args()

    runs = obs.runs()
    table = [experiment_record(name) for name in runs]
    parameters = condition_parameters()
    sim_runs = [
        name for name, run in runs.items()
        if run["motivation"] in parameters
        and (not args.paired_only or run["width"] in (1.2, 5.6))
    ]
    jobs = [
        (
            run_name,
            seed,
            str(ROOT / "results" / f"directed_{run_name}_s{seed}.sqlite"),
            parameters[runs[run_name]["motivation"]],
        )
        for run_name in sim_runs
        for seed in SEEDS
    ]
    with ProcessPoolExecutor(args.workers) as executor:
        simulation_records = list(executor.map(simulate, jobs))
    grouped = {}
    for record in simulation_records:
        grouped.setdefault(record["run"], []).append(record)
    simulations = {run: aggregate_simulations(records) for run, records in grouped.items()}
    add_residuals(table, simulations)
    hminus_norm = norm_comparison(
        table, "h-", "dakota_hminus_confirm.json"
    )
    h0_norm = norm_comparison(table, "h0", "dakota_h0_confirm.json")

    output = {
        "convention": {
            "frame_step": FRAME_STEP,
            "frame_step_seconds_at_25_fps": 2 * FRAME_STEP / 25.0,
            "speed_calculation": "BORDER_SINGLE_SIDED",
            "measurement_window": "same 10%-90% crossing window as observables_cq.compute",
            "occupied_frames_only": True,
            "directed_component": "-v_y",
            "gate_center": GATE_CENTER.tolist(),
            "radial_component": "velocity projected onto unit vector from position to (0, -0.15)",
            "tangential_magnitude": "sqrt(max(|v|^2 - v_r^2, 0)) per pedestrian and frame",
        },
        "parameters": parameters,
        "simulation_seeds": list(SEEDS),
        "paired_only": args.paired_only,
        "runs": table,
        "hminus_norm": hminus_norm,
        "h0_norm": h0_norm,
    }
    results_path = ROOT / "results" / "directed_speed.json"
    json.dump(output, open(results_path, "w"), indent=1)
    make_figure(table, ROOT / "directed_speed.png")
    print(f"wrote {results_path} and {ROOT / 'directed_speed.png'}")
    print(json.dumps({"hminus_norm": hminus_norm, "h0_norm": h0_norm}, indent=2))


if __name__ == "__main__":
    main()
