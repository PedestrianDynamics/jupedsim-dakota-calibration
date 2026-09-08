# Experiment data (not included; download from the Jülich Pedestrian Dynamics Data Archive)

| experiment | archive page | file to unpack here |
|---|---|---|
| Hermes bottleneck 2009 (doi:10.34735/ped.2009.6) | https://ped.fz-juelich.de/db/doku.php?id=hermes_bottleneck | `2009bottleneck_trajectories_hdf5.zip` → `data/ao-*-400.h5` |
| CrowdQueue 2018 (doi:10.34735/ped.2018.1) | https://ped.fz-juelich.de/db/doku.php?id=crowdqueue | `trajectories_hdf5.zip` → `data/crowdqueue/*.h5` and `2018crowdqueue.json` → `data/crowdqueue/meta.json` |
| BaSiGo entrance semicircle 2013 (doi:10.34735/ped.2013.2) | https://ped.fz-juelich.de/da/doku.php?id=entrance_semicircle | `2013entrance_semicircle_trajectories_h5.zip` → `data/semicircle/entrance_1.h5` |

`corrected_geometry.md` gives a corrected walkable-area polygon per Hermes run
(the archive polygon is a camera-window box with the walls cut off). Use the
Hermes files as published from 2026-09-08 on: the earlier files carried gap
widths 0.1 m narrower than `b_Exit` for three runs, see `hermes/geometry_check.md`.
