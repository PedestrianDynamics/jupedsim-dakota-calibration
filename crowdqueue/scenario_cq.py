"""JuPedSim replica of a CrowdQueue run: geometry from the archive WKT,
agents start at the measured first-frame positions (pushed apart where the
tracking put two people closer than two radii)."""
import pathlib

import jupedsim as jps
import numpy as np
import shapely
import shapely.ops

import observables_cq as obs

DT = 0.01
MAX_ITER = 12_000  # 120 s: the longest experiment run is 67 s; a run that has not emptied by then is deadlocked


def repair_positions(pts, min_dist, region, rng, iters=2000):
    """Push overlapping points apart until all pairs are >= min_dist, keeping
    every point inside `region` (the walkable area eroded by the radius)."""
    p = np.array(pts, float) + rng.uniform(-0.01, 0.01, (len(pts), 2))

    def clamp(q):
        for i, (x, y) in enumerate(q):
            if not region.contains(shapely.Point(x, y)):
                q[i] = shapely.ops.nearest_points(region, shapely.Point(x, y))[0].coords[0]
        return q

    p = clamp(p)
    for _ in range(iters):
        d = p[:, None, :] - p[None, :, :]
        dist = np.hypot(d[..., 0], d[..., 1]) + np.eye(len(p)) * 10
        close = dist < min_dist
        if not close.any():
            return p
        push = np.where(close[..., None], d / dist[..., None] * (min_dist - dist)[..., None] * 0.6, 0).sum(1)
        p = clamp(p + push + rng.uniform(-0.002, 0.002, p.shape))
    raise RuntimeError("could not separate initial positions")


def run(run_name, seed, out_file, desired_speed=1.2, radius=0.2, time_gap=1.0,
        strength_neighbor=8.0, range_neighbor=0.1, strength_geometry=5.0, range_geometry=0.02):
    r = obs.runs()[run_name]
    geo = shapely.from_wkt(obs.geometry_wkt(r["file"]))
    sim = jps.Simulation(
        model=jps.CollisionFreeSpeedModel(
            strength_neighbor_repulsion=strength_neighbor, range_neighbor_repulsion=range_neighbor,
            strength_geometry_repulsion=strength_geometry, range_geometry_repulsion=range_geometry),
        geometry=geo, dt=DT,
        trajectory_writer=jps.SqliteTrajectoryWriter(output_file=pathlib.Path(out_file), every_nth_frame=4),
    )
    exit_id = sim.add_exit_stage(shapely.box(-7.5, -3.9, 7.5, -3.0))
    journey_id = sim.add_journey(jps.JourneyDescription([exit_id]))
    rng = np.random.default_rng(seed)
    region = geo.buffer(-(radius + 0.03))
    pts = repair_positions(list(obs.initial_positions(r["file"]).values()), 2 * radius + 0.02, region, rng)
    for x, y in pts:
        sim.add_agent(jps.CollisionFreeSpeedModelAgentParameters(
            journey_id=journey_id, stage_id=exit_id, position=(x, y),
            desired_speed=desired_speed, radius=radius, time_gap=time_gap))
    while sim.agent_count() > 0 and sim.iteration_count() < MAX_ITER:
        sim.iterate()
    return sim.elapsed_time()
