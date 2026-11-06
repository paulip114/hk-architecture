#!/usr/bin/env python3
"""ArchBench: measures an AI agent doing Hong Kong architect's work (stdlib only).

  python3 benchmark/archbench.py list
  python3 benchmark/archbench.py export --out pack/
  python3 benchmark/archbench.py run --name my-agent --agent-cmd 'claude -p' [--mode closed|kb] [--tasks F01,S01]
  python3 benchmark/archbench.py baseline gold --name gold
  python3 benchmark/archbench.py score benchmark/runs/my-agent
  python3 benchmark/archbench.py compare benchmark/runs/a benchmark/runs/b

Scoring is deterministic. What it does not measure is listed in benchmark/README.md.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TASKS_DIR = HERE / "tasks"
RUNS_DIR = HERE / "runs"
STAGES = {"1": "可行性研究與前期規劃", "2": "方案設計", "3": "設計發展與法定審批", "4": "施工圖與招標", "5": "施工與竣工交付"}
# Provisional gates: a starting point, not calibrated against human architects.
GATES = {"overall": 0.80, "stage": 0.60}
KB_EXCLUDE = {"benchmark", ".git", ".venv", "__pycache__", "tests", ".DS_Store", "AGENTS.md", "CLAUDE.md"}
PUBLIC_CHECK_FIELDS = ("path", "type", "options", "desc", "file")


def load_tasks(ids=None):
    tasks = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(TASKS_DIR.glob("*.json"))]
    if ids:
        wanted = set(ids)
        unknown = wanted - {t["id"] for t in tasks}
        if unknown:
            raise SystemExit(f"Unknown task id(s): {', '.join(sorted(unknown))}")
        tasks = [t for t in tasks if t["id"] in wanted]
    return tasks


def public_view(task):
    """What the agent may see: never the expected values or the patterns."""
    fields = []
    for c in task["checks"]:
        if c["type"] == "absent":
            continue
        fields.append({k: c[k] for k in PUBLIC_CHECK_FIELDS if k in c})
    return {"id": task["id"], "title": task["title"], "prompt": task["prompt"],
            "input": task.get("input", {}), "answer_fields": fields}


def task_markdown(task, mode):
    v = public_view(task)
    kb = ("A knowledge base and tools are in ./kb (start with kb/README.md and kb/docs/reference.md). Only use them if they help."
          if mode == "kb" else "No knowledge base is provided for this task. Use what you know and say what you cannot verify.")
    return f"""# {v['title']} ({v['id']})

{v['prompt']}

{kb}

## Input
```json
{json.dumps(v['input'], ensure_ascii=False, indent=1)}
```

