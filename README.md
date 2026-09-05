# Calibrating JuPedSim's Collision Free Speed model with Dakota

Code and results for the note [How do you validate a pedestrian model against real data?](https://pedestriandynamics.org/notes/dakota-calibration/) on pedestriandynamics.org.

Requirements: Python 3 with `jupedsim`, `pedpy`, `h5py`, `matplotlib`;
[Dakota](https://github.com/snl-dakota/dakota/releases) 6.24 on the PATH.

Data: download `2009bottleneck_trajectories_hdf5.zip` from
https://ped.fz-juelich.de/db/doku.php?id=hermes_bottleneck and unpack the
five `ao-*.h5` files into `data/`.

| file | purpose |
|---|---|
| `observables.py` | flow, density, speed from a trajectory (experiment or simulation) |
| `scenario.py` | JuPedSim replica of the bottleneck geometry |
| `driver.py` | Dakota analysis driver: parameters in, observables (or residuals) out |
| `compare_baseline.py` | default-parameter simulation vs experiment |
| `morris/dakota.in` | Morris screening, 7 parameters |
| `sobol/dakota.in` | Sobol indices, 5 parameters |
| `calib/dakota.in` | EGO calibration, all five parameters free |
| `calib_v0fixed/dakota.in` | EGO calibration with desired_speed fixed at 1.55 m/s |
| `run_all.sh` | full pipeline |
| `validate.py` | calibrated parameters on all five widths |
| `plot_*.py` | figures |
| `results/` | Dakota tabular outputs, calibration log, observables |
| `figures/` | figures used in the note |

Run a study from its folder:

    python3 compare_baseline.py                    # writes exp_observables.json
    cd morris && HERMES_WIDTHS=2.4,3.6,5.0 dakota -i dakota.in -o dakota.out
    cd sobol  && HERMES_WIDTHS=2.4,3.6,5.0 dakota -i dakota.in -o dakota.out
    cd calib  && HERMES_RESIDUALS=1 JPS_N_SEEDS=2 HERMES_WIDTHS=2.4,3.6,5.0 dakota -i dakota.in -o dakota.out
    python3 validate.py <desired_speed> <radius> <time_gap> <strength_neighbor> <range_neighbor>

Setup after Liao et al. (2014): 20 m corridor, 1 m boards, semicircular holding
area r = 8.618 m with 350 agents at 3 /m2. Calibrated on b = 2.4, 3.6, 5.0 m,
validated on 3.0 and 4.4 m. `run_all.sh` runs the whole pipeline.

| parameter | default | all five free (`calib/`) | desired speed fixed (`calib_v0fixed/`) |
|---|---|---|---|
| desired_speed [m/s] | 1.2 | 0.80 (lower bound) | 1.55 (measured free speed) |
| radius [m] | 0.20 | 0.141 | 0.127 |
| time_gap [s] | 1.0 | 0.561 | 0.811 |
| strength_neighbor_repulsion | 8 | 6.05 | 2.09 |
| range_neighbor_repulsion [m] | 0.10 | 0.155 | 0.248 |

Wall repulsion kept at defaults (strength 5, range 0.02).

## Second experiment: CrowdQueue (`crowdqueue/`)

Wuppertal 2018 entrance experiment (doi:10.34735/ped.2018.1): 0.5 m gate,
corridor widths 1.2–5.6 m, baseline / low / high motivation, 11–75 people.
Download `trajectories_hdf5.zip` from
https://ped.fz-juelich.de/db/doku.php?id=crowdqueue into `data/crowdqueue/`.
Geometry and initial positions come from the HDF5 files.

| file | purpose |
|---|---|
| `observables_cq.py` | gate flow (clog-aware), density and speed in the corridor |
| `scenario_cq.py` | geometry from the archive WKT, agents at the measured first-frame positions |
| `driver_cq.py` | Dakota driver, residuals normalised by sigma |
| `evaluate_cq.py` | one parameter set on all runs, 3 seeds |
| `calib_h0/` | EGO, 6 parameters (wall repulsion free), baseline-motivation runs at 1.2/3.4/5.6 m |
| `probe_hminus/`, `probe_hplus/` | time gap refit on low / high motivation runs |
| `results/` | transfer test with Hermes parameters, calibrated, refit |

| parameter | Hermes (v0 fixed) | CrowdQueue h0 |
|---|---|---|
| radius [m] | 0.127 | 0.101 (lower bound) |
| time_gap [s] | 0.811 | 0.958 |
| strength_neighbor | 2.09 | 1.70 |
| range_neighbor [m] | 0.248 | 0.336 |
| strength_geometry | 5 (fixed) | 1.39 |
| range_geometry [m] | 0.02 (fixed) | 0.105 |

Findings: the Hermes parameters clog at the 0.5 m gate in 16 of 21 runs; after
recalibration the model reaches ~1.1 /s and stays there, matching low-motivation
runs, undershooting baseline runs by 10–30 % and clogging in some 1.2 m corridor
seeds, and it cannot reach the 2.1 /s of the high-motivation run at any time gap
without destroying density and speed.
