# Space-awareness test (draft)

Hypothesis: agents behave differently inside a constriction. Test: keep the
Collision Free Speed model, add a per-agent state s in [0, 1] from the distance
d to the gate line, s = 1 / (1 + exp((d - d_switch) / w_switch)), and blend
per-agent parameters towards a constriction value, p * (1 + s (f_p - 1)) for
every parameter p with a factor f_p in the Dakota parameter file. An agent at
or past the line keeps s = 1 until it leaves. Implementation:
`../space_state.py`, hooked into `hermes/scenario.py` and
`crowdqueue/scenario_cq.py` through the `state_rule` argument; both drivers
pass the rule on when `d_switch`, `w_switch` and at least one factor are in
the parameter file.

Both scenarios now build `CollisionFreeSpeedModelV2`, which carries all six
parameters per agent and lets them be changed at runtime. With uniform
parameters V2 reproduces V1 exactly (Hermes 2.4 m, seed 1: flow, density,
speed and elapsed time identical to four digits; CrowdQueue 090 and 110, two
seeds: identical status and flow), so the published results are unchanged.

Objective: the joint one of `../joint` (30 sigma-normalised residuals), twelve
design variables (six base parameters, two switch parameters, factors on
radius, time gap, neighbour strength and neighbour range; wall repulsion stays
shared). Compare against the static joint set (Hermes norm 6.2, CrowdQueue
norm 13.6) and transfer to BaSiGo and the low-motivation runs without
refitting.

    JPS_N_SEEDS=1 dakota -i dakota.in -o dakota.out

## Search box

JuPedSim 1.4.2 enforces only radius in (0, 2], time gap in [0.1, 10] and
desired speed in [0, 10], and only when an agent is added; the repulsion
parameters are unchecked and runtime changes are unchecked, so
`space_state.py` clamps the blended radius and time gap itself. The Dakota
bounds are the plausible part of that space:

| parameter | bounds | reason |
|---|---|---|
| radius [m] | 0.10 to 0.22 | half a shoulder width is 0.20 to 0.25; the round body needs less, every calibration so far gave 0.10 to 0.15 |
| time gap [s] | 0.30 to 1.50 | headway at capacity flow is 0.5 to 1 s; below 0.3 s the model is a queue of touching discs, calibrated values 0.55 to 1.04 |
| desired speed [m/s] | fixed 1.55 | measured on the Hermes participants |
| neighbour strength | 1 to 10 | default 8; Morris: below 1 the term is inert, above 10 with a long range agents cross walls |
| neighbour range [m] | 0.02 to 0.35 | default 0.10; part 2 spacing slice: from 0.34 m every CrowdQueue run stalls |
| wall strength | 1 to 10 | default 5; weak walls with strong neighbour repulsion abort runs (Morris, part 1) |
| wall range [m] | 0.01 to 0.15 | default 0.02; 0.15 is a third of the 0.5 m gate |
| d_switch [m] | 0.3 to 4 | from one body length to the depth of the Hermes measurement area |
| w_switch [m] | 0.1 to 1.5 | sharp step to a transition spanning the whole approach |
| f_radius | 0.60 to 1.00 | shrink only; 0.6 is the shoulder rotation limit, growth would create overlaps |
| f_time_gap | 0.35 to 1.50 | product with the time-gap lower bound stays above JuPedSim's 0.1 s |
| f_strength_neighbor | 0.2 to 3 | either direction; 3 x 10 is where wall crossings start |
| f_range_neighbor | 0.2 to 1.2 | product with the range upper bound stays below the 0.42 m stall cliff |

## Smoke test, 2026-09-08

Joint static set as base, d_switch 1.5 m, w_switch 0.5 m, one seed. The
driver returns 30 residuals in about 15 s.

| factors near the gate | CrowdQueue 090 / 110, two seeds | joint driver, all runs |
|---|---|---|
| none | all empty | Hermes 6.2, CrowdQueue 13.6 |
| radius 0.85, time gap 0.8 | 090 stalls in both seeds at 21/24 | Hermes 5.6, CrowdQueue 26.6, two stalls |
| radius 0.85 | one stall per run | |
| time gap 0.8 | no stall, flow +3 to +8 % | |
| time gap 0.8, neighbour range 0.7 | no stall, flow +10 to +20 % | Hermes 4.1, CrowdQueue 18.8, all seven empty |

The stall with a smaller radius is a three-agent arch: two agents in the
corners of the gate mouth and one directly in front. A smaller radius near the
gate lets agents nest into the corners. Expect a stall cliff along f_radius
like the spacing slice of part 2; a Morris screening over the twelve
parameters should map it before any calibration. Shortening the time gap and
the neighbour range near the gate keeps every run passable and improves
Hermes, but raises the CrowdQueue flows further above the measurement, so the
first optimizer question is whether any constriction set lowers the gate flow
at all. Distance is the first of three candidate state variables; local
density and a blocked-time indicator are the other two.
