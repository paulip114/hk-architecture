"""Recomputes answer keys independently of the literal values stored in tasks/*.json.

ANCHORS[task_id](task_input) returns {answer_path: value}. tests/test_benchmark.py requires these to equal the stored keys,
so a change to a repo tool or rule table that moves a key fails the tests instead of silently changing what is "correct".
Tasks with no repo tool (clash detection, tender evaluation, finishes coordination) are recomputed from first principles here.
Checks marked "judgement" in a task have no anchor: they were reviewed by hand and cite their source in the task's `source`.
"""
import copy
import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import bpr_check  # noqa: E402
import contract_admin  # noqa: E402
import cost_estimate  # noqa: E402
import massing_study  # noqa: E402
import moe_check  # noqa: E402
import planning_lease_check  # noqa: E402
import submission_timeline as st  # noqa: E402
import supervision_plan  # noqa: E402

FORMS = json.loads((ROOT / "submission" / "forms.json").read_text(encoding="utf-8"))
PERIODS = json.loads((ROOT / "submission" / "periods.json").read_text(encoding="utf-8"))
PLANNING = json.loads((ROOT / "planning" / "planning_lands.json").read_text(encoding="utf-8"))
SFBC = json.loads((ROOT / "contracts" / "sfbc.json").read_text(encoding="utf-8"))
ROOM_CHECKS = {"glass": "glass", "openable": "openable", "top of opening": "head",
               "furthest point": "distance", "floor-to-ceiling": "ceiling"}
MOE_CHECKS = {"number of exit routes": "exit_count", "total exit route width": "exit_width",
              "narrowest exit route": "exit_narrow", "max travel distance": "travel", "deadend travel": "deadend",
              "distance between stair doors": "stair_door_sep", "risers per flight": "risers"}


def bpr(i):
    return bpr_check.run(copy.deepcopy(i))


