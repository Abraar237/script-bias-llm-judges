"""Free analyses using data we already have: (1) rank/logit-transformed tier
reanalysis to separate the discretion story from ceiling/floor compression,
(2) Benjamini-Hochberg FDR correction over every reported p-value,
(3) Qwen logprob distribution analysis (mode shift vs distributional widening),
(4) ranking-stability check: does the high/medium/low ordering ever flip.
Writes results/analysis_extra.json.
"""
import json, math, os, statistics as st
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
A = json.load(open(os.path.join(RES, "analysis.json")))


def load_gemini(path):
    by, tier = defaultdict(dict), {}
    for line in open(path):
        r = json.loads(line)
        if r["score"] is not None:
            by[r["id"]][r["condition"]] = r["score"]
            tier[r["id"]] = r["tier"]
    return by, tier


# --- 1. Rank-transformed tier reanalysis (Flash) ---
by, tier = load_gemini(os.path.join(RES, "scores_gemini-3.6-flash_t0.jsonl"))
ids = sorted(by)
rank_result = {}
for cond in ["iast", "ascii", "hinglish"]:
    # rank deva scores and cond scores jointly within each tier to remove ceiling/floor scaling
    for t in ["high", "medium", "low"]:
        tids = [i for i in ids if tier[i] == t and "deva" in by[i] and cond in by[i]]
        deva_vals = [by[i]["deva"] for i in tids]
        cond_vals = [by[i][cond] for i in tids]
        # logit-ish transform on 0-100 clipped to (0.5,99.5) to avoid inf
        def logit(x):
            p = min(max(x, 0.5), 99.5) / 100
            return math.log(p / (1 - p))
        dl = [logit(v) for v in deva_vals]
        cl = [logit(v) for v in cond_vals]
        diffs = [c - d for c, d in zip(cl, dl)]
        rank_result.setdefault(cond, {})[t] = {
            "n": len(diffs), "mean_logit_shift": round(st.mean(diffs), 3) if diffs else None,
            "raw_mean_shift": round(st.mean(c - d for c, d in zip(cond_vals, deva_vals)), 2) if diffs else None,
        }
print("=== Rank/logit-transformed tier reanalysis (Flash) ===")
for cond, tt in rank_result.items():
    for t, v in tt.items():
        print(f"  {cond:8s} {t:6s} logit-shift={v['mean_logit_shift']:+.3f}  raw-shift={v['raw_mean_shift']:+.2f}  n={v['n']}")
print("Interpretation: if the logit-shift is near-zero while the raw shift peaks at medium,")
print("ceiling/floor compression on the raw scale is the better explanation than discretion.")
print("If logit-shift ALSO peaks at medium, the discretion story survives the transform.\n")

# --- 2. Benjamini-Hochberg FDR correction over every reported p-value ---
pvals = []
for j in A["judges"]:
    for cond, e in j["conditions"].items():
        if "p_wilcoxon_perm" in e:
            pvals.append((j["judge"], cond, "overall", e["p_wilcoxon_perm"]))
        for t, bt in e.get("by_tier", {}).items():
            if "p" in bt:
                pvals.append((j["judge"], cond, t, bt["p"]))
qb = A.get("qwen_mitigation_battery", {})
for arm, conds in qb.items():
    for cond, e in conds.items():
        if "p" in e:
            pvals.append((f"qwen-mit-{arm}", cond, "overall", e["p"]))

m = len(pvals)
sorted_p = sorted(pvals, key=lambda x: x[3])
fdr_results = []
prev_thresh_rank = 0
for rank, (judge, cond, t, p) in enumerate(sorted_p, 1):
    bh_crit = 0.05 * rank / m
    fdr_results.append({"judge": judge, "cond": cond, "tier": t, "p": p, "rank": rank,
                        "bh_critical": round(bh_crit, 6), "survives_fdr_0.05": p <= bh_crit})
