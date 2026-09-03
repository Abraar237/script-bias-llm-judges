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


# --- 4. Matched-interface Sonnet core arm (OpenRouter gateway, temp 0) ---
p = os.path.join(RES, "scores_openrouter_anthropic_claude-sonnet-5.jsonl")
if os.path.exists(p):
    by, tier = defaultdict(dict), {}
    for line in open(p):
        r = json.loads(line)
        if r["score"] is not None:
            by[r["id"]][r["condition"]] = r["score"]; tier[r["id"]] = r["tier"]
    block = {}
    for cond in ["iast", "ascii", "hinglish"]:
        ids = [i for i in by if "deva" in by[i] and cond in by[i]]
        diffs = [by[i][cond] - by[i]["deva"] for i in ids]
        e = {"n": len(diffs), "mean_shift": round(st.mean(diffs), 2),
             "ci95": boot_ci(diffs), "p": perm_p(diffs), "by_tier": {}}
        for t in ["high", "medium", "low"]:
            td = [by[i][cond] - by[i]["deva"] for i in ids if tier[i] == t]
            if td:
                e["by_tier"][t] = round(st.mean(td), 2)
        block[cond] = e
    OUT["matched_interface_sonnet"] = {
        "design": "full Sonnet core arm through the same OpenAI-compatible gateway as GPT-5.6, temperature 0, one item per call",
        "conditions": block}

# --- 5. Authorship replication set (Gemini-authored, 51 items) ---
repl = {}
for path, judge in [("replication_claude-sonnet-5.jsonl", "claude-sonnet-5"),
                    ("replication_gemini-3.6-flash.jsonl", "gemini-3.6-flash")]:
    fp = os.path.join(RES, path)
    if not os.path.exists(fp):
        continue
    by, tier = defaultdict(dict), {}
    for line in open(fp):
        r = json.loads(line)
        if r["score"] is not None:
            by[r["id"]][r["condition"]] = r["score"]; tier[r["id"]] = r["tier"]
    jb = {}
    for cond in ["iast", "ascii"]:
        ids = [i for i in by if "deva" in by[i] and cond in by[i]]
        diffs = [by[i][cond] - by[i]["deva"] for i in ids]
        e = {"n": len(diffs), "mean_shift": round(st.mean(diffs), 2),
             "ci95": boot_ci(diffs), "p": perm_p(diffs), "by_tier": {}}
        for t in ["high", "medium", "low"]:
            td = [by[i][cond] - by[i]["deva"] for i in ids if tier[i] == t]
            if td:
                e["by_tier"][t] = {"mean": round(st.mean(td), 2), "p": perm_p(td), "n": len(td)}
        jb[cond] = e
    repl[judge] = jb
OUT["authorship_replication"] = {"author_model": "gemini-3.1-pro-preview", "judges": repl}

# --- 6. Pairwise, all seven judges ---
from collections import Counter
from math import comb
pw = {}
for f, j in [("pairwise_gemini-3.6-flash.jsonl", "gemini-3.6-flash"),
             ("pairwise_claude-sonnet-5.jsonl", "claude-sonnet-5"),
             ("pairwise_gemini-3.1-pro-preview.jsonl", "gemini-3.1-pro-preview"),
             ("pairwise_claude-opus-5.jsonl", "claude-opus-5"),
             ("pairwise_claude-fable-5.jsonl", "claude-fable-5"),
             ("pairwise_gpt-5.6-terra.jsonl", "gpt-5.6"),
             ("pairwise_qwen-2.5-7b.jsonl", "qwen-2.5-7b")]:
    fp = os.path.join(RES, f)
    if not os.path.exists(fp):
        continue
    rows = [json.loads(l) for l in open(fp)]
    c = Counter(r["script_winner"] for r in rows)
    d_w, a_w = c.get("deva", 0), c.get("ascii", 0)
    n = d_w + a_w
    p_sign = min(1.0, sum(comb(n, k) for k in range(min(d_w, a_w) + 1)) / 2 ** n * 2) if n else None
    pw[j] = {"deva": d_w, "ascii": a_w, "tie": c.get("tie", 0),
             "unparsed": sum(1 for r in rows if r["script_winner"] is None),
             "sign_p": p_sign}
OUT["pairwise_all_judges"] = pw

# --- 7. Ranking-flip demo ---
fp = os.path.join(RES, "ranking_claude-sonnet-5.jsonl")
if os.path.exists(fp):
    scores = defaultdict(lambda: defaultdict(list))
    for line in open(fp):
        r = json.loads(line)
        if r["score"] is not None:
            scores[r["script"]][r["system"]].append(r["score"])
    rk = {}
    for script, sysmap in scores.items():
        means = {sysname: round(st.mean(v), 2) for sysname, v in sysmap.items()}
        order = sorted(means, key=means.get, reverse=True)
        rk[script] = {"means": means, "ranking": order,
                      "n_per_system": {k: len(v) for k, v in sysmap.items()}}
    flip = rk.get("deva", {}).get("ranking") != rk.get("ascii", {}).get("ranking")
    OUT["ranking_flip_demo"] = {"judge": "claude-sonnet-5",
                                "systems": ["qwen-2.5-7b", "gemini-3.6-flash", "gemini-3.1-pro-preview"],
                                "per_script": rk, "ranking_changed": flip}

path = os.path.join(RES, "analysis_batteries2.json")
json.dump(OUT, open(path, "w"), indent=1)
print(f"wrote {path}")
print(json.dumps(OUT, indent=1))
