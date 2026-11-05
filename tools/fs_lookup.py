#!/usr/bin/env python3
"""Look up FS Code 2011 (2024 Ed.) Part A definitions, use classes, performance requirements,
or any clause in the full Code text.

Usage:
  python3 fs_lookup.py "travel distance"      # definition (English or Chinese term, partial match)
  python3 fs_lookup.py 4b                     # use classification (Table A1)
  python3 fs_lookup.py B5                     # performance requirement
  python3 fs_lookup.py --clause C13.4         # print the clause from fs-code-2011.txt (if present)
"""
import argparse
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
A = json.loads((HERE.parent / "fs-code" / "part_a.json").read_text(encoding="utf-8"))
TEXT = [HERE.parent / "fs-code-2011.txt", Path("/mnt/project-files/architect-kb/fs-code-2011.txt")]


def clause(cid):
    src = next((p for p in TEXT if p.exists()), None)
    if src is None:
        return "fs-code-2011.txt not found (gitignored): save the Code text next to README.md."
    lines = src.read_text(encoding="utf-8").splitlines()
    pat = re.compile(rf"^\s*Clause {re.escape(cid)}\s*$")
    start = next((i for i, l in enumerate(lines) if pat.match(l)), None)
    if start is None:
        return f"Clause {cid} not found."
    end = next((j for j in range(start + 1, len(lines)) if re.match(r"^\s*(Clause [A-G]\d|Subsection [A-G]\d|Section \d)", lines[j])),
               min(start + 60, len(lines)))
    return "\n".join(lines[start:end]).strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("term", nargs="?")
    ap.add_argument("--clause")
    a = ap.parse_args()
    if a.clause:
        print(clause(a.clause))
        return
    t = (a.term or "").strip()
    if t in A["use_classes"]:
        u = A["use_classes"][t]
        print(f"Use Class {t}: {u['name']} ({u['zh']})\n{u['examples']}")
        return
    if t.upper() in A["performance_requirements"]:
        print(f"Performance Requirement {t.upper()}: {A['performance_requirements'][t.upper()]}")
        return
    hits = [(k, v) for k, v in A["definitions"].items() if t.lower() in k.lower() or (v.get("zh") and t in v["zh"])]
    if not hits:
        print(f"No definition matches '{t}'. Try --clause, or search fs-code-2011.txt.")
    for k, v in hits:
        print(f"“{k}”{' ('+v['zh']+')' if v.get('zh') else ''} {v['text']}\n  – FS Code 2011 Part A, Section 3\n")


if __name__ == "__main__":
    main()
