# -*- coding: utf-8 -*-
"""Turn results into text, and call tools/bpr_check.py where the engine allows."""
from __future__ import absolute_import, division, print_function, unicode_literals

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.normpath(os.path.join(_HERE, "..", "..", "tools"))


def can_run_bpr_check():
    """bpr_check.py uses f-strings, so it needs CPython 3.6+."""
    return sys.version_info >= (3, 6) and os.path.exists(os.path.join(TOOLS_DIR, "bpr_check.py"))


def run_bpr_check(project):
    """Run the full checker on a project dict. Returns (markdown, n_fail) or
    (None, None) on IronPython / when the tools folder is missing."""
    if not can_run_bpr_check():
        return None, None
    import importlib.util
    spec = importlib.util.spec_from_file_location("hk_bpr_check", os.path.join(TOOLS_DIR, "bpr_check.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    import copy
    p = copy.deepcopy(project)  # run() writes helper keys into floors
    rows, exempt, notes, _ = mod.run(p)
    return mod.report(p, rows, exempt, notes), sum(1 for r in rows if r[4] == "FAIL")


def quick_md(result, title="Quick GFA / PR / SC check"):
    t = result["totals"]
    lines = ["# %s" % title, "",
             "Accountable GFA: %.2f m2 (domestic %.2f, non-domestic %.2f); gross built %.2f m2; disregarded %.2f m2."
             % (t["total"], t["domestic"], t["non_domestic"], t["gross"], t["disregarded"]),
             "PR: domestic %.3f, non-domestic %.3f, total %.3f." % (t["pr_domestic"], t["pr_non_domestic"], t["pr_total"]),
             "", "| Ref | Item | Value | Limit | Result |", "| --- | --- | --- | --- | --- |"]
    for row in result["rows"]:
        lines.append("| %s | %s | %s | %s | %s |" % row)
    fails = sum(1 for r in result["rows"] if r[4] == "FAIL")
    lines += ["", "%d fail(s). Draft for Authorized Person review; run tools/bpr_check.py for the full check." % fails]
    return "\n".join(lines)
