"""Distance-based state variable for the space-awareness test.

Every agent carries a state s in [0, 1] that depends on its distance d to the
gate line: s = 1 / (1 + exp((d - d_switch) / w_switch)), so s -> 1 at the gate
and s -> 0 far upstream, with the transition centred at d_switch and w_switch
wide. Each per-agent parameter p of the Collision Free Speed model V2 with a
factor f_p in the parameter file is blended between its open-space value and a
constriction value:

    p_i = p * (1 + s_i * (f_p - 1))

Factors that are absent stay at 1, so that parameter is shared. The gate line
is a horizontal segment given per scenario; both scenarios flow in -y, and an
agent at or past the line keeps s = 1 until it leaves, so the parameters do
not revert inside the passage. Agents are updated every UPDATE_EVERY
iterations. JuPedSim checks its parameter limits only when an agent is added,
not when a value is changed at runtime, so the blend clamps to those limits.
"""
import numpy as np

SWITCH = ["d_switch", "w_switch"]
# factor name -> (scenario keyword, JuPedSim V2 agent state attribute)
FACTORS = {
    "f_radius": ("radius", "radius"),
    "f_time_gap": ("time_gap", "time_gap"),
    "f_strength_neighbor": ("strength_neighbor", "strength_neighbor_repulsion"),
    "f_range_neighbor": ("range_neighbor", "range_neighbor_repulsion"),
    "f_strength_geometry": ("strength_geometry", "strength_geometry_repulsion"),
    "f_range_geometry": ("range_geometry", "range_geometry_repulsion"),
}
PARAMS = SWITCH + list(FACTORS)
# JuPedSim 1.4.2 model constraints (checked at add_agent only): radius (0, 2], time gap [0.1, 10]
LIMITS = {"radius": (1e-3, 2.0), "time_gap": (0.1, 10.0)}
UPDATE_EVERY = 10  # iterations between state updates (0.1 s at dt = 0.01)


def from_params(p):
    """Return the rule parameters found in a Dakota parameter dict, or None
    when the switch parameters or every factor are missing."""
    factors = {k: float(p[k]) for k in FACTORS if k in p}
    if not all(k in p for k in SWITCH) or not factors:
        return None
    return {**{k: float(p[k]) for k in SWITCH}, **factors}


def state(d, rule):
    z = np.clip((np.asarray(d, float) - rule["d_switch"]) / rule["w_switch"], -50, 50)
    return 1.0 / (1.0 + np.exp(z))


def distance_to_segment(x, y, x1, x2, y0):
    """Distance from (x, y) to the horizontal segment [x1, x2] at height y0,
    zero for points at or past the line in the flow direction (y <= y0)."""
    dx = np.maximum(np.maximum(x1 - x, 0.0), x - x2)
    return np.where(y <= y0, 0.0, np.hypot(dx, y - y0))


class Rule:
    """Applies the blend to every agent of a running simulation."""

    def __init__(self, rule, gate, base):
        self.rule = rule
        self.x1, self.x2, self.y0 = gate
        # (attribute, open-space value, factor) for every parameter with a factor
        self.blend = [(attr, float(base[kw]), rule[f], LIMITS.get(attr, (-np.inf, np.inf)))
                      for f, (kw, attr) in FACTORS.items() if f in rule]

    def apply(self, sim):
        if sim.iteration_count() % UPDATE_EVERY:
            return
        agents = list(sim.agents())
        if not agents:
            return
        pos = np.array([a.position for a in agents])
        s = state(distance_to_segment(pos[:, 0], pos[:, 1], self.x1, self.x2, self.y0), self.rule)
        for attr, value, factor, (lo, hi) in self.blend:
            for a, v in zip(agents, np.clip(value * (1.0 + s * (factor - 1.0)), lo, hi)):
                setattr(a.model, attr, float(v))


def make(rule, gate, base):
    """Callable(sim) for the scenario loop, or None when no rule is given.
    `base` maps scenario keywords (radius, time_gap, ...) to open-space values."""
    if rule is None:
        return None
    return Rule(rule, gate, base).apply
