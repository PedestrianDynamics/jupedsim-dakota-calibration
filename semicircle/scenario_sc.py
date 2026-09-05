"""BaSiGo 2013 entrance without guiding barriers ("semicircle"): geometry from the
archive WKT; agents are injected at the time and position where they first appear
in the experiment (boundary-condition replay), so the inflow matches the run."""
import pathlib
import h5py
import jupedsim as jps
import numpy as np
import shapely
import shapely.ops

DATA = pathlib.Path(__file__).resolve().parent.parent / "data" / "semicircle" / "entrance_1.h5"
FPS = 25.0
DT = 0.01
T_END = 120.0  # experiment aborted at ~118 s


def arrivals():
    d = h5py.File(DATA)["trajectory"][:]
    out = []
    for i in np.unique(d["id"]):
        r = d[d["id"] == i]; k = np.argmin(r["frame"])
        out.append((r["frame"][k] / FPS, float(r["x"][k]), float(r["y"][k])))
    return sorted(out)


def geometry():
    geo = shapely.from_wkt(h5py.File(DATA).attrs["wkt_geometry"])
    # close the untracked far-left side (x < -2.5) where no barrier is recorded
    return geo.difference(shapely.box(-6, -2, -2.5, -0.05))


def run(seed, out_file, desired_speed=1.55, radius=0.13, time_gap=0.8, strength_neighbor=2.0,
        range_neighbor=0.25, strength_geometry=5.0, range_geometry=0.02):
    rng = np.random.default_rng(seed)
    geo = geometry()
    region = geo.buffer(-(radius + 0.03))
    sim = jps.Simulation(
        model=jps.CollisionFreeSpeedModel(strength_neighbor_repulsion=strength_neighbor, range_neighbor_repulsion=range_neighbor,
                                          strength_geometry_repulsion=strength_geometry, range_geometry_repulsion=range_geometry),
        geometry=geo, dt=DT, trajectory_writer=jps.SqliteTrajectoryWriter(output_file=pathlib.Path(out_file), every_nth_frame=4))
    exit_id = sim.add_exit_stage(shapely.box(-2.4, -2.0, 6.0, -1.7))
    journey = sim.add_journey(jps.JourneyDescription([exit_id]))
    pending = arrivals()
    placed = []

    def free(x, y):
        return region.contains(shapely.Point(x, y)) and all(np.hypot(x - px, y - py) > 2 * radius + 0.02 for px, py in placed)

    def try_add(x, y):
        for _ in range(20):
            if free(x, y):
                sim.add_agent(jps.CollisionFreeSpeedModelAgentParameters(journey_id=journey, stage_id=exit_id, position=(x, y),
                              desired_speed=desired_speed, radius=radius, time_gap=time_gap))
                placed.append((x, y)); return True
            x, y = x + rng.normal(0, 0.15), y + rng.normal(0, 0.15)
        return False

    while sim.elapsed_time() < T_END:
        t = sim.elapsed_time()
        # positions of live agents for the overlap test
        placed = [tuple(a.position) for a in sim.agents()]
        still = []
        for (ta, x, y) in pending:
            if ta <= t:
                if not try_add(x, y):
                    still.append((ta, x, y))
            else:
                still.append((ta, x, y))
        pending = still
        sim.iterate(10)
    return len(pending)
