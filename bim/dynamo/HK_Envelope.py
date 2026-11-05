# -*- coding: utf-8 -*-
# Dynamo Python Script node (engine: CPython3 or IronPython). No Revit access needed.
#
# IN[0]  bim folder of the hk-architecture repo
# IN[1]  site area m2     IN[2] height m       IN[3] site class "A"/"B"/"C"
# IN[4]  building type    IN[5] floor-to-floor m   IN[6] podium floors
# IN[7]  intended non-domestic PR (composite)  IN[8] OZP max PR (optional)  IN[9] lease max GFA (optional)
# OUT    envelope as [[key, value], ...]
import sys

if IN[0] and IN[0] not in sys.path:
    sys.path.insert(0, IN[0])
from hk_bim import bpr_limits  # noqa: E402

env = bpr_limits.envelope(IN[1], IN[2], IN[3] or "A", IN[4] or "domestic",
                          floor_to_floor_m=IN[5] or 3.15, podium_floors=int(IN[6] or 0),
                          non_domestic_pr=IN[7] or 0.0, ozp_max_pr=IN[8], lease_max_gfa_m2=IN[9])
OUT = sorted([[k, v] for k, v in env.items()])
