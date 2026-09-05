#!/usr/bin/env python3
"""Joint Dakota driver: Hermes (3 widths) + CrowdQueue baseline runs, sigma-normalised
residuals concatenated (9 + 21 = 30). Usage: python3 driver_joint.py params.in results.out"""
import os, pathlib, subprocess, sys
HERE = pathlib.Path.cwd()  # Dakota work directory, where all drivers are linked
params, results = sys.argv[1], sys.argv[2]
env = dict(os.environ, HERMES_RESIDUALS="1", HERMES_NORMALIZE="1", HERMES_WIDTHS="2.4,3.6,5.0",
           CQ_RESIDUALS="1", CQ_RUNS="090_c_12_h0,110_c_12_h0,170_q_12_h0,190_q_34_h0,270_c_34_h0,030_c_56_h0,150_q_56_h0",
           JPS_N_SEEDS=os.environ.get("JPS_N_SEEDS", "2"))
subprocess.run([sys.executable, str(HERE / "driver.py"), params, "res_hermes.out"], check=True, env=env)
subprocess.run([sys.executable, str(HERE / "driver_cq.py"), params, "res_cq.out"], check=True, env=env)
with open(results, "w") as out:
    out.write(open("res_hermes.out").read()); out.write(open("res_cq.out").read())
