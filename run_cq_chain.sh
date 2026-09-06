#!/bin/zsh
# Recompute the whole CrowdQueue chain on the corrected scenario (late entrants injected).
set -e; setopt null_glob
ROOT=$(cd "$(dirname "$0")" && pwd)
command -v dakota >/dev/null || export PATH=~/opt/dakota/bin:$PATH
export JPS_WORKERS=6
V=$ROOT; C=$V/crowdqueue; LOG=$V/cq_chain.log
H0=090_c_12_h0,110_c_12_h0,170_q_12_h0,190_q_34_h0,270_c_34_h0,030_c_56_h0,150_q_56_h0
HM=100_c_12_h-,120_c_12_h-,180_q_12_h-,280_c_34_h-,040_c_56_h-,160_q_56_h-,240_q_23_h-,060_c_45_h-,260_q_45_h-
best() { python3 -c "
import re,sys; t=open('$1').read(); m=re.search(r'Best parameters\s*=\s*\n((?:\s*\S+\s+\S+\n)+)', t)
d={l.split()[1]: l.split()[0] for l in m.group(1).strip().splitlines()}
print(' '.join(d[k] for k in sys.argv[1:]))" $2 $3 $4 $5 $6 $7; }
builtin cd $C
python3 build_exp_observables.py
for d in calib_h0 calib_h0_s9; do
  builtin cd $C/$d; rm -rf runs dakota.rst LHS_* fort.*
  CQ_RESIDUALS=1 JPS_N_SEEDS=2 CQ_RUNS=$H0 dakota -i dakota.in -o dakota.out > console.log 2>&1
  rm -rf runs dakota.rst LHS_* fort.*; echo "$d done $(date +%H:%M): $(best dakota.out radius time_gap strength_neighbor range_neighbor strength_geometry range_geometry)" >> $LOG
done
builtin cd $V/joint; rm -rf runs dakota.rst LHS_* fort.*
JPS_N_SEEDS=1 dakota -i dakota.in -o dakota.out > console.log 2>&1
rm -rf runs dakota.rst LHS_* fort.*; echo "joint done $(date +%H:%M): $(best dakota.out radius time_gap strength_neighbor range_neighbor strength_geometry range_geometry)" >> $LOG
builtin cd $C
P5=$(best calib_h0/dakota.out radius time_gap strength_neighbor range_neighbor strength_geometry range_geometry)
P9=$(best calib_h0_s9/dakota.out radius time_gap strength_neighbor range_neighbor strength_geometry range_geometry)
PJ=$(best $V/joint/dakota.out radius time_gap strength_neighbor range_neighbor strength_geometry range_geometry)
python3 evaluate_cq.py transfer_hermes 1.55 0.12749 0.81118 2.0872 0.24816 5 0.02 --seeds 3 > results/transfer_hermes.txt 2>&1
python3 evaluate_cq.py transfer_hermes_B 1.55 0.14763 0.55329 9.4434 0.10243 5 0.02 --seeds 3 > results/transfer_hermes_B.txt 2>&1
python3 evaluate_cq.py calib_h0 1.55 ${=P5} --seeds 3 > results/calib_h0.txt 2>&1
python3 evaluate_cq.py calib_h0_s9 1.55 ${=P9} --seeds 3 > results/calib_h0_s9.txt 2>&1
python3 evaluate_cq.py joint 1.55 ${=PJ} --seeds 3 > results/joint.txt 2>&1
echo "evaluations done $(date +%H:%M)" >> $LOG
# motivation probes with set C (the seed-9 h0 calibration)
set -- ${=P9}
sed -e "s/@TIME_GAP@/$2/" -e "s/@RADIUS@/$1/" -e "s/@STRENGTH_N@/$3/" -e "s/@RANGE_N@/$4/" -e "s/@STRENGTH_G@/$5/" -e "s/@RANGE_G@/$6/" probe_hminus/dakota.in.template > probe_hminus/dakota.in
builtin cd probe_hminus; rm -rf runs dakota.rst LHS_* fort.*
CQ_RESIDUALS=1 JPS_N_SEEDS=2 CQ_RUNS=$HM dakota -i dakota.in -o dakota.out > console.log 2>&1
rm -rf runs dakota.rst LHS_* fort.*; echo "probe h- done $(date +%H:%M): $(best dakota.out time_gap)" >> $LOG
builtin cd $C; python3 sweep_hplus.py $1 $3 $4 $5 $6 > results/hplus_sweep.txt 2>&1; echo "h+ sweep done $(date +%H:%M)" >> $LOG
builtin cd $V/semicircle; python3 evaluate_sc.py joint 1.55 ${=PJ} --seeds 3 > results/joint.txt 2>&1; echo "semicircle joint done $(date +%H:%M)" >> $LOG
echo "CQ CHAIN DONE" >> $LOG
