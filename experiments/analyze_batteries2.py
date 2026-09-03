"""Analysis for the review-response batteries (2026-09-03, round 2):
  1. Cross-script control (deliberately mismatched instruction/response cells)
     vs the matched cells from the core arms, Flash and Sonnet.
  2. Claude test-retest noise floor (same design as the Flash battery).
  3. Anchored-pointwise disambiguation (reference answer in context, Flash).
Writes results/analysis_batteries2.json.
"""
import json, os, random, statistics as st
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
OUT = {}


def boot_ci(diffs, n=10000, seed=7):
    random.seed(seed)
    means = sorted(st.mean(random.choices(diffs, k=len(diffs))) for _ in range(n))
    return round(means[int(0.025 * n)], 2), round(means[int(0.975 * n)], 2)


def perm_p(diffs, n=20000, seed=11):
    random.seed(seed)
    obs = abs(sum(diffs))
    hits = sum(1 for _ in range(n)
               if abs(sum(d * random.choice((1, -1)) for d in diffs)) >= obs)
    return round((hits + 1) / (n + 1), 5)


# --- 1. Cross-script control ---
# matched baselines come from the core one-per-call arms
def load_core(path):
    by = defaultdict(dict)
    for line in open(os.path.join(RES, path)):
        r = json.loads(line)
        if r.get("score") is not None:
            by[r["id"]][r["condition"]] = r["score"]
    return by

core = {
    "gemini-3.6-flash": load_core("scores_gemini-3.6-flash_t0.jsonl"),
    "claude-sonnet-5": load_core("scores_claude-api_claude-sonnet-5.jsonl"),
}
xs = {}
for judge in ["gemini-3.6-flash", "claude-sonnet-5"]:
    path = os.path.join(RES, f"crossscript_{judge}.jsonl")
    if not os.path.exists(path):
        continue
    cells = defaultdict(dict)
    for line in open(path):
        r = json.loads(line)
        if r.get("score") is not None:
            cells[r["cell"]][r["id"]] = r["score"]
    jb = {}
    # X1: deva instruction + ascii response, vs matched ascii cell (iast instr + ascii resp)
    ids = [i for i in cells.get("deva_instr_ascii_resp", {}) if "ascii" in core[judge].get(i, {})]
    d1 = [cells["deva_instr_ascii_resp"][i] - core[judge][i]["ascii"] for i in ids]
    if d1:
        jb["mismatch_deva_instr_ascii_resp_minus_matched_ascii"] = {
            "n": len(d1), "mean": round(st.mean(d1), 2), "ci95": boot_ci(d1), "p": perm_p(d1)}
    # X2: iast instruction + deva response, vs matched deva cell (deva instr + deva resp)
    ids = [i for i in cells.get("iast_instr_deva_resp", {}) if "deva" in core[judge].get(i, {})]
    d2 = [cells["iast_instr_deva_resp"][i] - core[judge][i]["deva"] for i in ids]
    if d2:
        jb["mismatch_iast_instr_deva_resp_minus_matched_deva"] = {
            "n": len(d2), "mean": round(st.mean(d2), 2), "ci95": boot_ci(d2), "p": perm_p(d2)}
    xs[judge] = jb
OUT["crossscript_control"] = {
    "design": "deliberately mismatched instruction/response script cells vs the matched "
              "cells of the core arms; a large negative mismatch effect would mean script "
              "mismatch, not orthography, drives penalties",
    "judges": xs,
}

# --- 2. Claude test-retest ---
p = os.path.join(RES, "testretest_claude-sonnet-5.jsonl")
if os.path.exists(p):
    tr = defaultdict(list)
    for line in open(p):
        r = json.loads(line)
        if r["score"] is not None:
            tr[(r["id"], r["condition"])].append(r["score"])
    sds = [st.stdev(v) for v in tr.values() if len(v) > 1]
    ranges = [max(v) - min(v) for v in tr.values() if len(v) > 1]
    OUT["testretest_claude_sonnet"] = {
        "n_item_conditions": len(tr),
        "mean_within_item_sd": round(st.mean(sds), 2) if sds else None,
        "mean_within_item_range": round(st.mean(ranges), 2) if ranges else None,
        "perfectly_stable": sum(1 for v in tr.values() if len(set(v)) == 1),
    }

# --- 3. Anchored pointwise ---
p = os.path.join(RES, "anchored_pointwise_gemini-3.6-flash.jsonl")
if os.path.exists(p):
    by = defaultdict(dict)
    tier = {}
    for line in open(p):
        r = json.loads(line)
        if r["score"] is not None:
            by[r["id"]][r["condition"]] = r["score"]
            tier[r["id"]] = r["tier"]
    ids = [i for i in by if "deva" in by[i] and "ascii" in by[i]]
    diffs = [by[i]["ascii"] - by[i]["deva"] for i in ids]
    res = {"n": len(diffs), "ascii_minus_deva_mean": round(st.mean(diffs), 2),
           "ci95": boot_ci(diffs), "p": perm_p(diffs), "by_tier": {}}
    for t in ["high", "medium", "low"]:
        td = [by[i]["ascii"] - by[i]["deva"] for i in ids if tier[i] == t]
        if td:
            res["by_tier"][t] = {"n": len(td), "mean": round(st.mean(td), 2)}
    OUT["anchored_pointwise_flash"] = {
        "design": "pointwise scoring with the frozen Devanagari original in context as a "
                  "calibration reference; unanchored pointwise baseline is +2.17 (Table 1), "
                  "pairwise preference is 288/300 deva",
        "result": res,
    }

path = os.path.join(RES, "analysis_batteries2.json")
json.dump(OUT, open(path, "w"), indent=1)
print(f"wrote {path}")
print(json.dumps(OUT, indent=1))
