# -*- coding: utf-8 -*-
"""Shared area-calculation and sheet-setup logic for the HK BIM scripts.

Plain Python only (no Revit / Rhino imports), written to run unchanged on
IronPython 2.7 (pyRevit default engine, GhPython in Rhino 7) and CPython 3
(pyRevit CPython engine, Dynamo CPython3 node, Rhino 8 Python 3).

Rules and schedule figures come from the knowledge base in this repo:
  bpr/first_schedule.json   First / Second Schedule of Cap. 123F
  tools/bpr_check.py        full compliance checker (CPython 3 only)
"""
from __future__ import absolute_import

__version__ = "0.1.0"