## Required answer
Answer with one JSON object using these fields. A dotted path means a nested object. Dates are YYYY-MM-DD; numbers are bare
numbers. Where `options` is listed, use only those values. Write it to ./response.json, or print only that JSON object.
```json
{json.dumps(v['answer_fields'], ensure_ascii=False, indent=1)}
```
"""


# ---------- answer parsing
def extract_json(text):
    """Last fenced JSON block, else the last top-level JSON object in the text."""
    for block in reversed(re.findall(r"```(?:json)?\s*\n(.*?)```", text, re.S)):
        try:
            v = json.loads(block)
            if isinstance(v, dict):
                return v
        except ValueError:
            pass
    dec, found, i = json.JSONDecoder(), None, 0
    while True:
        i = text.find("{", i)
        if i < 0:
            return found
        try:
            v, end = dec.raw_decode(text, i)
            if isinstance(v, dict):
                found = v
            i = end
        except ValueError:
            i += 1


def get_path(obj, path):
    for part in path.split("."):
        if not isinstance(obj, dict) or part not in obj:
            return None
        obj = obj[part]
    return obj


def norm(x):
    return str(x).strip().casefold()


def to_number(x):
    if isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        try:
            return float(re.sub(r"[,\s]|HK\$|m²|%", "", x))
        except ValueError:
            return None
    return None


# ---------- check scoring (each returns score in [0, 1], detail)
def score_check(c, resp, resp_dir=None):
    t = c["type"]
    if t == "absent":
        hit = re.search(c["pattern"], json.dumps(resp, ensure_ascii=False), re.I | re.S)
        return (0.0, f"forbidden content: {hit.group(0)[:60]!r}") if hit else (1.0, "ok")
    if t == "dxf":
        return score_dxf(c, resp_dir)
    got = get_path(resp, c["path"])
    if got is None:
        return 0.0, "missing"
    exp = c.get("expected")
    if t == "number":
        n = to_number(got)
        if n is None:
            return 0.0, f"not a number: {got!r}"
        tol = c.get("tol", abs(exp) * c["pct"] / 100 if "pct" in c else 0.01)
        return (1.0, "ok") if abs(n - exp) <= tol else (0.0, f"got {n:g}, expected {exp:g} ±{tol:g}")
    if t == "bool":
        return (1.0, "ok") if got is exp else (0.0, f"got {got!r}, expected {exp!r}")
    if t in ("enum", "date"):
        return (1.0, "ok") if norm(got) == norm(exp) else (0.0, f"got {got!r}, expected {exp!r}")
    if t == "set":
        if not isinstance(got, list):
            return 0.0, f"not a list: {got!r}"
        g, e = {norm(x) for x in got}, {norm(x) for x in exp}
        if not e:
            return (1.0, "ok") if not g else (0.0, f"false positives: {sorted(g)}")
        tp = len(g & e)
        f1 = 2 * tp / (len(g) + len(e)) if g or e else 1.0
        if f1 == 1.0:
            return 1.0, "ok"
        return f1, f"missed {sorted(e - g)}; false positives {sorted(g - e)}"
    if t == "text":
        missing = [p for p in c["patterns"] if not re.search(p, str(got), re.I | re.S)]
        return (1.0, "ok") if not missing else (0.0, f"missing concept(s): {missing}")
    raise ValueError(f"Unknown check type {t}")


def score_dxf(c, resp_dir):
    """Returns (None, reason) when the drawing tools are not installed, so the check is left out rather than failed."""
    try:
        sys.path.insert(0, str(ROOT / "tools"))
        import dxf_area_takeoff
    except ImportError as e:
        return None, f"skipped: {e}"
    f = Path(resp_dir or ".") / c["file"]
    if not f.is_file():
        return 0.0, f"{c['file']} not produced"
    try:
        rows, warns, _ = dxf_area_takeoff.run(str(f), c["layers"])
    except Exception as e:  # any unreadable drawing is a failed artifact, not a crash of the scorer
        return 0.0, f"unreadable DXF: {e}"
    got = {norm(r["name"]): r["area_m2"] for r in rows}
    ok, bad = 0, []
    for name, area in c["expected_rooms"].items():
        a = got.get(norm(name))
        if a is not None and abs(a - area) <= area * c.get("pct", 1) / 100:
            ok += 1
        else:
            bad.append(f"{name}: got {a}, expected {area}")
    extra = len(got) - len({norm(n) for n in c["expected_rooms"]} & set(got))
    if extra:
        bad.append(f"{extra} extra room outline(s)")
    return ok / (len(c["expected_rooms"]) + extra), "; ".join(bad + warns) or "ok"


def score_task(task, resp, resp_dir=None):
    results, total, weight, critical = [], 0.0, 0.0, []
    for c in task["checks"]:
        s, detail = score_check(c, resp or {}, resp_dir)
        label = c.get("path") or c.get("file") or c["id"]
        results.append({"check": label, "score": s, "detail": detail, "critical": bool(c.get("critical"))})
        if s is None:
            continue
        w = c.get("weight", 1.0)
        total += s * w
        weight += w
        if c.get("critical") and s < 1.0:
            critical.append(f"{task['id']}.{label}: {detail}")
    return {"id": task["id"], "title": task["title"], "stage": task["stage"], "capability": task["capability"],
            "score": total / weight if weight else None, "critical_failures": critical, "checks": results}


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def score_run(run_dir, ids=None):
    run_dir = Path(run_dir)
    meta_file = run_dir / "run.json"
    meta = json.loads(meta_file.read_text(encoding="utf-8")) if meta_file.exists() else {}
    tasks = load_tasks(ids or meta.get("tasks"))
    results = []
    for t in tasks:
        d = run_dir / t["id"]
        resp = None
        f = d / "response.json"
        if f.exists():
            try:
                resp = json.loads(f.read_text(encoding="utf-8"))
            except ValueError:
                resp = None
        r = score_task(t, resp if isinstance(resp, dict) else None, d)
        r["answered"] = isinstance(resp, dict)
        results.append(r)
    by_stage = {s: mean([r["score"] for r in results if r["stage"] == s]) for s in sorted({r["stage"] for r in results})}
    caps = sorted({r["capability"] for r in results})
    by_cap = {c: mean([r["score"] for r in results if r["capability"] == c]) for c in caps}
    overall = mean(by_stage.values())  # stages weigh equally, however many tasks each has
    critical = [c for r in results for c in r["critical_failures"]]
    complete = set(by_stage) == set(STAGES) and not ids and not meta.get("partial")
    reasons = []
    if overall < GATES["overall"]:
        reasons.append(f"overall {overall:.1%} < {GATES['overall']:.0%}")
    reasons += [f"stage {s} {v:.1%} < {GATES['stage']:.0%}" for s, v in by_stage.items() if v < GATES["stage"]]
    if critical:
        reasons.append(f"{len(critical)} critical failure(s)")
    if not complete:
        reasons.append("partial run: no verdict")
    verdict = "PARTIAL" if not complete else ("PASS" if not reasons else "FAIL")
    return {"meta": meta, "overall": overall, "by_stage": by_stage, "by_capability": by_cap, "critical_failures": critical,
            "verdict": verdict, "reasons": reasons, "tasks": results,
            "answered": sum(r["answered"] for r in results), "total": len(results)}


def report_md(s, title):
    pct = lambda x: "n/a" if x is None else f"{x:.1%}"
    m = s["meta"]
    out = [f"# ArchBench: {title}", "",
           f"**{s['verdict']}: {pct(s['overall'])}** ({s['answered']}/{s['total']} tasks answered"
           f", mode `{m.get('mode', 'n/a')}`)", ""]
    if s["reasons"]:
        out += ["Why: " + "; ".join(s["reasons"]) + ".", ""]
    out += ["Gates are provisional, not calibrated against human architects. A pass does not make any output fit to sign.", "",
            "| Stage | Score |", "| --- | --- |"]
    out += [f"| {k} {STAGES[k]} | {pct(v)} |" for k, v in s["by_stage"].items()]
    out += ["", "| Capability | Score |", "| --- | --- |"]
    out += [f"| {k} | {pct(v)} |" for k, v in s["by_capability"].items()]
    if s["critical_failures"]:
        out += ["", "## Critical failures", ""] + [f"- {c}" for c in s["critical_failures"]]
    out += ["", "## Tasks", "", "| Task | Stage | Capability | Score | Lost marks |", "| --- | --- | --- | --- | --- |"]
    for r in s["tasks"]:
        lost = "; ".join(f"`{c['check']}` {c['detail']}" for c in r["checks"] if c["score"] is None or c["score"] < 1)
        lost = lost.replace("|", "\\|").replace("\n", " ")[:600]
        out.append(f"| {r['id']} {r['title']} | {r['stage']} | {r['capability']} | {pct(r['score'])} | {lost} |")
    return "\n".join(out) + "\n"


# ---------- commands
def cmd_list(a):
    for t in load_tasks():
        crit = " [critical]" if any(c.get("critical") for c in t["checks"]) else ""
        print(f"{t['id']}  S{t['stage']}  {t['capability']:<16} {t['title']}{crit}")
    print(f"\n{len(load_tasks())} tasks")


def cmd_export(a):
    out = Path(a.out)
    for t in load_tasks():
        d = out / t["id"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "TASK.md").write_text(task_markdown(t, a.mode), encoding="utf-8")
        (d / "input.json").write_text(json.dumps(t.get("input", {}), ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Exported {len(load_tasks())} tasks to {out} (no answer keys)")


def run_dir_for(a):
    return Path(a.out) if a.out else RUNS_DIR / a.name


def write_meta(run_dir, **kw):
    meta = {"date": date.today().isoformat(), **kw}
    (run_dir / "run.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")


def cmd_run(a):
    ids = a.tasks.split(",") if a.tasks else None
    tasks = load_tasks(ids)
    run_dir = run_dir_for(a)
    run_dir.mkdir(parents=True, exist_ok=True)
    write_meta(run_dir, name=a.name, agent_cmd=a.agent_cmd, mode=a.mode, tasks=[t["id"] for t in tasks], partial=bool(ids))
    for t in tasks:
        with tempfile.TemporaryDirectory(prefix="archbench-") as tmp:
            ws = Path(tmp)
            if a.mode == "kb":
                shutil.copytree(ROOT, ws / "kb", ignore=shutil.ignore_patterns(*KB_EXCLUDE))
            prompt = task_markdown(t, a.mode)
            (ws / "TASK.md").write_text(prompt, encoding="utf-8")
            (ws / "input.json").write_text(json.dumps(t.get("input", {}), ensure_ascii=False, indent=1), encoding="utf-8")
            start, status, out = time.time(), "ok", ""
            try:
                p = subprocess.run(a.agent_cmd, shell=True, cwd=ws, input=prompt, capture_output=True, text=True, timeout=a.timeout)
                out = p.stdout + ("\n[stderr]\n" + p.stderr if p.stderr else "")
                if p.returncode:
                    status = f"exit {p.returncode}"
                stdout = p.stdout
            except subprocess.TimeoutExpired as e:
                status, stdout = "timeout", e.stdout.decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
                out = stdout
            d = run_dir / t["id"]
            d.mkdir(exist_ok=True)
            (d / "stdout.txt").write_text(out, encoding="utf-8")
            resp = None
            if (ws / "response.json").exists():
                try:
                    resp = json.loads((ws / "response.json").read_text(encoding="utf-8"))
                except ValueError:
                    status += ", invalid response.json"
            if not isinstance(resp, dict):
                resp = extract_json(stdout)
            if resp is not None:
                (d / "response.json").write_text(json.dumps(resp, ensure_ascii=False, indent=1), encoding="utf-8")
            for c in t["checks"]:
                if c.get("file") and (ws / c["file"]).is_file():
                    shutil.copy(ws / c["file"], d / c["file"])
            secs = round(time.time() - start, 1)
            (d / "meta.json").write_text(json.dumps({"status": status, "seconds": secs}), encoding="utf-8")
            print(f"{t['id']}: {status}, {secs}s, {'answered' if resp is not None else 'NO ANSWER'}", flush=True)
    finish(run_dir, a.name)


def gold_response(task):
    r = {}
    for c in task["checks"]:
        if c["type"] in ("absent", "dxf"):
            continue
        cur = r
        parts = c["path"].split(".")
        for p in parts[:-1]:
            cur = cur.setdefault(p, {})
        cur[parts[-1]] = c.get("gold") if c["type"] == "text" else c["expected"]
    return r


def naive_response(task):
    """An overconfident agent: first option everywhere, finds no problems, computes nothing."""
    r = {}
    filler = {"number": 0, "bool": True, "date": "2000-01-01", "set": [], "text": "OK"}
    for c in task["checks"]:
        if c["type"] in ("absent", "dxf"):
            continue
        cur = r
        parts = c["path"].split(".")
        for p in parts[:-1]:
            cur = cur.setdefault(p, {})
        cur[parts[-1]] = c["options"][0] if c["type"] == "enum" else filler[c["type"]]
    return r


def write_gold_dxf(task, d):
    """Draws the rooms given in the input, so the gold baseline also covers the artifact check."""
    try:
        import ezdxf
    except ImportError:
        return
    for c in task["checks"]:
        if c["type"] != "dxf":
            continue
        doc = ezdxf.new()
        doc.header["$INSUNITS"] = 4
        msp = doc.modelspace()
        for room in task["input"]["rooms"]:
            pts = [(x * 1000, y * 1000) for x, y in room["polygon"]]
            msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "A-ROOM"})
            lx, ly = room["label_point"]
            msp.add_text(room["name"], dxfattribs={"layer": "A-ROOM", "insert": (lx * 1000, ly * 1000)})
        doc.saveas(d / c["file"])


def cmd_baseline(a):
    run_dir = run_dir_for(a)
    run_dir.mkdir(parents=True, exist_ok=True)
    tasks = load_tasks()
    write_meta(run_dir, name=a.name, agent_cmd=f"baseline:{a.which}", mode="baseline", tasks=[t["id"] for t in tasks], partial=False)
    for t in tasks:
        d = run_dir / t["id"]
        d.mkdir(exist_ok=True)
        if a.which == "blank":
            continue
        resp = gold_response(t) if a.which == "gold" else naive_response(t)
        (d / "response.json").write_text(json.dumps(resp, ensure_ascii=False, indent=1), encoding="utf-8")
        if a.which == "gold":
            write_gold_dxf(t, d)
    finish(run_dir, a.name)


def finish(run_dir, title):
    s = score_run(run_dir)
    (run_dir / "report.md").write_text(report_md(s, title), encoding="utf-8")
    (run_dir / "report.json").write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n{title}: {s['verdict']} {s['overall']:.1%}; {len(s['critical_failures'])} critical; report: {run_dir / 'report.md'}")
    return s


def cmd_score(a):
    d = Path(a.run_dir)
    if not d.is_dir():
        raise SystemExit(f"No such run directory: {d}")
    s = finish(d, a.title or d.name)
    sys.stdout.write("\n" + report_md(s, a.title or d.name))


def cmd_compare(a):
    runs = [(Path(d).name, score_run(d)) for d in a.run_dirs]
    pct = lambda x: "n/a" if x is None else f"{x:.1%}"
    head = "| Metric | " + " | ".join(n for n, _ in runs) + " |"
    rows = [head, "| --- |" + " --- |" * len(runs),
            "| Verdict | " + " | ".join(s["verdict"] for _, s in runs) + " |",
            "| Overall | " + " | ".join(pct(s["overall"]) for _, s in runs) + " |",
            "| Critical failures | " + " | ".join(str(len(s["critical_failures"])) for _, s in runs) + " |"]
    for k in STAGES:
        rows.append(f"| Stage {k} | " + " | ".join(pct(s["by_stage"].get(k)) for _, s in runs) + " |")
    for c in sorted({c for _, s in runs for c in s["by_capability"]}):
        rows.append(f"| {c} | " + " | ".join(pct(s["by_capability"].get(c)) for _, s in runs) + " |")
    print("\n".join(rows))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    p = sub.add_parser("export")
    p.add_argument("--out", required=True)
    p.add_argument("--mode", choices=["closed", "kb"], default="closed")
    p.set_defaults(fn=cmd_export)
    p = sub.add_parser("run", help="run an agent command once per task; the prompt arrives on stdin")
    p.add_argument("--name", required=True)
    p.add_argument("--agent-cmd", required=True)
    p.add_argument("--mode", choices=["closed", "kb"], default="closed")
    p.add_argument("--tasks", help="comma-separated ids; a partial run gets no verdict")
    p.add_argument("--timeout", type=int, default=600)
    p.add_argument("--out")
    p.set_defaults(fn=cmd_run)
    p = sub.add_parser("baseline", help="gold = answer key, naive = overconfident, blank = no answers")
    p.add_argument("which", choices=["gold", "naive", "blank"])
    p.add_argument("--name", required=True)
    p.add_argument("--out")
    p.set_defaults(fn=cmd_baseline)
    p = sub.add_parser("score")
    p.add_argument("run_dir")
    p.add_argument("--title")
    p.set_defaults(fn=cmd_score)
    p = sub.add_parser("compare")
    p.add_argument("run_dirs", nargs="+")
    p.set_defaults(fn=cmd_compare)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
