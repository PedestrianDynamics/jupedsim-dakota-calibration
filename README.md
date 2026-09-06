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
| `crowdqueue/` | CrowdQueue 2018 narrow-gate study: driver, scenario, observables, calibrations from two starts (`calib_h0/`, `calib_h0_s9/`), motivation-condition diagnostic calibrations, motivation probes, per-seed results in `results/` |
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

Each Dakota driver also writes an `evaluation_status.json` sidecar in its
evaluation directory. It records the parameters, seeds and per-run completion
status, crossed population and exception category. In the joint driver the
sidecars are named `hermes_evaluation_status.json` and
`crowdqueue_evaluation_status.json`. Dakota still receives finite numeric
responses: failed or too-short runs use a zero fallback, while incomplete runs
retain whatever finite partial observables were computed. Neither case should
be interpreted as a physical zero flow without checking the sidecar.

## Running

    cd hermes && python3 compare_baseline.py            # baseline and exp_observables.json
    cd hermes/morris_r20 && HERMES_WIDTHS=2.4,3.6,5.0 dakota -i dakota.in -o dakota.out
    cd hermes/calib_v0fixed && HERMES_RESIDUALS=1 JPS_N_SEEDS=2 HERMES_WIDTHS=2.4,3.6,5.0 dakota -i dakota.in -o dakota.out
    ./run_all_fixed.sh                                   # CrowdQueue chain + Hermes validations + semicircle (about 1 h)
    ./run_motivation_diagnostics.sh                      # v0/T and spacing profiles + front-occupancy diagnostic

## Final parameter sets

Desired speed fixed at the measured 1.55 m/s in all calibrated sets. Sets A/B and
C/D are two optimizer starts on the same data.

| parameter | default | Hermes A | Hermes B | CrowdQueue C | CrowdQueue D | joint |
|---|---|---|---|---|---|---|
| radius [m] | 0.20 | 0.127 | 0.148 | 0.124 | 0.101 | 0.115 |
| time_gap [s] | 1.0 | 0.811 | 0.553 | 1.038 | 0.958 | 0.962 |
| strength_neighbor | 8 | 2.09 | 9.44 | 9.01 | 1.70 | 8.62 |
| range_neighbor [m] | 0.10 | 0.248 | 0.102 | 0.062 | 0.336 | 0.189 |
| strength_geometry | 5 | 5 (fixed) | 5 (fixed) | 2.96 | 1.39 | 4.69 |
| range_geometry [m] | 0.02 | 0.02 (fixed) | 0.02 (fixed) | 0.072 | 0.105 | 0.031 |

## Final findings (short)

- Hermes: both calibrated sets improve all observables substantially; by the
  stated tolerance (6 % flow, 10 % density and speed) both fail at the held-out
  3.0 m flow and at the 5.0 m calibration flow, set A also at the held-out 4.4 m
  speed. At 5.0 m set A keeps density and underpredicts speed, set B the reverse.
- Sobol: the group of influential parameters is stable across 40/80/160 base
  samples and three replicate seeds; magnitudes and within-group order are not.
- CrowdQueue: Hermes set A stalls in 46 of 63 seeds, set B empties 59 but is
  20–40 % too fast. Set C also empties 59 of 63 seeds; its baseline flows are
  +12 % on average (−2 % to +30 %). Set D, the other optimizer start, stalls in
  14 seeds and fails once. Identical seeds reproduce identical simulations.
- Motivation diagnostic: with the five interaction parameters fixed at set C,
  the extended v0/T profiles select approximately (1.17 m/s, 0.79 s) for h0 and
  (1.50 m/s, 1.73 s) for h−. Three-seed norms are 9.19 and 11.74, or 1.60 and
  2.26 assumed standard deviations per residual. The h− timing fit reproduces
  much of the front-area head-count contrast but remains 24–53 % too slow in
  seven runs. A radius/neighbor-range slice is worse (three-seed norm 14.41) and
  develops a stall cliff: at neighbor ranges of 0.337 m or more all nine runs
  stall or fail at every sampled radius. Seven-parameter own/swap norms are
  8.26/15.65 for h0 and 10.64/16.41 for h−; several coordinates move, so the
  fits distinguish conditions but do not identify a mechanism. The h+ condition
  has only one usable run and is not calibrated separately.
- Joint: Hermes norm 6.2 versus 2.4–2.7 for the specialists; CrowdQueue norm
  13.6 versus 11.3 for set C; 57 of 63 seeds emptied. No set found meets the
  tolerances in both experiments.
- Semicircle: Hermes A and the joint set drain the crowd at about 1.3 and
  1.4 /s where the experiment gave 0.57 /s, with a regular, too-shallow density
  profile.

## Pipeline corrections and safeguards (2026-09-06)

Five errors were found by review and fixed; everything downstream was
recomputed: (1) participants entering the tracked corridor after the first frame
are injected at their first observation (`crowdqueue/observables_cq.arrivals`);
(2) the JuPedSim trajectory writer is closed so no frames are lost
(`writer.close()`); (3) the CrowdQueue walkable area is clipped to the corridor
and the exit placed at the gate outlet; (4) mean speed excludes frames in which
the measurement area is empty; and (5) motivation reruns now resolve set C from
the seed-9 Dakota output instead of a copied constant or the other optimizer
start. `hermes/truncation_check.py` shows the
retained Hermes analyses are insensitive to (2): at most two crossings and 0.4 %
in any observable. The drivers now retain explicit audit records for failed and
incomplete evaluations, and the Hermes launcher resolves its repository root
instead of relying on an undefined shell variable. The Hermes initial
population is a synthetic jittered lattice in a semicircular initialization
region; that region is not a measured physical boundary. Hermes and CrowdQueue
screening use fixed simulation seeds, while seed variability is assessed by
separate replicate runs.

The motivation diagnostic includes `profile_motivation.py`, which keeps the five
static set-C parameters fixed and profiles desired speed and time gap,
`profile_spacing.py`, which fixes the h0 valley and profiles radius and neighbor
range on h−, and `plot_motivation_profile.py` for the three-panel surface. The
profile figure marks stalled and failed grid points instead of interpreting its
yellow stall cliff as an ordinary residual landscape. `evaluate_front_occupancy.py`
derives the number of people in the upstream measurement area over time for the
paired 1.2 m runs, both at common set C and at the condition-specific profile
points. `directed_speed.py` (`cd crowdqueue && python3 directed_speed.py`,
output `results/directed_speed.json` and `directed_speed.png`) decomposes the
front-area speed into the radial component towards the gate and the tangential
remainder for all 21 runs and the two profile points, and recomputes the h0 and
h− norms with radial speed as a sensitivity check; people standing still
register 0.09–0.13 m/s with the calibrated speed definition, which bounds how
well the wide-corridor speed terms can be resolved. `animate_motivation_pair.py`
renders the two 63-person 1.2 m runs, experiment beside simulation, as
`motivation_pair.gif` for the note (illustration only). For a production Dakota
calibration, capture failures separately and use a declared recovery value or a
smooth, documented penalty; a finite fallback is not a physical zero.
