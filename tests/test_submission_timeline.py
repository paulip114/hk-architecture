"""Tests for tools/submission_timeline.py against the statutory periods in submission/periods.json.

Run:  python3 -m unittest discover -s tests
"""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("submission_timeline", ROOT / "tools" / "submission_timeline.py")
st = importlib.util.module_from_spec(spec)
spec.loader.exec_module(st)


def rows(sub):
    out, _ = st.check(dict(sub, as_of="2026-11-05"))
    return out


def find(rs, text):
    return [r for r in rs if text in r[1]]


class Periods(unittest.TestCase):
    def test_statutory_periods(self):
        P = st.PER
        self.assertEqual(P["gbp_first"]["days"], 60)            # B(A)R 30(3)(a)
        self.assertEqual(P["gbp_major_revision"]["days"], 60)   # B(A)R 30(3)(b)
        self.assertEqual(P["gbp_resubmission"]["days"], 30)     # B(A)R 30(3)(c)
        self.assertEqual(P["consent"]["days"], 28)              # B(A)R 32(3)
        self.assertEqual(P["amendment"]["days"], 28)            # B(A)R 33(2)
        self.assertEqual(P["op"]["days"], 14)                   # BO s.21(7)
        self.assertEqual(P["consent_lapse"]["months"], 3)       # BO s.20(1)
        self.assertEqual(P["ba10_before_commencement"]["days"], 7)  # B(A)R 20(1)

    def test_all_verified(self):
        self.assertEqual([k for k, v in st.PER.items() if not v["verified"]], [])


class Checks(unittest.TestCase):
    def test_first_submission_due_date(self):
        r = find(rows({"submissions": [{"id": "A", "type": "first", "date": "2026-01-01"}]}), "Refusal due by")[0]
        self.assertIn("2026-03-02", r[1])

    def test_wr_restarts_and_limit(self):
        rs = rows({"submissions": [{"id": "A", "type": "resubmission", "date": "2026-01-01",
                                    "wr_dates": ["2026-01-20", "2026-02-10", "2026-03-01"]}]})
        self.assertEqual(find(rs, "Withdrawal")[0][2], st.FAIL)
        self.assertIn("2026-03-31", find(rs, "Refusal due by")[0][1])

    def test_ba10_short_notice_fails(self):
        rs = rows({"consents": [{"id": "C", "applied": "2026-01-01", "granted": "2026-01-20"}],
                   "commencement": {"date": "2026-02-01", "ba10_date": "2026-01-28"}})
        self.assertEqual(find(rs, "BA10")[0][2], st.FAIL)

    def test_consent_lapse(self):
        rs = rows({"consents": [{"id": "C", "applied": "2026-01-01", "granted": "2026-01-31"}],
                   "commencement": {"date": "2026-05-01", "ba10_date": "2026-04-20"}})
        self.assertEqual(find(rs, "Consent lapse")[0][2], st.FAIL)
        rs = rows({"consents": [{"id": "C", "applied": "2026-01-01", "granted": "2026-01-31"}],
                   "commencement": {"date": "2026-04-30", "ba10_date": "2026-04-20"}})
        self.assertFalse(find(rs, "Consent lapse"))

    def test_op_deemed(self):
        r = find(rows({"op": {"applied": "2026-11-01", "prereq": {}}}), "Refusal due by")[0]
        self.assertIn("2026-11-16", r[1])

    def test_ap_completion_certificate(self):
        rs = rows({"completion": {"date": "2026-10-01", "rc_cert_date": "2026-10-08", "ap_cert_date": "2026-10-16"}})
        self.assertEqual(find(rs, "RC certificate")[0][2], st.PASS)
        self.assertEqual(find(rs, "AP certificate")[0][2], st.FAIL)

    def test_demo_runs(self):
        demo = json.loads((ROOT / "examples" / "demo_submission.json").read_text(encoding="utf-8"))
        self.assertTrue(rows(demo["submission"]))



class Cap1Section71(unittest.TestCase):
    def consent_due(self, applied, **kw):
        sub = {"consents": [{"id": "C", "applied": applied}], **kw}
        return next(r[1] for r in rows(sub) if r[1].startswith("Consent due"))

    def test_last_day_on_sunday_moves_to_monday(self):
        # 2027-01-03 + 28 days = 2027-01-31, a Sunday
        self.assertIn("2027-02-01", self.consent_due("2027-01-03"))

    def test_last_day_on_general_holiday_moves(self):
        # 2026-11-27 + 28 days = 2026-12-25, followed by 26 December and Sunday 27 December
        self.assertIn("2026-12-28", self.consent_due("2026-11-27"))

    def test_warning_day_moves_the_last_day(self):
        # 2027-01-01 + 28 days = 2027-01-29, a Friday
        self.assertIn("2027-01-29", self.consent_due("2027-01-01"))
        self.assertIn("2027-01-30", self.consent_due("2027-01-01", warning_days=["2027-01-29"]))

    def test_pnap_targets_do_not_move(self):
        self.assertEqual(st.plus(st.d("2027-01-03"), "fast_track_aa"), st.d("2027-02-02"))
        self.assertEqual(st.plus(st.d("2026-12-17"), "enquiry_45th_day"), st.d("2027-01-31"))

    def test_holiday_list_covers_a_stated_year(self):
        self.assertGreaterEqual(st.HOLIDAYS["covered_to_year"], 2026)
        self.assertIn("2026-12-25", st.HOLIDAYS["general_holidays"])


if __name__ == "__main__":
    unittest.main()
