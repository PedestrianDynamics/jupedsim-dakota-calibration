# Calibrating and validating JuPedSim's Collision Free Speed model with Dakota

Code, Dakota inputs, results and figures for the note
[How do you validate a pedestrian model against real data?](https://pedestriandynamics.org/notes/dakota-calibration/)
on pedestriandynamics.org. This README describes the final state of the study;
earlier intermediate results have been superseded and are not repeated here.

## Requirements

Python 3 with `jupedsim` 1.4.2, `pedpy` 1.4.0, `h5py`, `shapely`, `numpy`,
`matplotlib`; [Dakota](https://github.com/snl-dakota/dakota/releases) 6.24 on
the PATH (the scripts fall back to `~/opt/dakota/bin`). Experiment data: see
`data/README.md` (three archive downloads, not included).

## Layout

| folder | content |
|---|---|
| `hermes/` | Hermes 2009 wide-bottleneck study: driver, scenario, observables, Morris (`morris*/`), Sobol (`sobol*/`), calibrations (`calib/`, `calib_v0fixed/`, `calib_v0fixed_s9/`), validation and plotting scripts, `truncation_check.py` |
| `crowdqueue/` | CrowdQueue 2018 narrow-gate study: driver, scenario, observables, calibrations from two starts (`calib_h0/`, `calib_h0_s9/`), motivation probes, per-seed results in `results/` |
| `semicircle/` | BaSiGo 2013 unguided entrance: boundary-condition replay, density maps, results |
| `joint/` | joint Hermes + CrowdQueue calibration (`driver_joint.py`, `best_params.json`) |
| `results/` | Hermes validations (six seeds, sets A and B; three seeds, joint), baseline, seed-noise |
| `figures/` | the figures of the note |
| `run_all_fixed.sh` | recomputes the whole CrowdQueue chain, the Hermes validations and the semicircle from a checkout |

Every per-seed record in `crowdqueue/results/*.json` carries the run, seed,
expected (tracked) and injected population, dropped injections, completion
status (`emptied` / `not emptied` / `stalled` / `failed` with the exception
type), the measurement window, active-passage and throughput flow, density,
speed, and a subsampled N(t) curve.

## Running

    cd hermes && python3 compare_baseline.py            # baseline and exp_observables.json
    cd hermes/morris_r20 && HERMES_WIDTHS=2.4,3.6,5.0 dakota -i dakota.in -o dakota.out
    cd hermes/calib_v0fixed && HERMES_RESIDUALS=1 JPS_N_SEEDS=2 HERMES_WIDTHS=2.4,3.6,5.0 dakota -i dakota.in -o dakota.out
    ./run_all_fixed.sh                                   # CrowdQueue chain + Hermes validations + semicircle (about 1 h)

## Final parameter sets

Desired speed fixed at the measured 1.55 m/s in all calibrated sets. Sets A/B and
C/D are two optimizer starts on the same data.

| parameter | default | Hermes A | Hermes B | CrowdQueue C | CrowdQueue D | joint |
|---|---|---|---|---|---|---|
| radius [m] | 0.20 | 0.127 | 0.148 | 0.144 | 0.101 | 0.115 |
| time_gap [s] | 1.0 | 0.811 | 0.553 | 0.833 | 0.958 | 1.024 |
| strength_neighbor | 8 | 2.09 | 9.44 | 9.41 | 1.70 | 4.01 |
| range_neighbor [m] | 0.10 | 0.248 | 0.102 | 0.090 | 0.336 | 0.190 |
| strength_geometry | 5 | 5 (fixed) | 5 (fixed) | 2.60 | 1.39 | 2.60 |
| range_geometry [m] | 0.02 | 0.02 (fixed) | 0.02 (fixed) | 0.032 | 0.105 | 0.045 |

## Final findings (short)

- Hermes: both calibrated sets improve all observables substantially; by the
  stated tolerance (6 % flow, 10 % density and speed) both fail at the held-out
  3.0 m flow and at the 5.0 m calibration flow, set A also at the held-out 4.4 m
  speed. At 5.0 m set A keeps density and underpredicts speed, set B the reverse.
- Sobol: the group of influential parameters is stable across 40/80/160 base
  samples and three replicate seeds; magnitudes and within-group order are not.
- CrowdQueue: Hermes set A stalls in 46 of 63 seeds, set B empties 62 but is
  20–40 % too fast. Set C (best of two starts) empties all 63 seeds with baseline
  flows +12 % on average (−19 % to +36 %). The model does not reproduce the
  difference between motivation conditions in either direction.
- Joint: Hermes norm 7.9 vs 2.4–2.7 for the specialists, CrowdQueue norm 12.0 vs
  10.9, 60 of 63 seeds emptied. No set found meets the tolerances in both.
- Semicircle: Hermes A and the joint set drain the crowd at 1.3 and 1.7 /s where
  the experiment gave 0.6 /s, with a regular, too-shallow density profile.

## Pipeline corrections (2026-09-06)

Three errors were found by review and fixed; everything downstream was
recomputed: (1) participants entering the tracked corridor after the first frame
are injected at their first observation (`crowdqueue/observables_cq.arrivals`);
(2) the JuPedSim trajectory writer is closed so no frames are lost
(`writer.close()`); (3) the CrowdQueue walkable area is clipped to the corridor
and the exit placed at the gate outlet. `hermes/truncation_check.py` shows the
retained Hermes analyses are insensitive to (2): at most two crossings and 0.4 %
in any observable.
