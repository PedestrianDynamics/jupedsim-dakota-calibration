"""JuPedSim replica of the Hermes 2009 bottleneck.

Setup after Liao et al. (2014), Validation of FDS+Evac in wide bottlenecks:
20 m wide corridor, bottleneck boards 1 m long (the wall band |y| < 0.5 in the
archive coordinates) with a gap of width b centred at x = 0.9, and a
semicircular holding area of radius 8.618 m directly in front of the
bottleneck holding 350 participants at 3 persons per square metre.
"""
import pathlib
import sys

import jupedsim as jps
import numpy as np
import shapely

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import space_state  # noqa: E402

GAP_CENTER = 0.9
N_AGENTS = 350
HOLDING_RADIUS = 8.618  # semicircle in front of the bottleneck, 3 /m2 with 350 people
DT = 0.01
MAX_ITER = 30_000


def geometry(gap_width):
    outer = shapely.box(-10, -8, 10, 11.5)  # 20 m wide corridor, exit 8 m behind the bottleneck
    wall = shapely.box(-10, -0.5, 10, 0.5)
    gap = shapely.box(GAP_CENTER - gap_width / 2, -0.5, GAP_CENTER + gap_width / 2, 0.5)
    return outer.difference(wall).union(gap)


def waiting_positions(seed, radius):
    """Hexagonal lattice inside the semicircular holding area, plus jitter.
    Spacing 0.62 m gives 3 /m2; the N_AGENTS points closest to the bottleneck
    are kept. No two agents overlap at insertion (distance >= 2 radius)."""
    rng = np.random.default_rng(seed)
    spacing = max(0.62, 2 * radius + 0.1)
    jitter = (spacing - 2 * radius - 0.01) / (2 * np.sqrt(2))
    cx, cy = GAP_CENTER, 0.5 + 0.35  # centre of the semicircle at the bottleneck entrance
    pts = []
    for row, y in enumerate(np.arange(cy, cy + HOLDING_RADIUS + spacing, spacing * np.sqrt(3) / 2)):
        x0 = cx + (spacing / 2 if row % 2 else 0)
        for x in np.arange(x0 - HOLDING_RADIUS - spacing, x0 + HOLDING_RADIUS + spacing, spacing):
            if (x - cx) ** 2 + (y - cy) ** 2 <= HOLDING_RADIUS ** 2 and abs(x) < 9.5:
                pts.append((x, y))
    pts = np.array(pts)
    d = np.hypot(pts[:, 0] - cx, pts[:, 1] - cy)
    pts = pts[np.argsort(d)][:N_AGENTS]
    if len(pts) < N_AGENTS:
        raise RuntimeError(f"holding area holds only {len(pts)} agents at spacing {spacing}")
    pts = pts + rng.uniform(-jitter, jitter, pts.shape)
    return [tuple(p) for p in pts]


def run(gap_width, seed, out_file, desired_speed=1.2, radius=0.2, time_gap=1.0,
        strength_neighbor=8.0, range_neighbor=0.1, strength_geometry=5.0, range_geometry=0.02,
        state_rule=None):
    # distance-based blend of per-agent parameters towards the gap line (space_state.py)
    on_step = space_state.make(state_rule, (GAP_CENTER - gap_width / 2, GAP_CENTER + gap_width / 2, 0.0), locals())
    # the writer buffers 100 frames and only writes them on close()
    writer = jps.SqliteTrajectoryWriter(output_file=pathlib.Path(out_file), every_nth_frame=6)
    sim = jps.Simulation(
        model=jps.CollisionFreeSpeedModelV2(),  # per-agent parameters; identical to V1 when they are uniform
        geometry=geometry(gap_width),
        dt=DT,
        trajectory_writer=writer,
    )
    exit_id = sim.add_exit_stage(shapely.box(-6, -8, 6, -7))
    journey_id = sim.add_journey(jps.JourneyDescription([exit_id]))
    for pos in waiting_positions(seed, radius):
        sim.add_agent(jps.CollisionFreeSpeedModelV2AgentParameters(
            journey_id=journey_id, stage_id=exit_id, position=pos,
            desired_speed=desired_speed, radius=radius, time_gap=time_gap,
            strength_neighbor_repulsion=strength_neighbor, range_neighbor_repulsion=range_neighbor,
            strength_geometry_repulsion=strength_geometry, range_geometry_repulsion=range_geometry))
    try:
        while sim.agent_count() > 0 and sim.iteration_count() < MAX_ITER:
            if on_step:
                on_step(sim)
            sim.iterate()
    finally:
        writer.close()
    return sim.elapsed_time()