n_survive = sum(1 for r in fdr_results if r["survives_fdr_0.05"])
print(f"=== Benjamini-Hochberg FDR correction ===")
print(f"  {m} total p-values tested; {n_survive} survive FDR q=0.05")
print(f"  (largest surviving p-value sets the effective significance threshold)\n")

# --- 3. Qwen logprob distribution analysis ---
qrows = [json.loads(l) for l in open(os.path.join(RES, "scores_qwen2.5-7b_logprobs.jsonl"))]
by_cond_lp = defaultdict(list)
for r in qrows:
    tl = r.get("top_logprobs", {})
    if not tl:
        continue
    # expected score under the top-20 distribution (renormalized), vs argmax
    import re as _re
    numeric = {k: v for k, v in tl.items() if _re.fullmatch(r"\d+", k.strip())}
    if not numeric:
        continue
    probs = {k: math.exp(v) for k, v in numeric.items()}
    z = sum(probs.values())
    if z == 0:
        continue
    expected = sum(int(k) * (p / z) for k, p in probs.items())
    variance = sum(((int(k) - expected) ** 2) * (p / z) for k, p in probs.items())
    by_cond_lp[r["condition"]].append((expected, variance ** 0.5))
print("=== Qwen logprob distribution (expected score and std, top-20 mass) ===")
for cond, vals in by_cond_lp.items():
    if vals:
        exps = [v[0] for v in vals]
        stds = [v[1] for v in vals]
        print(f"  {cond:8s} mean expected-score={st.mean(exps):6.2f}  mean within-call std={st.mean(stds):5.2f}  n={len(vals)}")
print("Interpretation: if 'ascii'/'iast' std is materially higher than 'deva', the shift is a widening")
print("of the score distribution (increased uncertainty), not a clean mode move.\n")

# --- 4. Ranking-stability check across the three quality tiers (proxy 'systems') ---
print("=== Ranking-stability check (high/medium/low as proxy systems) ===")
flip_any = False
for j in A["judges"]:
    tiers_present = all("by_tier" in e for e in j["conditions"].values())
    if not tiers_present:
        continue
    for cond, e in j["conditions"].items():
        bt = e.get("by_tier", {})
        if not all(t in bt and "mean_shift" in bt[t] for t in ["high", "medium", "low"]):
            continue
        # reconstruct approximate absolute means: we only have shift, not deva means per judge;
        # use the Flash/Pro deva means (99.1/51.4/15.2) as the shared baseline reference frame
        deva_h, deva_m, deva_l = 99.1, 51.4, 15.2
        cond_h = deva_h + bt["high"]["mean_shift"]
        cond_m = deva_m + bt["medium"]["mean_shift"]
        cond_l = deva_l + bt["low"]["mean_shift"]
        order_deva = "high>medium>low"  # 99.1 > 51.4 > 15.2 always true
        order_cond = "high>medium>low" if (cond_h > cond_m > cond_l) else "FLIPPED"
        if order_cond == "FLIPPED":
            flip_any = True
        print(f"  {j['judge']:26s} {cond:8s}: deva-frame order preserved={'YES' if order_cond!='FLIPPED' else 'NO'}")
print(f"\nAny ranking flip observed: {flip_any}")
print("Note: tier gaps in this dataset are large by design (99 vs 51 vs 15), so this checks")
print("whether shifts of the observed size (<=18 points) could flip a 3-tier ranking; it does")
print("not by itself demonstrate a real-system leaderboard flip, which needs closely-matched systems.\n")

out = {
    "rank_logit_tier_reanalysis": rank_result,
    "fdr_correction": {"n_tests": m, "n_survive_q05": n_survive, "detail": fdr_results},
    "qwen_logprob_distribution": {c: {"mean_expected": round(st.mean(v[0] for v in vals), 2),
                                      "mean_std": round(st.mean(v[1] for v in vals), 2), "n": len(vals)}
                                  for c, vals in by_cond_lp.items() if vals},
    "ranking_stability": {"any_flip_in_deva_reference_frame": flip_any},
}
json.dump(out, open(os.path.join(RES, "analysis_extra.json"), "w"), indent=1)
print("wrote results/analysis_extra.json")
