# -*- coding: utf-8 -*-
"""Shift+click: set the area scheme names used by GFA Schedule."""
from pyrevit import forms, script

import hk_bootstrap
hk_bootstrap.ensure_path()
from hk_bim import revit_adapter  # noqa: E402

cfg = script.get_config()
for key, default, label in (("gfa_scheme", revit_adapter.GFA_SCHEME, "GFA area scheme name"),
                            ("sc_scheme", revit_adapter.SC_SCHEME, "Site coverage area scheme name")):
    val = forms.ask_for_string(default=cfg.get_option(key, default), prompt=label, title="HK GFA settings")
    if val:
        cfg.set_option(key, val)
script.save_config()
