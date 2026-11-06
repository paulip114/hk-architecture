"""Tests for ArchBench: answer keys stay tied to the repo tools, keys never reach the agent, and the scorer discriminates.

Run:  python3 -m unittest discover -s tests
"""
import contextlib
import importlib.util
import io
import json
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "benchmark"))

import anchors  # noqa: E402
import archbench as ab  # noqa: E402

TASKS = ab.load_tasks()
HAS_DXF = all(importlib.util.find_spec(m) for m in ("ezdxf", "shapely"))


def scored(check, resp):
    return ab.score_check(check, resp)[0]


def baseline(which, tmp):
    args = type("A", (), {"which": which, "name": which, "out": str(Path(tmp) / which)})
    ab.cmd_baseline(args)
    return ab.score_run(Path(tmp) / which)


class Keys(unittest.TestCase):
    def test_tasks_are_well_formed(self):
        self.assertEqual(len({t["id"] for t in TASKS}), len(TASKS))
        self.assertEqual({t["stage"] for t in TASKS}, set(ab.STAGES))
        for t in TASKS:
            self.assertTrue(t.get("source"), t["id"])
            for c in t["checks"]:
                if c["type"] == "enum":
                    self.assertIn(c["expected"], c["options"], t["id"])
                if c["type"] == "set" and "options" in c:
                    self.assertLessEqual(set(c["expected"]), set(c["options"]), t["id"])

    def test_keys_equal_independent_recomputation(self):
        for t in TASKS:
            fn = anchors.ANCHORS.get(t["id"])
            if not fn:
                continue
            got = fn(t["input"])
            for c in t["checks"]:
                if c["type"] == "text" or c.get("judgement"):
                    continue
                with self.subTest(task=t["id"], check=c.get("path") or c.get("id")):
                    if c["type"] == "dxf":
                        for room, area in c["expected_rooms"].items():
                            self.assertAlmostEqual(got[f"dxf.{room}"], area, places=2)
                    elif t["id"] == "D05":
                        self.assertAlmostEqual(sum(got.values()), c["expected"], places=2)
                    elif c["type"] == "number":
                        self.assertAlmostEqual(float(got[c["path"]]), c["expected"], delta=max(abs(c["expected"]) * 1e-4, 0.006))
                    elif c["type"] == "set":
                        self.assertEqual(sorted(got[c["path"]]), sorted(c["expected"]))
                    else:
                        self.assertEqual(got[c["path"]], c["expected"])

    def test_unanchored_tasks_are_declared_judgement(self):
        for t in TASKS:
            if t["id"] not in anchors.ANCHORS:
                self.assertTrue(t["source"].startswith("Judgement"), t["id"])


class NoLeak(unittest.TestCase):
    def test_public_view_has_no_answers(self):
        for t in TASKS:
            v = ab.public_view(t)
            for f in v["answer_fields"]:
                self.assertFalse({"expected", "gold", "patterns", "expected_rooms", "judgement"} & set(f), t["id"])
            self.assertNotIn("source", v)
            self.assertNotIn("checks", v)

    def test_export_contains_no_key_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            ab.cmd_export(type("A", (), {"out": tmp, "mode": "closed"}))
            text = "".join(p.read_text(encoding="utf-8") for p in Path(tmp).rglob("*") if p.is_file())
        for word in ('"expected"', '"gold"', '"patterns"', '"source"', "expected_rooms"):
            self.assertNotIn(word, text)


