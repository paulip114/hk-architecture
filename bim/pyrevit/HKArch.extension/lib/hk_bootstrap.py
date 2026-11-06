# -*- coding: utf-8 -*-
"""Puts the repo's bim/ folder on sys.path so `import hk_bim` works.

pyRevit adds this extension's lib/ folder to sys.path automatically. The
extension lives at <repo>/bim/pyrevit/HKArch.extension, so bim/ is two
levels up. Set HK_BIM_PATH to point elsewhere if you move the extension.
"""
import os
import sys


def ensure_path():
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [os.environ.get("HK_BIM_PATH"),
                  os.path.normpath(os.path.join(here, "..", "..", ".."))]
    for c in candidates:
        if c and os.path.isdir(os.path.join(c, "hk_bim")):
            if c not in sys.path:
                sys.path.insert(0, c)
            return c
    raise ImportError("hk_bim not found. Set HK_BIM_PATH to the repo's bim folder.")
