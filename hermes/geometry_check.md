# Hermes 2009 archive geometry vs. nominal bottleneck width

Script: `hermes/geometry_check.py` (reads `data/ao-*-400.h5`, writes
`results/geometry_check.json` and `figures/geometry_check_*.png`).

## Question

The archive HDF5 files carry a `wkt_geometry` polygon per run and a parameter
`b_Exit` (the nominal bottleneck width). Do the two agree, and which one do the
trajectories support?

## What the archive polygons say

Each polygon is a 12 m x 18 m camera box with two rectangular holes for the
boards. The gap between the holes is the bottleneck:

| run | b_Exit [m] | archive gap [m] | archive edges (x) | archive centre | boards extent (x) |
|---|---|---|---|---|---|
| ao-240-400 | 2.4 | **2.30** | -0.25 / 2.05 | 0.90 | -3.05 / 4.45 |
| ao-300-400 | 3.0 | **2.90** | -0.55 / 2.35 | 0.90 | -3.05 / 4.45 |
| ao-360-400 | 3.6 | 3.60 | -0.90 / 2.70 | 0.90 | -3.00 / 4.50 |
| ao-440-400 | 4.4 | 4.40 | -1.30 / 3.10 | 0.90 | -3.00 / 4.50 |
| ao-500-400 | 5.0 | **4.90** | -1.50 / 3.40 | **0.95** | -3.00 / 4.50 |

Three of the five polygons are 0.1 m narrower than `b_Exit`. For 2.4 and 3.0
both edges are moved inward by 0.05 m (the outer board ends are moved by the same
0.05 m, so the whole board pair was shifted, not just resized). For 5.0 only the
left edge is moved, by 0.1 m, which also puts the gap centre at 0.95 instead
of 0.9. The 3.6 and 4.4 polygons match `b_Exit` exactly.

## What the trajectories say

Head positions inside the board band (|y| < 0.5) give an envelope per run.
"Clearance" is the distance from the outermost head to the wall; the physical
minimum for a head marker is on the order of one shoulder half-width, so a
clearance of a few centimetres means the wall is placed too far in.

| run | head x-range | envelope width | clearance to archive walls (L / R) | clearance to nominal edges (L / R) |
|---|---|---|---|---|
| ao-240-400 | -0.22 / 2.04 | 2.25 | **0.03 / 0.015** | 0.08 / 0.065 |
| ao-300-400 | -0.51 / 2.30 | 2.81 | **0.04 / 0.05** | 0.09 / 0.10 |
| ao-360-400 | -0.83 / 2.59 | 3.42 | 0.07 / 0.11 | 0.07 / 0.11 |
| ao-440-400 | -1.16 / 2.97 | 4.13 | 0.14 / 0.13 | 0.14 / 0.13 |
| ao-500-400 | -1.47 / 3.31 | 4.78 | **0.03** / 0.10 | 0.13 / 0.10 |

With the 0.5 / 99.5 percentiles instead of the extremes the picture is the
same: archive-wall clearances of 8-10 cm on the disputed edges versus 12-18 cm
on the undisputed ones, while the nominal edges give 12-20 cm everywhere.

Reading:

- On the two runs where archive and nominal agree (3.6, 4.4) heads stay
  7-14 cm from the walls.
- On the three disputed runs the archive walls would have heads passing 1.5-5 cm
  from a board. The nominal edges restore the 7-13 cm clearance seen elsewhere.
- The head-envelope width grows linearly with `b_Exit` (`geometry_check_widths.png`)
  with a roughly constant offset of about 0.2-0.3 m, again with no kink at the three
  disputed widths.
- The 5.0 run centre from the trajectories is 0.92, closer to the nominal 0.9
  than to the archive 0.95, but this is a weak signal.

So the trajectories favour the nominal `b_Exit` values and the gap centre at
x = 0.9. The archive polygons for 2.4, 3.0 and 5.0 look like a transcription
error of 0.05-0.1 m, not a real difference in the setup. Tracking noise of a few
centimetres cannot be excluded, so this is consistency evidence, not proof.

## Consequences for the study

- `data/corrected_geometry.md` and `hermes/scenario.py` already use the nominal
  widths centred at 0.9. Nothing needs to change there.
- `hermes/observables.py` builds the counting line from the nominal width. The
  line is inside the gap either way, so the flow counts are not affected.
- If the archive polygons were right after all, the simulated widths would be
  too large by 4 % (2.4), 3 % (3.0) and 2 % (5.0). The flow scales roughly with
  width, so this would be a bias of the same size, below the 10 % sigma used in
  the calibration and smaller than the seed scatter.
- The archive `wkt_geometry` should not be used as the walkable area for these
  three runs (PedPy plots, measurement areas touching the walls, or any
  wall-distance observable).

## Figures

- `figures/geometry_check_occupancy.png`: 2D occupancy around the bottleneck with
  archive boards (grey) with the x coordinates of their inner edges, and nominal
  edges (red dashed).
- `figures/geometry_check_xhist.png`: x histogram of head positions inside the
  board band with both wall positions.
- `figures/geometry_check_envelope.png`: min/max x per 0.25 m y-slice; the
  narrowing coincides with the band |y| < 0.5 in all runs.
- `figures/geometry_check_widths.png`: nominal vs archive gap width.