class Scoring(unittest.TestCase):
    def test_number(self):
        c = {"path": "x", "type": "number", "expected": 1000, "pct": 0.5}
        self.assertEqual(scored(c, {"x": 1004}), 1)
        self.assertEqual(scored(c, {"x": "HK$1,004"}), 1)
        self.assertEqual(scored(c, {"x": 1030}), 0)
        self.assertEqual(scored(c, {}), 0)
        self.assertEqual(scored(c, {"x": True}), 0)

    def test_bool_is_strict(self):
        c = {"path": "x", "type": "bool", "expected": False}
        self.assertEqual(scored(c, {"x": False}), 1)
        self.assertEqual(scored(c, {"x": "false"}), 0)
        self.assertEqual(scored(c, {"x": 0}), 0)

    def test_set_penalises_misses_and_false_positives(self):
        c = {"path": "x", "type": "set", "expected": ["a", "b"]}
        self.assertEqual(scored(c, {"x": ["B", "a"]}), 1)
        self.assertAlmostEqual(scored(c, {"x": ["a"]}), 2 / 3)
        self.assertAlmostEqual(scored(c, {"x": ["a", "b", "c", "d"]}), 2 / 3)
        self.assertEqual(scored(c, {"x": []}), 0)
        self.assertEqual(scored({"path": "x", "type": "set", "expected": []}, {"x": ["z"]}), 0)

    def test_nested_path_and_absent(self):
        self.assertEqual(scored({"path": "a.b", "type": "enum", "expected": "Q"}, {"a": {"b": "q"}}), 1)
        self.assertEqual(scored({"id": "n", "type": "absent", "pattern": "secret"}, {"x": "a SECRET"}), 0)

    def test_critical_failure_fails_the_run_whatever_the_score(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "r"
            ab.cmd_baseline(type("A", (), {"which": "gold", "name": "r", "out": str(run)}))
            f = run / "D06" / "response.json"
            bad = json.loads(f.read_text(encoding="utf-8"))
            bad["decision"] = "sign_as_ap"
            f.write_text(json.dumps(bad), encoding="utf-8")
            s = ab.score_run(run)
            self.assertGreater(s["overall"], 0.95)
            self.assertEqual(s["verdict"], "FAIL")


class Baselines(unittest.TestCase):
    def test_scores_separate_gold_naive_blank(self):
        with tempfile.TemporaryDirectory() as tmp:
            gold, naive, blank = (baseline(w, tmp) for w in ("gold", "naive", "blank"))
        self.assertEqual(gold["verdict"], "PASS")
        self.assertEqual(gold["overall"], 1.0)
        self.assertEqual(gold["critical_failures"], [])
        self.assertEqual(naive["verdict"], "FAIL")
        self.assertLess(naive["overall"], 0.25)
        self.assertGreaterEqual(len(naive["critical_failures"]), 5)
        self.assertEqual(blank["overall"], 0)

    def test_small_error_in_a_key_number_loses_marks(self):
        t = next(t for t in TASKS if t["id"] == "F06")
        resp = ab.gold_response(t)
        resp["total_cost_hkd"] *= 1.03
        self.assertLess(ab.score_task(t, resp)["score"], 1)

    @unittest.skipUnless(HAS_DXF, "ezdxf / shapely not installed")
    def test_dxf_artifact_is_measured(self):
        t = next(t for t in TASKS if t["id"] == "D05")
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            self.assertEqual(ab.score_task(t, {"total_area_m2": 108}, d)["score"], 0.25)   # no file: only the typed answer
            ab.write_gold_dxf(t, d)
            self.assertEqual(ab.score_task(t, {"total_area_m2": 108}, d)["score"], 1)
            import ezdxf
            doc = ezdxf.readfile(d / "plan.dxf")
            doc.header["$INSUNITS"] = 6    # declare metres while the geometry is in mm: areas are a million times out
            doc.saveas(d / "plan.dxf")
            self.assertEqual(ab.score_task(t, {"total_area_m2": 108}, d)["score"], 0.25)


class HumanReview(unittest.TestCase):
    def write(self, tmp, **change):
        review = json.loads((ROOT / "benchmark" / "rubric" / "example-scores.json").read_text(encoding="utf-8"))
        review.update(change)
        f = Path(tmp) / "scores.json"
        f.write_text(json.dumps(review), encoding="utf-8")
        return f

    def test_weighted_score(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(ab.human_review(self.write(tmp))["score"], 0.5)   # every criterion 2 of 4

    def test_rejects_bad_marks(self):
        with tempfile.TemporaryDirectory() as tmp:
            good = json.loads((ROOT / "benchmark" / "rubric" / "example-scores.json").read_text(encoding="utf-8"))["scores"]
            for bad in (5, -1, 2.5, True):
                with self.assertRaises(SystemExit):
                    ab.human_review(self.write(tmp, scores={**good, "communication": bad}))
            with self.assertRaises(SystemExit):
                ab.human_review(self.write(tmp, reviewer=""))

    def test_human_score_does_not_change_the_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "r"
            ab.cmd_baseline(type("A", (), {"which": "naive", "name": "r", "out": str(run)}))
            f = self.write(tmp, scores={k: 4 for k in json.loads(self.write(tmp).read_text(encoding="utf-8"))["scores"]})
            with contextlib.redirect_stdout(io.StringIO()):   # the report has Chinese, and main() is what sets UTF-8
                ab.cmd_score(type("A", (), {"run_dir": str(run), "title": "t", "human": str(f)}))
            s = json.loads((run / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(s["verdict"], "FAIL")
            self.assertEqual(s["human_review"]["score"], 1.0)
            self.assertIn("Human review", (run / "report.md").read_text(encoding="utf-8"))


class Extract(unittest.TestCase):
    def test_extract_json(self):
        self.assertEqual(ab.extract_json('text\n```json\n{"a": 1}\n```\nmore'), {"a": 1})
        self.assertEqual(ab.extract_json('thinking {"a": 1} then {"b": {"c": 2}} done'), {"b": {"c": 2}})
        self.assertIsNone(ab.extract_json("no json here {oops"))


FAKE_AGENT = r'''
import json, re, sys
prompt = sys.stdin.read()
tid = re.search(r"\(([A-Z]\d\d)\)", prompt).group(1)
if tid == "T03":
    open("response.json", "w").write(json.dumps({"form": {"bq": "SFBCwQ.2005", "no_bq": "SFBCnQ.2006"}}))
elif tid == "T01":
    print("Here is my answer:\n```json\n" + json.dumps({"hard_clashes": ["B1|D1"]}) + "\n```")
elif tid == "T04":
    print("sorry, no answer")
assert "expected" not in prompt and "gold" not in prompt
'''


class Runner(unittest.TestCase):
    def test_agent_command_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "fake_agent.py"
            script.write_text(FAKE_AGENT, encoding="utf-8")
            run = Path(tmp) / "run"
            cmd = f"{shlex.quote(sys.executable)} {shlex.quote(str(script))}"
            r = subprocess.run([sys.executable, str(ROOT / "benchmark" / "archbench.py"), "run", "--name", "fake", "--agent-cmd", cmd,
                                "--tasks", "T01,T03,T04", "--out", str(run)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            s = json.loads((run / "report.json").read_text(encoding="utf-8"))
        by = {t["id"]: t for t in s["tasks"]}
        self.assertEqual(by["T03"]["score"], 1)
        self.assertEqual(by["T01"]["score"], 0.5)         # F1 of 1 of 3 clashes
        self.assertFalse(by["T04"]["answered"])
        self.assertEqual(s["verdict"], "PARTIAL")


if __name__ == "__main__":
    unittest.main()
