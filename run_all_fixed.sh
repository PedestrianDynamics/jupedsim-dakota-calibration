#!/bin/zsh
set -e; setopt null_glob
V=/Users/chraibi/_sciebo_mixed/dakota/v2; export JPS_WORKERS=6
$V/run_cq_chain.sh
builtin cd $V/hermes
python3 validate.py 1.55 0.12749 0.81118 2.0872 0.24816 > logs_validation.txt 2>&1; cp validation/validation.json validation/validation_seed5.json
python3 validate.py 1.55 0.14763 0.55329 9.4434 0.10243 > logs_validation_B.txt 2>&1; cp validation/validation.json validation/validation_seed9.json; cp validation/validation_seed5.json validation/validation.json
PJ=$(python3 -c "
import re; t=open('$V/joint/dakota.out').read(); m=re.search(r'Best parameters\s*=\s*\n((?:\s*\S+\s+\S+\n)+)', t)
d={l.split()[1]: l.split()[0] for l in m.group(1).strip().splitlines()}; print(' '.join(d[k] for k in ['radius','time_gap','strength_neighbor','range_neighbor','strength_geometry','range_geometry']))")
python3 -c "
import json; v = '$PJ'.split(); k = ['radius','time_gap','strength_neighbor','range_neighbor','strength_geometry','range_geometry']
json.dump(dict(desired_speed=1.55, **{a: float(b) for a, b in zip(k, v)}), open('$V/joint/best_params.json', 'w'), indent=1)"
python3 validate_joint.py > logs_validation_joint.txt 2>&1
python3 compare_baseline.py > logs_baseline.txt 2>&1
python3 plot_baseline.py > /dev/null 2>&1
echo "hermes validations done $(date +%H:%M)" >> $V/cq_chain.log
builtin cd $V/semicircle
python3 evaluate_sc.py hermes 1.55 0.12749 0.81118 2.0872 0.24816 5.0 0.02 --seeds 3 > results/hermes.txt 2>&1
python3 evaluate_sc.py joint 1.55 ${=PJ} --seeds 3 > results/joint.txt 2>&1
echo "semicircle done $(date +%H:%M)" >> $V/cq_chain.log
echo "ALL FIXED DONE" >> $V/cq_chain.log
