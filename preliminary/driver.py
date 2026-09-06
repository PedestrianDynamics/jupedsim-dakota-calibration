#!/usr/bin/env python3
"""Dakota analysis driver: one JuPedSim run per evaluation.

Usage (called by Dakota):  python3 driver.py params.in results.out
Reads sampled parameters, runs a corridor-with-door evacuation,
writes the evacuation time back to Dakota.
"""
import os
import pathlib
import statistics
import sys

import jupedsim as jps
import pedpy
import shapely

N_AGENTS = 50
DT = 0.01
MAX_ITER = 60_000  # 600 s wall-clock cap for a stuck run
N_SEEDS = int(os.environ.get("JPS_N_SEEDS", "1"))  # replicates averaged per evaluation


def read_params(path):
    """Parse Dakota's standard params file: '<value> <tag>' per line."""
    params = {}
    for line in open(path):
        parts = line.split()
        if len(parts) == 2:
            params[parts[1]] = parts[0]
    return params


def build_geometry(door_width):
    """Two 10 m x 10 m rooms joined by a 0.3 m thick wall with a centred door."""
    left = shapely.box(0, 0, 10, 10)
    door = shapely.box(10, 5 - door_width / 2, 10.3, 5 + door_width / 2)
    right = shapely.box(10.3, 0, 20, 10)
    return shapely.union_all([left, door, right])


def run(desired_speed, door_width, seed, out_dir, radius=0.2):
    sim = jps.Simulation(
        model=jps.CollisionFreeSpeedModel(),
        geometry=build_geometry(door_width),
        dt=DT,
        trajectory_writer=jps.SqliteTrajectoryWriter(
            output_file=out_dir / f"trajectory_{seed}.sqlite"
        ),
    )
    exit_id = sim.add_exit_stage(shapely.box(19, 0, 20, 10))
    journey_id = sim.add_journey(jps.JourneyDescription([exit_id]))

    positions = jps.distribute_by_number(
        polygon=shapely.box(1, 1, 8, 9),
        number_of_agents=N_AGENTS,
        distance_to_agents=0.4,
        distance_to_polygon=0.3,
        seed=seed,
    )
    for pos in positions:
        sim.add_agent(
            jps.CollisionFreeSpeedModelAgentParameters(
                journey_id=journey_id,
                stage_id=exit_id,
                position=pos,
                desired_speed=desired_speed,
                radius=radius,
            )
        )

    while sim.agent_count() > 0 and sim.iteration_count() < MAX_ITER:
        sim.iterate()
    return sim.elapsed_time(), door_flow(out_dir / f"trajectory_{seed}.sqlite")


def door_flow(trajectory_file):
    """Mean flow [1/s] through the door: crossings per time between first and last."""
    traj = pedpy.load_trajectory_from_jupedsim_sqlite(trajectory_file)
    line = pedpy.MeasurementLine([(10.15, 0.0), (10.15, 10.0)])
    _, crossings = pedpy.compute_n_t(traj_data=traj, measurement_line=line)
    t_cross = crossings["frame"] / traj.frame_rate
    return (len(t_cross) - 1) / (t_cross.max() - t_cross.min())


def main():
    params_file, results_file = sys.argv[1], sys.argv[2]
    p = read_params(params_file)
    seed0 = int(float(p.get("sim_seed", 1)))
    results = [
        run(
            desired_speed=float(p["desired_speed"]),
            door_width=float(p["door_width"]),
            seed=seed0 + k,
            radius=float(p.get("radius", 0.2)),
            out_dir=pathlib.Path(params_file).resolve().parent,
        )
        for k in range(N_SEEDS)
    ]
    t_evac = statistics.mean(r[0] for r in results)
    flow = statistics.mean(r[1] for r in results)
    with open(results_file, "w") as f:
        f.write(f"{t_evac:.4f} evacuation_time\n")
        f.write(f"{flow:.4f} door_flow\n")


if __name__ == "__main__":
    main()
