#!/usr/bin/env python3
"""Dakota driver wrapper for the two-parameter set-C motivation profile."""
import os

import driver_cq


os.environ["CQ_FIXED_PARAMS"] = (
    '{"radius": 0.144, "strength_neighbor": 9.41, "range_neighbor": 0.09, '
    '"strength_geometry": 2.60, "range_geometry": 0.032}'
)
driver_cq.main()