def add_months(day, n):
    m = day.month - 1 + n
    return date(day.year + m // 12, m % 12 + 1, day.day)


def room_failures(i):
    out = []
    for r in bpr(i)[0]:
        if r[4] == "FAIL":
            for name in (x["name"] for x in i["rooms"]):
                if r[1].startswith(name + " ("):
                    out.append(f"{name}|{next(v for k, v in ROOM_CHECKS.items() if k in r[1])}")
    return sorted(out)


def f01(i):
    cls, _ = bpr_check.classify_site(i["site"])
    h, area = i["building"]["height_m"], i["site"]["area_m2"]
    pr = bpr_check.limit("domestic", "plot_ratio", cls, h)
    candidates = {"schedule": pr * area, "ozp": i["limits"]["ozp_max_pr_domestic"] * area, "lease": i["lease"]["max_gfa_m2"]}
    gov = min(candidates, key=candidates.get)
    return {"site_class": cls, "schedule_pr": pr, "schedule_max_gfa_m2": candidates["schedule"],
            "ozp_max_gfa_m2": candidates["ozp"], "governing_max_gfa_m2": candidates[gov], "governing_constraint": gov,
            "top_band_sc_pct": bpr_check.limit("domestic", "site_coverage_pct", cls, h)}


def f02(i):
    return {f"class.{k}": bpr_check.classify_site(v)[0] for k, v in i["sites"].items()}


def f03(i):
    cls, h, area = i["site"]["class"], i["building"]["height_m"], i["site"]["area_m2"]
    pd, pn = bpr_check.limit("domestic", "plot_ratio", cls, h), bpr_check.limit("non_domestic", "plot_ratio", cls, h)
    dn = i["non_domestic_gfa_m2"] / area
    formula = pd * (1 - dn / pn)
    capped = min(formula, i["ozp_max_pr_total"] - dn)
    return {"pd": pd, "pn": pn, "dn": dn, "max_domestic_pr_formula": round(formula, 3), "max_domestic_pr_final": round(capped, 3),
            "max_domestic_gfa_m2": round(capped * area, 2), "governing_constraint": "ozp_total" if capped < formula else "reg21_formula"}


def f04(i):
    rows, _, _, gfa = bpr(i)
    gross = sum(f["gross_area_m2"] * f.get("count", 1) for f in i["floors"])
    halves = sum(e["area_m2"] * 0.5 * f.get("count", 1) for f in i["floors"] for e in f.get("exempt", [])
                 if e["category"] == "car_park_above_50")
    return {"gross_area_m2": gross, "accountable_gfa_m2": gfa, "plot_ratio": gfa / i["site"]["area_m2"],
            "pr_limit": bpr_check.limit("non_domestic", "plot_ratio", i["site"]["class"], i["building"]["height_m"]),
            "car_park_above_50_disregarded_m2": halves, "complies": not [r for r in rows if r[4] == "FAIL"]}


def f05(i):
    rows, _, needs = planning_lease_check.run(copy.deepcopy(i["project"]), copy.deepcopy(i["planning_lease"]))
    q = i["planning_lease"]
    c2 = {u.lower() for u in q["ozp"]["column2_uses"]}
    height = next(r[2] for r in rows if r[1] == "Building height")
    return {"s16_required": bool(needs["s16"]), "s12a_required": bool(needs["s12A"]), "lease_modification_required": bool(needs["lease_mod"]),
            "column2_uses": [u for u in q["proposal"]["uses"] if u.lower() in c2],
            "uses_outside_lease": [u for u in q["proposal"]["uses"] if u not in q["lease"]["user_allows"]],
            "building_height_mpd": float(height.split()[0])}


def f06(i):
    c = cost_estimate.run(copy.deepcopy(i))
    return {"building_works_hkd": c["summary"][0][1], "construction_cost_hkd": c["construction"], "total_cost_hkd": c["total"],
            "construction_cost_per_cfa_hkd": c["construction"] / c["cfa"], "over_budget": c["total"] > i["cost"]["budget"]}


def s01(i):
    return {"failures": room_failures(i)}


def s02(i):
    rows = bpr(i)[0]
    cls, h = i["site"]["class"], i["building"]["height_m"]
    keys = {"Open space": "open_space_area", "Distance from rear boundary": "rear_distance",
            "Open space level below floor of lowermost storey": "open_space_level", "Domestic plot ratio": "plot_ratio"}
    fails = [v for k, v in keys.items() for r in rows if r[1] == k and r[4] == "FAIL"]
    fails += ["site_coverage" for r in rows if r[1].startswith("Site coverage") and r[4] == "FAIL"]
    return {"pr_limit": bpr_check.limit("domestic", "plot_ratio", cls, h), "sc_limit_pct": bpr_check.limit("domestic", "site_coverage_pct", cls, h),
            "required_open_space_m2": bpr_check.SCHEDULE["second_schedule_open_space_fraction_of_roofed_over_area"][cls] * i["open_space"]["roofed_over_area_m2"],
            "failures": sorted(fails)}


def s03(i):
    rows, _ = massing_study.run_options(copy.deepcopy(i))
    ok = [r for r in rows if r[7] == "PASS"]
    best = max(ok, key=lambda r: r[5])
    return {"compliant_options": sorted(r[0] for r in ok), "recommended_option": best[0], "recommended_gfa_m2": best[5]}


def s04(i):
    t = PLANNING["tpb"]
    p = {k: date.fromisoformat(v) for k, v in i.items()}
    return {"s16_comment_end": (p["s16_lodged"] + timedelta(weeks=t["s16_comment_weeks"])).isoformat(),
            "s16_decision_by": add_months(p["s16_lodged"], t["s16_decision_months"]).isoformat(),
            "s17_lodge_by": (p["s16_notified"] + timedelta(days=t["s17_lodge_days"])).isoformat(),
            "s17_decision_by": add_months(p["s17_lodged"], t["s17_decision_months"]).isoformat(),
            "appeal_lodge_by": (p["s17_notified"] + timedelta(days=t["appeal_lodge_days"])).isoformat()}


def d01(i):
    rows, _ = moe_check.run(copy.deepcopy(i))
    codes = {s["name"]: s["code"] for s in i["storeys"]}
    codes.update({s["name"]: s["name"] for s in i["staircases"]})
    out, occ = [], {}
    for r in rows:
        for name, code in sorted(codes.items(), key=lambda x: -len(x[0])):
            if r[1].startswith(name):
                if "occupant capacity" in r[1]:
                    occ[f"occupants.{code}"] = int(r[2])
                elif r[4] == "FAIL":
                    out.append(f"{code}|{next(v for k, v in MOE_CHECKS.items() if k in r[1])}")
                break
    # a failure not tied to a storey or stair (e.g. protected lobby) would be missed above: require none
    assert sum(r[4] == "FAIL" for r in rows) == len(out), "unmapped MoE failure"
    return {"failures": sorted(out), **occ}


def d02(i):
    rows = st.check(copy.deepcopy(i))[0]
    p, c, cp = i["submissions"], i["consents"][0], i["completion"]
    plus = lambda s, k: st.plus(date.fromisoformat(s), k).isoformat()
    out = {"g1_refusal_due": plus(p[0]["date"], "gbp_first"), "g1_45th_day": plus(p[0]["date"], "enquiry_45th_day"),
           "g2_refusal_due": plus(p[1]["wr_dates"][-1], "gbp_resubmission"), "consent_due": plus(c["applied"], "consent"),
           "consent_lapses_after": st.add_months(date.fromisoformat(c["granted"]), PERIODS["periods"]["consent_lapse"]["months"]).isoformat(),
           "ba10_latest": (date.fromisoformat(i["commencement"]["date"]) - timedelta(days=PERIODS["periods"]["ba10_before_commencement"]["days"])).isoformat(),
           "rc_cert_due": plus(cp["date"], "rc_completion_cert"), "ap_cert_due": plus(cp["date"], "ap_completion_cert"),
           "op_refusal_due": plus(i["op"]["applied"], "op")}
    g1 = next(r for r in rows if r[0].startswith("Plans G1") and r[1].startswith("Refusal due"))
    out["g1_result_after_period"] = g1[2] != "PASS"
    return out


def d03(i):
    rows = st.check(copy.deepcopy(i))[0]
    m = {("Consent C1", "Consent lapse"): "consent_lapsed", ("Commencement", "BA10 notice"): "ba10_late",
         ("Commencement", "TCP appointment notice"): "tcp_notice_late", ("Commencement", "Consent before works"): "works_before_consent",
         ("Completion", "RC certificate to AP"): "rc_cert_late", ("Completion", "AP certificate to BA"): "ap_cert_late",
         ("Amendment A1", "Approval before works"): "a1_started_unapproved", ("Amendment A2", "Minor amendment status"): "a2_not_minor",
         ("Amendment A2", "Approval before works"): "a2_started_unapproved", ("Amendment A3", "Minor amendment status"): "a3_not_minor"}
    fails = [m[(r[0], r[1])] for r in rows if r[2] == "FAIL" and (r[0], r[1]) in m]
    assert sum(r[2] == "FAIL" for r in rows) == len(fails), "unmapped submission failure"
    return {"failures": sorted(fails), "lapsed_consent_renewal_form": next(f["form"] for f in FORMS["building_works"] if "renew consent" in f["purpose"])}


def d04(i):
    forms = {f["purpose"]: f["form"] for f in FORMS["building_works"]}
    return {f"form.{k}": forms[v] for k, v in i["_purposes"].items()}


def d05(i):
    def area(poly):
        return abs(sum(poly[k][0] * poly[(k + 1) % len(poly)][1] - poly[(k + 1) % len(poly)][0] * poly[k][1] for k in range(len(poly)))) / 2
    return {f"dxf.{r['name']}": area(r["polygon"]) for r in i["rooms"]}


def d07(i):
    fails = room_failures(i)
    return {"failures": fails, "complies": not fails}


def t01(i):
    es = i["elements"]
    out = []
    for a in range(len(es)):
        for b in range(a + 1, len(es)):
            A, B = es[a], es[b]
            if all(A["min"][k] < B["max"][k] and B["min"][k] < A["max"][k] for k in range(3)):
                out.append("|".join(sorted((A["id"], B["id"]))))
    return {"hard_clashes": sorted(out)}


def t02(i):
    ok = []
    for t in i["tenders"]:
        corrected = sum(t["items"].values())
        if t["bond_provided"] and t["received"] <= i["deadline"] and not t["qualified"]:
            ok.append((corrected, t["id"]))
    best = min(ok)
    corrected = {t["id"]: sum(t["items"].values()) for t in i["tenders"]}
    return {"compliant_tenders": sorted(x[1] for x in ok), "recommended": best[1], "recommended_corrected_sum_hkd": best[0],
            "over_budget_by_hkd": best[0] - i["budget"], **{f"corrected.{k}": v for k, v in corrected.items()}}


def t03(i):
    keys = {f["key"] for f in SFBC["forms"]}
    assert {"SFBCwQ.2005", "SFBCnQ.2006"} <= keys
    return {"form.bq": "SFBCwQ.2005", "form.no_bq": "SFBCnQ.2006"}


def t04(i):
    rooms = {r["id"] for r in i["rooms"]}
    sched = {r["room"] for r in i["finishes_schedule"]}
    return {"rooms_missing_finishes": sorted(rooms - sched), "finishes_for_unknown_rooms": sorted(sched - rooms),
            "doors_under_rated": sorted(d["id"] for d in i["doors"] if d["provided_frp_min"] < d["required_frp_min"])}


def c01(i):
    rows = contract_admin.run(copy.deepcopy(i["contract"]), date.fromisoformat(i["as_of"]))
    val = {r[1]: r for r in rows}
    n = lambda s: float(s.replace("HK$", "").replace(",", "").split()[0])
    ld_pending = val["Pending EOT"][5].split("HK$")[1].replace(",", "")
    return {"extended_completion": val["Extended Completion Date"][2], "delay_days": int(val["Delay beyond extended Completion Date"][2].split()[0]),
            "ld_hkd": n(val["Liquidated damages"][2]), "ld_if_pending_eot_granted_hkd": float(ld_pending),
            "retention_held_hkd": n(val["Retention held"][2]), "half_retention_hkd": n(val["Release ½ retention"][2]),
            "half_retention_release_by": val["Release ½ retention"][2].split(" by ")[1], "dlp_end": val["Defects Liability Period ends"][2]}


def c02(i):
    rows = contract_admin.run(copy.deepcopy(i["contract"]), date.fromisoformat(i["as_of"]))
    refs = ["EOT-A", "EOT-B", "AI-1", "AI-2", "LE-1", "LE-2", "IPA-9", "IPA-10"]
    fails = sorted({next(x for x in refs if r[1].startswith(x + " ")) for r in rows if r[4] == "FAIL"})
    assert sum(r[4] == "FAIL" for r in rows) == len(fails), "unmapped contract failure"
    limit = next(r[3] for r in rows if r[1] == "IPA-10 admitted amount paid")
    return {"late_items": fails, "ipa10_payment_due": limit.split(" by ")[1]}


def c03(i):
    rows = st.check(copy.deepcopy(i))[0]
    names = {"approval and consent for all amendments": "all_amendments_approved", "latest GBP": "plans_tally", "Stage III": "stage_iii_done",
             "BD106": "bd106_in_plans", "GFA and car parking": "gfa_summary", "consolidated digital": "consolidated_digital_file", "qualifying minor works": "minor_works_in_plans"}
    miss = [v for r in rows if r[0] == "OP / TOP" and r[2] == "FAIL" for k, v in names.items() if k in r[1]]
    return {"missing_prerequisites": sorted(miss), "ready_to_apply": not miss}


def c04(i):
    lim = PERIODS["not_minor_amendment_thresholds"]
    return {"not_minor": sorted(c["id"] for c in i["changes"] if c["value"] > lim[c["measure"]])}


def c06(i):
    rows, _ = supervision_plan.run(copy.deepcopy(i))
    return {"unmet_requirements": sorted(r[1].split(" – ")[1].replace(" ", "|") for r in rows if r[4] == "FAIL")}


ANCHORS = {"F01": f01, "F02": f02, "F03": f03, "F04": f04, "F05": f05, "F06": f06, "S01": s01, "S02": s02, "S03": s03, "S04": s04,
           "D01": d01, "D02": d02, "D03": d03, "D04": d04, "D05": d05, "D07": d07, "T01": t01, "T02": t02, "T03": t03, "T04": t04,
           "C01": c01, "C02": c02, "C03": c03, "C04": c04, "C06": c06}
