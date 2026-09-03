"""Analysis for the 2026-09-03 follow-up batteries. Every number quoted in the
paper's follow-up section comes from this script's output file,
results/analysis_batteries.json:

  1. GPT-5.6-terra core battery (OpenRouter, one item per call, temp=0)
  2. Sub-dimension decomposition, Sonnet (claude -p) and Gemini Flash (native)
  3. Pairwise deva-vs-ascii preference, Sonnet and Flash, both orders
  4. Protocol control: Sonnet batched-25 vs one-per-call, same interface
  5. Test-retest noise baseline (Flash, 5 reps, temp=0)
  6. Qwen logprob LEADING-TOKEN distribution (honest relabel: logprobs were
     captured at the first generated token only, so for 2-digit scores this
     measures the leading digit, not the full 0-100 expected score)
"""
import json, math, random, statistics as st
from collections import defaultdict, Counter
from math import comb
import os

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
OUT = {}


def load_scores(path, score_key="score"):
    by, tier = defaultdict(dict), {}
    n_null = 0
    for line in open(os.path.join(RES, path)):
        r = json.loads(line)
        if r.get(score_key) is None:
            n_null += 1
            continue
        by[r["id"]][r["condition"]] = r[score_key]
        tier[r["id"]] = r["tier"]
    return by, tier, n_null


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


def shift_block(by, tier, conds=("iast", "ascii", "hinglish")):
    block = {}
    for cond in conds:
        ids = [i for i in by if "deva" in by[i] and cond in by[i]]
        diffs = [by[i][cond] - by[i]["deva"] for i in ids]
        if not diffs:
            continue
        sd = st.stdev(diffs) if len(diffs) > 1 else 1e-9
        e = {"n": len(diffs), "mean_shift": round(st.mean(diffs), 2),
             "ci95": boot_ci(diffs), "p": perm_p(diffs),
             "dz": round(st.mean(diffs) / sd, 2), "by_tier": {}}
        for t in ["high", "medium", "low"]:
            td = [by[i][cond] - by[i]["deva"] for i in ids if tier[i] == t]
            if td:
                e["by_tier"][t] = {"n": len(td), "mean_shift": round(st.mean(td), 2)}
        block[cond] = e
    return block


# --- 1. GPT-5.6-terra core battery ---
by, tier, n_null = load_scores("scores_openrouter_openai_gpt-5.6-terra.jsonl")
OUT["gpt_5_6_terra"] = {"protocol": "openrouter-unified-temp0-one-per-call",
                        "unparsed": n_null, "conditions": shift_block(by, tier)}

# --- 2. Sub-dimension decomposition ---
subdim = {}
for path, judge in [("subdim_native_claude-sonnet-5.jsonl", "claude-sonnet-5"),
                    ("subdim_native_gemini-3.6-flash.jsonl", "gemini-3.6-flash")]:
    by2, tier2 = defaultdict(dict), {}
    n_null = 0
    for line in open(os.path.join(RES, path)):
        r = json.loads(line)
        subs = {k: r[k] for k in ["correctness", "completeness", "helpfulness", "clarity"]}
        if any(v is None for v in subs.values()):
            n_null += 1
            continue
        by2[r["id"]][r["condition"]] = subs
        tier2[r["id"]] = r["tier"]
    jblock = {"unparsed": n_null, "conditions": {}}
    for cond in ["iast", "ascii", "hinglish"]:
        ids = [i for i in by2 if "deva" in by2[i] and cond in by2[i]]
        if not ids:
            continue
        dims, total = {}, 0.0
        for dim in ["correctness", "completeness", "helpfulness", "clarity"]:
            d = [by2[i][cond][dim] - by2[i]["deva"][dim] for i in ids]
            m = st.mean(d)
            dims[dim] = {"mean_shift_0to25": round(m, 2),
                         "ci95": boot_ci(d), "p": perm_p(d)}
            total += m
        jblock["conditions"][cond] = {
            "n": len(ids), "dims": dims,
            "total_shift_0to100": round(total, 2),
            "clarity_share_pct": round(dims["clarity"]["mean_shift_0to25"] / total * 100) if total else None,
        }
    subdim[judge] = jblock
OUT["subdimension_decomposition"] = subdim

