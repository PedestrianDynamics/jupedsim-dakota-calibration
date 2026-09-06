# Preliminary two-room test case

The synthetic study run before touching any experiment: two 10 m rooms joined by a
door of variable width, 50 agents, evacuation time and door flow as observables,
a hidden "truth" for the measurements. It is where the gradient-based solver
(`calib/`, nl2sol) stalled at its start point and the surrogate-based one
(`calib_ego/`, efficient_global) worked, and where the speed–radius identifiability
valley (`grid/`) first showed. The note refers to it in Step 4. The top-level
`README.md` here is the original description of this toy study.
