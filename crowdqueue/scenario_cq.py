"""JuPedSim replica of a CrowdQueue run: geometry from the archive WKT,
agents start at the measured first-frame positions (pushed apart where the
tracking put two people closer than two radii)."""
import pathlib
import sys

import jupedsim as jps
import numpy as np
import shapely
import shapely.ops

import observables_cq as obs

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import space_state  # noqa: E402

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
        strength_neighbor=8.0, range_neighbor=0.1, strength_geometry=5.0, range_geometry=0.02,
        state_rule=None):
    r = obs.runs()[run_name]
    # distance-based blend of per-agent parameters towards the gate entry line (space_state.py)
    on_step = space_state.make(state_rule, (-0.25, 0.25, -0.15), locals())
    geo = shapely.from_wkt(obs.geometry_wkt(r["file"]))
    # keep only the corridor and the area behind the gate: the archive polygon is a
    # 16 x 16 m box in which the space beside and above the barriers is walkable, and
    # from there the router finds a way around the barriers to the exit
    half = r["width"] / 2 + 0.15  # cut through the 0.25 m barriers, not along their faces
    clipped = geo.intersection(shapely.box(-half, -4.0, half, 12.0))
    parts = [g for g in getattr(clipped, "geoms", [clipped]) if g.geom_type == "Polygon"]
    geo = max(parts, key=lambda g: g.area)  # the corridor with the gate and the area behind it
    # the writer buffers 100 frames and only writes them on close(); without the
    # close the last seconds of every run are lost
    writer = jps.SqliteTrajectoryWriter(output_file=pathlib.Path(out_file), every_nth_frame=4)
    sim = jps.Simulation(
        model=jps.CollisionFreeSpeedModelV2(),  # per-agent parameters; identical to V1 when they are uniform
        geometry=geo, dt=DT, trajectory_writer=writer,
    )
    # exit only at the outlet of the gate passage, so every agent must pass the gate;
    # a full-width exit lets the router send agents around the outside of the barrier walls
    exit_id = sim.add_exit_stage(shapely.box(-0.6, -2.0, 0.6, -1.4))
    journey_id = sim.add_journey(jps.JourneyDescription([exit_id]))
    rng = np.random.default_rng(seed)
    region = geo.buffer(-(radius + 0.03))
    arr = [(t, x, min(y, 6.5)) for t, x, y in obs.arrivals(r["file"])]  # entrants seen above the corridor end start inside it
    first = [(x, y) for t, x, y in arr if t == 0.0]
    pending = [(t, x, y) for t, x, y in arr if t > 0.0]
    pts = repair_positions(first, 2 * radius + 0.02, region, rng)

    def add(x, y):
        sim.add_agent(jps.CollisionFreeSpeedModelV2AgentParameters(
            journey_id=journey_id, stage_id=exit_id, position=(x, y),
            desired_speed=desired_speed, radius=radius, time_gap=time_gap,
            strength_neighbor_repulsion=strength_neighbor, range_neighbor_repulsion=range_neighbor,
            strength_geometry_repulsion=strength_geometry, range_geometry_repulsion=range_geometry))

    for x, y in pts:
        add(x, y)
    n_dropped = 0
    try:
        while (sim.agent_count() > 0 or pending) and sim.iteration_count() < MAX_ITER:
            if pending and pending[0][0] <= sim.elapsed_time():
                live = [tuple(a.position) for a in sim.agents()]
                still = []
                for t0, x, y in pending:
                    if t0 > sim.elapsed_time():
                        still.append((t0, x, y)); continue
                    placed = False
                    for _ in range(20):  # nudge until the spot is free of walls and agents
                        if region.contains(shapely.Point(x, y)) and all(np.hypot(x - px, y - py) > 2 * radius + 0.02 for px, py in live):
                            add(x, y); live.append((x, y)); placed = True; break
                        x, y = x + rng.normal(0, 0.1), y + rng.normal(0, 0.1)
                    if not placed:
                        if sim.elapsed_time() - t0 > 10.0:  # give up after 10 s of trying
                            n_dropped += 1
                        else:
                            still.append((t0, x, y))
                pending = still
            if on_step:
                on_step(sim)
            sim.iterate(10)
    finally:
        writer.close()
    return n_dropped
