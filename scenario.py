"""JuPedSim replica of the Hermes 2009 bottleneck.

Outer area 12 x 18 m (x in [-6, 6], y in [-8, 10]); a 1 m thick wall band at
|y| < 0.5 with a gap of width b centred at x = 0.9. Assumption: the wall band
spans the full width (the archive WKT leaves the ends at |x| > 4.5 open, which
lies outside the camera window and cannot be checked).
"""
import pathlib

import jupedsim as jps
import numpy as np
import shapely

GAP_CENTER = 0.9
N_AGENTS = 350
DT = 0.01
MAX_ITER = 30_000


def geometry(gap_width):
    outer = shapely.box(-6, -8, 6, 14)  # y extended beyond the archive box so 350 agents fit for any radius
    wall = shapely.box(-6, -0.5, 6, 0.5)
    gap = shapely.box(GAP_CENTER - gap_width / 2, -0.5, GAP_CENTER + gap_width / 2, 0.5)
    return outer.difference(wall).union(gap)


def waiting_positions(seed, radius):
    """Hexagonal lattice filled row by row from the wall, plus jitter.
    Spacing 0.5 m (~4.6 /m2) or wider if the radius demands it, so that no two
    agents overlap at insertion (JuPedSim requires distance >= 2 radius)."""
    rng = np.random.default_rng(seed)
    spacing = max(0.5, 2 * radius + 0.1)
    jitter = (spacing - 2 * radius - 0.01) / (2 * np.sqrt(2))
    pts = []
    y = 1.0
    row = 0
    while len(pts) < N_AGENTS:
        x0 = -5.5 + (spacing / 2 if row % 2 else 0)
        for x in np.arange(x0, 5.5, spacing):
            pts.append((x, y))
        y += spacing * np.sqrt(3) / 2
        row += 1
    pts = np.array(pts[:N_AGENTS]) + rng.uniform(-jitter, jitter, (N_AGENTS, 2))
    return [tuple(p) for p in pts]


def run(gap_width, seed, out_file, desired_speed=1.2, radius=0.2, time_gap=1.0,
        strength_neighbor=8.0, range_neighbor=0.1, strength_geometry=5.0, range_geometry=0.02):
    sim = jps.Simulation(
        model=jps.CollisionFreeSpeedModel(
            strength_neighbor_repulsion=strength_neighbor,
            range_neighbor_repulsion=range_neighbor,
            strength_geometry_repulsion=strength_geometry,
            range_geometry_repulsion=range_geometry,
        ),
        geometry=geometry(gap_width),
        dt=DT,
        trajectory_writer=jps.SqliteTrajectoryWriter(output_file=pathlib.Path(out_file), every_nth_frame=6),
    )
    exit_id = sim.add_exit_stage(shapely.box(-6, -8, 6, -7))
    journey_id = sim.add_journey(jps.JourneyDescription([exit_id]))
    for pos in waiting_positions(seed, radius):
        sim.add_agent(jps.CollisionFreeSpeedModelAgentParameters(
            journey_id=journey_id, stage_id=exit_id, position=pos,
            desired_speed=desired_speed, radius=radius, time_gap=time_gap))
    while sim.agent_count() > 0 and sim.iteration_count() < MAX_ITER:
        sim.iterate()
    return sim.elapsed_time()
