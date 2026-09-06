"""Recompute CrowdQueue experimental observables from the archive trajectories."""
import json
import pathlib

import observables_cq as obs


if __name__ == "__main__":
    result = {}
    for name, run in obs.runs().items():
        measured = obs.compute(obs.load_experiment(run["file"]), run["width"])
        result[name] = {
            "width": run["width"],
            "motivation": run["motivation"],
            "priming": run["priming"],
            "flow": measured["flow"],
            "density": measured["density"],
            "speed": measured["speed"],
            "n_total": measured["n_total"],
        }
    destination = pathlib.Path(__file__).resolve().parent / "exp_observables_cq.json"
    with open(destination, "w") as output:
        json.dump(result, output, indent=1)
    print(f"wrote {destination.name} ({len(result)} runs)")
