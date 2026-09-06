"""Compare front-area occupancy for paired h0 and h- runs at 1.2 m.

The simulations include the common CrowdQueue set C and the condition-specific
v0/T profile points, while replaying each run's observed initial positions and
arrivals. The comparison is therefore conditional on those inputs; it tests
whether the model preserves or erases the observed positioning difference, not
whether it generates it.
"""
import json
import pathlib
from concurrent.futures import ProcessPoolExecutor

import numpy as np

import observables_cq as obs
from parameter_io import best_parameters
import scenario_cq


RUNS = ["090_c_12_h0", "100_c_12_h-", "110_c_12_h0", "120_c_12_h-"]
PARAMETERS = ["radius", "time_gap", "strength_neighbor", "range_neighbor",
              "strength_geometry", "range_geometry"]


def condition_parameters():
    values = best_parameters("calib_h0_s9/dakota.out")
    static = {name: values[name] for name in PARAMETERS}
    result = {"set_c": {"desired_speed": 1.55, **static}}
    for condition, directory in (("h0", "motivation_profile_h0"),
                                 ("h-", "motivation_profile_hminus")):
        profile = best_parameters(pathlib.Path(directory) / "dakota.out")
        result[condition] = {
            "desired_speed": profile["desired_speed"],
            "time_gap": profile["time_gap"],
            **{name: value for name, value in static.items() if name != "time_gap"},
        }
    return result


def experiment_record(run_name):
    run = obs.runs()[run_name]
    trajectory = obs.load_experiment(run["file"])
    measured = obs.compute(trajectory, run["width"])
    time, count = obs.front_occupancy(trajectory, run["width"])
    active = (time >= measured["window"][0]) & (time <= measured["window"][1])
    return {
        "time": time.tolist(),
        "count": count.tolist(),
        "window": list(measured["window"]),
        "mean_count_in_window": float(np.mean(count[active])),
        "n_total": measured["n_total"],
    }


def simulate(job):
    run_name, seed, output, fit, parameters = job
    dropped = scenario_cq.run(run_name, seed, output, **parameters)
    trajectory = obs.load_simulation(output)
    measured = obs.compute(trajectory, obs.runs()[run_name]["width"])
    time, count = obs.front_occupancy(trajectory, obs.runs()[run_name]["width"])
    active = (time >= measured["window"][0]) & (time <= measured["window"][1])
    return {
        "run": run_name,
        "seed": seed,
        "fit": fit,
        "time": time.tolist(),
        "count": count.tolist(),
        "window": list(measured["window"]),
        "mean_count_in_window": float(np.mean(count[active])),
        "status": "emptied" if measured["emptied"] and dropped == 0 else "incomplete",
    }


if __name__ == "__main__":
    output_dir = pathlib.Path("results")
    parameters = condition_parameters()
    jobs = []
    for run in RUNS:
        condition = obs.runs()[run]["motivation"]
        for fit, selected in (("set_c", parameters["set_c"]),
                              ("profile", parameters[condition])):
            jobs.extend((run, seed,
                         str(output_dir / f"front_{fit}_{run}_s{seed}.sqlite"),
                         fit, selected) for seed in (1, 2, 3))
    with ProcessPoolExecutor(6) as executor:
        simulations = list(executor.map(simulate, jobs))
    result = {
        "parameters": parameters,
        "conditioning": "observed initial positions and arrivals replayed per run",
        "experiment": {run: experiment_record(run) for run in RUNS},
        "simulation": simulations,
    }
    with open(output_dir / "front_occupancy.json", "w") as output:
        json.dump(result, output, indent=1)
    for _, _, filename, _, _ in jobs:
        pathlib.Path(filename).unlink(missing_ok=True)
    print("wrote results/front_occupancy.json")
