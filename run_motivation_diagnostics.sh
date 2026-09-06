#!/bin/zsh
# Recompute the condition-specific profiles and positioning diagnostic.
set -e
setopt null_glob

ROOT=$(cd "$(dirname "$0")" && pwd)
C=$ROOT/crowdqueue
command -v dakota >/dev/null || export PATH=~/opt/dakota/bin:$PATH
H0=030_c_56_h0,050_c_45_h0,070_c_23_h0,090_c_12_h0,110_c_12_h0,150_q_56_h0,170_q_12_h0,190_q_34_h0,230_q_23_h0,250_q_45_h0,270_c_34_h0
HM=040_c_56_h-,060_c_45_h-,100_c_12_h-,120_c_12_h-,160_q_56_h-,180_q_12_h-,240_q_23_h-,260_q_45_h-,280_c_34_h-
C_PARAMS=($(python3 $C/parameter_io.py $C/calib_h0_s9/dakota.out radius time_gap strength_neighbor range_neighbor strength_geometry range_geometry))

builtin cd $C
python3 build_exp_observables.py

run_dakota() {
  local directory=$1
  local runs=$2
  builtin cd $C/$directory
  rm -rf runs dakota.rst LHS_* fort.*
  CQ_RESIDUALS=1 CQ_RUNS=$runs JPS_N_SEEDS=1 JPS_WORKERS=3 \
    dakota -i dakota.in -o dakota.out > console.log 2>&1
  rm -rf runs dakota.rst LHS_* fort.*
}

(run_dakota motivation_profile_h0 $H0) &
H0_PID=$!
(run_dakota motivation_profile_hminus $HM) &
HM_PID=$!
wait $H0_PID $HM_PID

builtin cd $C
sed -e "s/@TIME_GAP@/$C_PARAMS[2]/" -e "s/@RADIUS@/$C_PARAMS[1]/" \
  -e "s/@STRENGTH_N@/$C_PARAMS[3]/" -e "s/@RANGE_N@/$C_PARAMS[4]/" \
  -e "s/@STRENGTH_G@/$C_PARAMS[5]/" -e "s/@RANGE_G@/$C_PARAMS[6]/" \
  probe_hminus/dakota.in.template > probe_hminus/dakota.in
builtin cd probe_hminus
rm -rf runs dakota.rst LHS_* fort.*
CQ_RESIDUALS=1 JPS_N_SEEDS=2 CQ_RUNS=$HM dakota -i dakota.in -o dakota.out > console.log 2>&1
rm -rf runs dakota.rst LHS_* fort.*

builtin cd $C
python3 sweep_hplus.py $C_PARAMS[1] $C_PARAMS[3] $C_PARAMS[4] $C_PARAMS[5] $C_PARAMS[6] > results/hplus_sweep.txt 2>&1
python3 profile_motivation.py h0 --workers 2 &
H0_PID=$!
python3 profile_motivation.py h- --workers 2 &
HM_PID=$!
python3 profile_spacing.py --workers 2 &
SPACING_PID=$!
wait $H0_PID $HM_PID $SPACING_PID

H0_DAKOTA=($(python3 parameter_io.py motivation_profile_h0/dakota.out desired_speed time_gap))
HM_DAKOTA=($(python3 parameter_io.py motivation_profile_hminus/dakota.out desired_speed time_gap))
HM_PROBE=($(python3 parameter_io.py probe_hminus/dakota.out time_gap))
H0_GRID=($(python3 -c "import json; b=json.load(open('results/motivation_profile_h0.json'))['best']; print(b['desired_speed'], b['time_gap'])"))
HM_GRID=($(python3 -c "import json; b=json.load(open('results/motivation_profile_hminus.json'))['best']; print(b['desired_speed'], b['time_gap'])"))

python3 evaluate_motivation.py dakota_h0_confirm h0 $H0_DAKOTA[1] $C_PARAMS[1] $H0_DAKOTA[2] $C_PARAMS[3] $C_PARAMS[4] $C_PARAMS[5] $C_PARAMS[6] --seeds 3
python3 evaluate_motivation.py dakota_hminus_confirm h- $HM_DAKOTA[1] $C_PARAMS[1] $HM_DAKOTA[2] $C_PARAMS[3] $C_PARAMS[4] $C_PARAMS[5] $C_PARAMS[6] --seeds 3
python3 evaluate_motivation.py probe_hminus_confirm h- 1.55 $C_PARAMS[1] $HM_PROBE[1] $C_PARAMS[3] $C_PARAMS[4] $C_PARAMS[5] $C_PARAMS[6] --seeds 3
python3 evaluate_motivation.py profile_h0_confirm h0 $H0_GRID[1] $C_PARAMS[1] $H0_GRID[2] $C_PARAMS[3] $C_PARAMS[4] $C_PARAMS[5] $C_PARAMS[6] --seeds 3
python3 evaluate_motivation.py profile_hminus_confirm h- $HM_GRID[1] $C_PARAMS[1] $HM_GRID[2] $C_PARAMS[3] $C_PARAMS[4] $C_PARAMS[5] $C_PARAMS[6] --seeds 3

SPACING=($(python3 -c "import json; b=json.load(open('results/motivation_profile_spacing_hminus.json'))['best']; print(b['radius'], b['range_neighbor'])"))
python3 evaluate_motivation.py spacing_hminus_confirm h- $H0_DAKOTA[1] $SPACING[1] $H0_DAKOTA[2] $C_PARAMS[3] $SPACING[2] $C_PARAMS[5] $C_PARAMS[6] --seeds 3

python3 evaluate_front_occupancy.py
python3 plot_motivation_profile.py
python3 plot_front_occupancy.py
python3 plot_hplus.py
python3 directed_speed.py