# --- 3. Pairwise preference ---
pw = {}
for path, judge in [("pairwise_gemini-3.6-flash.jsonl", "gemini-3.6-flash"),
                    ("pairwise_claude-sonnet-5.jsonl", "claude-sonnet-5")]:
    rows = [json.loads(l) for l in open(os.path.join(RES, path))]
    c = Counter(r["script_winner"] for r in rows)
    d_w, a_w, ties = c.get("deva", 0), c.get("ascii", 0), c.get("tie", 0)
    n = d_w + a_w
    p_sign = min(1.0, sum(comb(n, k) for k in range(min(d_w, a_w) + 1)) / 2 ** n * 2) if n else None
    byorder = {o: dict(Counter(r["script_winner"] for r in rows if r["order"] == o))
               for o in ["deva_first", "ascii_first"]}
    bytier = {t: dict(Counter(r["script_winner"] for r in rows if r["tier"] == t))
              for t in ["high", "medium", "low"]}
    unparsed = sum(1 for r in rows if r["script_winner"] is None)
    pw[judge] = {"n_trials": len(rows), "deva_wins": d_w, "ascii_wins": a_w,
                 "ties": ties, "unparsed": unparsed,
                 "sign_test_p": p_sign, "by_order": byorder, "by_tier": bytier}
OUT["pairwise_deva_vs_ascii"] = pw

# --- 4. Protocol control (batched-25 vs one-per-call, same interface) ---
bb, tierb, nb = load_scores("scores_protocol-batched_claude-sonnet-5.jsonl")
bo, tiero, no = load_scores("scores_claude-api_claude-sonnet-5.jsonl")
OUT["protocol_control_sonnet"] = {
    "design": "same model, same claude -p interface, same rubric per item, same sampling; "
              "batch size (25 vs 1) is the only manipulated variable",
    "batched_25": {"unparsed": nb, "conditions": shift_block(bb, tierb)},
    "one_per_call": {"unparsed": no, "conditions": shift_block(bo, tiero)},
}

# --- 5. Test-retest noise baseline ---
tr = defaultdict(list)
for line in open(os.path.join(RES, "testretest_gemini-3.6-flash.jsonl")):
    r = json.loads(line)
    if r["score"] is not None:
        tr[(r["id"], r["condition"])].append(r["score"])
sds = [st.stdev(v) for v in tr.values() if len(v) > 1]
ranges = [max(v) - min(v) for v in tr.values() if len(v) > 1]
OUT["testretest_flash"] = {
    "design": "30 stratified items x deva+ascii x 5 identical calls, temp=0",
    "n_item_conditions": len(tr),
    "mean_within_item_sd": round(st.mean(sds), 2),
    "mean_within_item_range": round(st.mean(ranges), 2),
    "perfectly_stable": sum(1 for v in tr.values() if len(set(v)) == 1),
}

# --- 6. Qwen leading-token distribution (honest relabel) ---
import re as _re
by_cond_lp = defaultdict(list)
for line in open(os.path.join(RES, "scores_qwen2.5-7b_logprobs.jsonl")):
    r = json.loads(line)
    tl = r.get("top_logprobs", {})
    numeric = {k: v for k, v in tl.items() if _re.fullmatch(r"\d+", k.strip())}
    if not numeric:
        continue
    probs = {k: math.exp(v) for k, v in numeric.items()}
    z = sum(probs.values())
    if z == 0:
        continue
    exp = sum(int(k) * (p / z) for k, p in probs.items())
    var = sum(((int(k) - exp) ** 2) * (p / z) for k, p in probs.items())
    by_cond_lp[r["condition"]].append((exp, var ** 0.5))
OUT["qwen_leading_token_distribution"] = {
    "caveat": "logprobs were captured at the FIRST generated score token only; for "
              "two-digit scores this is the distribution over the leading digit, not "
              "the full 0-100 expected score",
    "per_condition": {c: {"mean_expected_leading_token": round(st.mean(v[0] for v in vals), 2),
                          "mean_within_call_sd": round(st.mean(v[1] for v in vals), 2),
                          "n": len(vals)}
                      for c, vals in by_cond_lp.items() if vals},
}

path = os.path.join(RES, "analysis_batteries.json")
json.dump(OUT, open(path, "w"), indent=1)
print(f"wrote {path}")
print(json.dumps({k: (v if k in ("testretest_flash",) else "...") for k, v in OUT.items()}, indent=1))
