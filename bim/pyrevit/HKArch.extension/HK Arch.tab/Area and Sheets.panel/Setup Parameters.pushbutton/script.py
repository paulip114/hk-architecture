# -*- coding: utf-8 -*-
"""Add the HK shared parameters (HK_GFA_Category, HK_Use, HK_Site_Area,
title block fields ...) to this model from bim/revit/HK_shared_parameters.txt,
and create the "HK GFA" and "HK SC" area schemes if missing."""
from __future__ import print_function

__title__ = "Setup\nParameters"
__author__ = "hk-architecture"

import os

import hk_bootstrap
bim = hk_bootstrap.ensure_path()

from pyrevit import DB, revit, script  # noqa: E402

from hk_bim import revit_adapter  # noqa: E402

doc = revit.doc
out = script.get_output()
spf = os.path.join(bim, "revit", "HK_shared_parameters.txt")

with revit.Transaction("HK: shared parameters and area schemes"):
    added, present = revit_adapter.bind_shared_parameters(doc, doc.Application, spf)
    schemes = [s.Name for s in DB.FilteredElementCollector(doc).OfClass(DB.AreaScheme)]
    made = []
    for name in (revit_adapter.GFA_SCHEME, revit_adapter.SC_SCHEME):
        if name not in schemes:
            # AreaScheme.Create is not in the API for every Revit version; fall back to a note.
            create = getattr(DB.AreaScheme, "Create", None)
            if create is not None:
                create(doc).Name = name
                made.append(name)
            else:
                out.print_md("Create area scheme **%s** by hand (Area and Volume Computations > Area Schemes)." % name)

out.print_md("# HK parameters")
out.print_md("Added: %s" % (", ".join(added) or "none"))
out.print_md("Already in the model: %s" % (", ".join(present) or "none"))
if made:
    out.print_md("Created area schemes: %s" % ", ".join(made))
out.print_md("Next: fill Project Information (HK_Site_Area, HK_Building_Height, HK_Site_Class, "
             "HK_Building_Type ...), draw Areas in the HK GFA scheme, then run **GFA Schedule**.")
