# -*- coding: utf-8 -*-
# Dynamo Python Script node (engine: CPython3). Creates the BD general building plans sheet set.
#
# IN[0]  bim folder of the hk-architecture repo
# IN[1]  title block type (Family Types node)
# IN[2]  levels needing per-floor sheets (list of Levels, in order)
# IN[3]  template codes to include, e.g. ["000","002","010","011","012","020","040","050"]; empty = all
# IN[4]  plan scale (100 or 200)
# IN[5]  drawing number prefix (default "GBP")
# IN[6]  run (Boolean toggle)
# OUT    [sheet list preview, created numbers, skipped numbers]
import sys

if IN[0] and IN[0] not in sys.path:
    sys.path.insert(0, IN[0])

import clr  # noqa: E402
clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager  # noqa: E402
from RevitServices.Transactions import TransactionManager  # noqa: E402
clr.AddReference("RevitAPI")

from hk_bim import revit_adapter, sheets  # noqa: E402

doc = DocumentManager.Instance.CurrentDBDocument
tb = UnwrapElement(IN[1])  # noqa: F821  (Dynamo built-in)
levels = [UnwrapElement(l).Name for l in (IN[2] or [])]  # noqa: F821
codes = set(IN[3]) if IN[3] else None
scale = int(IN[4] or 100)
prefix = IN[5] or "GBP"

todo = sheets.sheet_list(levels, prefix=prefix, plan_scale=scale, include=codes)
preview = [[s["number"], s["name"], s["name_zh"], s["scale"]] for s in todo]
created, skipped = [], []
if IN[6]:
    TransactionManager.Instance.EnsureInTransaction(doc)
    created, skipped = revit_adapter.create_sheets(doc, todo, tb.Id, place_views=True, view_scale=scale)
    TransactionManager.Instance.TransactionTaskDone()
OUT = [preview, created, skipped]
