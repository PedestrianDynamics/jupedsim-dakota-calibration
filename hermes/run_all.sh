#!/bin/zsh
# Full pipeline: baseline -> (Morris | EGO calibration) -> Sobol -> validation -> figures
set -e
setopt null_glob
command -v dakota >/dev/null || export PATH=~/opt/dakota/bin:$PATH
H=$ROOT/hermes
builtin cd $H
W=2.4,3.6,5.0
[ -f baseline/baseline.json ] || python3 compare_baseline.py > logs_baseline.txt
python3 - <<'PY'
import json; b = json.load(open("baseline/baseline.json"))
json.dump({f"{v['b']:.1f}": v["exp"] for v in b.values()}, open("exp_observables.json", "w"), indent=1)
PY
python3 plot_baseline.py && python3 plot_setup.py
for d in morris sobol calib; do rm -rf $d/runs $d/dakota.rst $d/LHS_* $d/*.dat $d/dakota.out $d/console.log $d/fort.*; done
( builtin cd morris && HERMES_WIDTHS=$W dakota -i dakota.in -o dakota.out > console.log 2>&1 ) &
( builtin cd calib && HERMES_RESIDUALS=1 JPS_N_SEEDS=2 HERMES_WIDTHS=$W dakota -i dakota.in -o dakota.out > console.log 2>&1 ) &
wait
echo "morris+calib done $(date)"
python3 plot_morris.py
( builtin cd sobol && HERMES_WIDTHS=$W dakota -i dakota.in -o dakota.out > console.log 2>&1 )
echo "sobol done $(date)"
python3 plot_sobol.py
best=$(python3 -c "
import re; t = open('calib/dakota.out').read()
m = re.search(r'Best parameters\s*=\s*\n((?:\s*\S+\s+\S+\n){5})', t)
print(' '.join(l.split()[0] for l in m.group(1).strip().splitlines()))")
echo "best: $best"
python3 validate.py $best > logs_validation.txt
for d in morris sobol calib; do rm -rf $d/runs $d/dakota.rst $d/LHS_* $d/fort.*; done
echo "ALL DONE $(date)"
