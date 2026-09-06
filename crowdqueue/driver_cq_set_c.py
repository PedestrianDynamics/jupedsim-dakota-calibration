#!/usr/bin/env python3
"""Dakota driver wrapper for the two-parameter set-C motivation profile."""
import json
import os

import driver_cq
from parameter_io import best_parameters


PARAMETER_NAMES = (
    "radius", "strength_neighbor", "range_neighbor",
    "strength_geometry", "range_geometry",
)


if __name__ == "__main__":
    calibrated = best_parameters(driver_cq.HERE / "calib_h0_s9" / "dakota.out")
    fixed = {name: calibrated[name] for name in PARAMETER_NAMES}
    os.environ["CQ_FIXED_PARAMS"] = json.dumps(fixed)
    driver_cq.main()
