#!/bin/zsh
set -e; setopt null_glob
ROOT=$(cd "$(dirname "$0")/.." && pwd)
command -v dakota >/dev/null || export PATH=~/opt/dakota/bin:$PATH
H=$ROOT/hermes
for d in sobol_N40_s11 sobol_N40_s17 sobol_N80_s3 sobol_N160_s3 morris_r20; do
  builtin cd $H/$d; rm -rf runs dakota.rst LHS_* fort.*
  HERMES_WIDTHS=2.4,3.6,5.0 dakota -i dakota.in -o dakota.out > console.log 2>&1
  rm -rf runs dakota.rst LHS_* fort.*
  echo "$d done $(date +%H:%M)"
done
echo "CONVERGENCE DONE"
