#!/usr/bin/env python3
"""Space-awareness Dakota driver: the joint objective of joint/driver_joint.py
(Hermes 3 widths + CrowdQueue 7 baseline runs, 30 sigma-normalised residuals)
with the distance-based state rule of space_state.py switched on by the four
extra design variables d_switch, w_switch, f_radius, f_time_gap.
Usage: python3 driver_sa.py params.in results.out"""
import os
import pathlib
import subprocess
import sys
HERE = pathlib.Path.cwd()  # Dakota work directory, where all drivers are linked
params, results = sys.argv[1], sys.argv[2]
env = dict(os.environ, HERMES_RESIDUALS="1", HERMES_NORMALIZE="1", HERMES_WIDTHS="2.4,3.6,5.0",
           HERMES_STATUS_FILE="hermes_evaluation_status.json",
           CQ_RESIDUALS="1", CQ_RUNS="090_c_12_h0,110_c_12_h0,170_q_12_h0,190_q_34_h0,270_c_34_h0,030_c_56_h0,150_q_56_h0",
           CQ_STATUS_FILE="crowdqueue_evaluation_status.json",
           JPS_N_SEEDS=os.environ.get("JPS_N_SEEDS", "1"))
subprocess.run([sys.executable, str(HERE / "driver.py"), params, "res_hermes.out"], check=True, env=env)
subprocess.run([sys.executable, str(HERE / "driver_cq.py"), params, "res_cq.out"], check=True, env=env)
with open(results, "w") as out:
    out.write(open("res_hermes.out").read())
    out.write(open("res_cq.out").read())
