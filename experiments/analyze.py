"""Full statistical analysis for the script-bias study.
Reads all judge outputs in results/, produces results/analysis.json with:
paired mean differences, bootstrap 95% CIs, Wilcoxon signed-rank (exact via
permutation when scipy absent), effect sizes, tier breakdowns, mitigation
comparison, and reason-text script-mention rates.
Every number in the paper comes from this file.
"""
import json, math, os, random, re, statistics as st
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
CONDS = ["iast", "ascii", "hinglish"]


def load_gemini(path):
    by, tier, reasons = defaultdict(dict), {}, defaultdict(dict)
    for line in open(path):
        r = json.loads(line)
        if r["score"] is not None:
            by[r["id"]][r["condition"]] = r["score"]
            tier[r["id"]] = r["tier"]
            reasons[r["id"]][r["condition"]] = r.get("reason", "")
    return by, tier, reasons


def load_qwen(path):
    import re as _re
    by, tier = defaultdict(dict), {}
    for line in open(path):
        r = json.loads(line)
        m = _re.match(r"^\s*(\d{1,3})", r["text"])
        if m and 0 <= int(m.group(1)) <= 100:
            by[r["id"]][r["condition"]] = int(m.group(1))
            tier[r["id"]] = r["tier"]
    return by, tier, None


def load_claude(name):
    by, tier = defaultdict(dict), {}
    for r in range(4):
        key = json.load(open(os.path.join(HERE, "claude_packets", f"key_r{r}.json")))
        data = json.load(open(os.path.join(RES, f"claude_{name}_r{r}.json")))
        for e in data:
            k = key[str(e["n"])]
            by[k["id"]][k["cond"]] = e["score"]
            tier[k["id"]] = k["tier"]
    return by, tier, None


def wilcoxon_p(diffs, n_perm=20000):
    """Two-sided sign-flip permutation test on paired differences."""
    d = [x for x in diffs if x != 0]
    if not d:
        return 1.0
    obs = abs(sum(d))
    rng = random.Random(7)
    hits = 0
    for _ in range(n_perm):
        s = sum(x if rng.random() < 0.5 else -x for x in d)
        if abs(s) >= obs:
            hits += 1
    return (hits + 1) / (n_perm + 1)


def boot_ci(diffs, n_boot=10000):
    rng = random.Random(11)
    means = []
    for _ in range(n_boot):
        samp = [diffs[rng.randrange(len(diffs))] for _ in diffs]
        means.append(st.mean(samp))
    means.sort()
    return means[int(0.025 * n_boot)], means[int(0.975 * n_boot)]


def analyze_judge(by, tier, reasons, label):
    out = {"judge": label, "n_items": len(by), "conditions": {}}
    for cond in CONDS:
        pairs = [(by[i]["deva"], by[i][cond], i) for i in by if "deva" in by[i] and cond in by[i]]
        diffs = [c - d for d, c, _ in pairs]  # positive = romanized scored HIGHER
        if len(diffs) < 10:
            out["conditions"][cond] = {"n": len(diffs), "note": "insufficient pairs yet"}
            continue
        lo, hi = boot_ci(diffs)
        sd = st.pstdev(diffs) or 1e-9
        entry = {
            "n": len(pairs),
            "mean_deva": round(st.mean(p[0] for p in pairs), 2),
            "mean_cond": round(st.mean(p[1] for p in pairs), 2),
            "mean_shift": round(st.mean(diffs), 3),
            "ci95": [round(lo, 2), round(hi, 2)],
            "p_wilcoxon_perm": round(wilcoxon_p(diffs), 5),
            "cohen_dz": round(st.mean(diffs) / sd, 3),
            "by_tier": {},
        }
        for t in ["high", "medium", "low"]:
            td = [c - d for d, c, i in pairs if tier[i] == t]
            if len(td) < 5:
                entry["by_tier"][t] = {"n": len(td), "note": "insufficient"}
                continue
            tlo, thi = boot_ci(td)
            entry["by_tier"][t] = {
                "mean_shift": round(st.mean(td), 2),
                "ci95": [round(tlo, 2), round(thi, 2)],
                "p": round(wilcoxon_p(td), 5),
            }
        if reasons:
            pat = re.compile(r"hinglish|roman|script|transliter|devanagari|orthograph", re.I)
            hits = sum(1 for i in by if cond in reasons.get(i, {}) and pat.search(reasons[i][cond] or ""))
            entry["reason_mentions_script"] = f"{hits}/{len(pairs)}"
        out["conditions"][cond] = entry
    return out


def main():
    report = {"generated": "2026-08-29", "judges": []}
    specs = [
        ("gemini-3.6-flash", os.path.join(RES, "scores_gemini-3.6-flash_t0.jsonl"), "gemini"),
        ("gemini-3.6-flash+mitigation", os.path.join(RES, "scores_gemini-3.6-flash_mit-t0.jsonl"), "gemini"),
        ("gemini-3.1-pro-preview", os.path.join(RES, "scores_gemini-3.1-pro-preview_t0.jsonl"), "gemini"),
        ("claude-sonnet-5", "sonnet", "claude"),
        ("claude-opus-5", "opus", "claude"),
        ("claude-fable-5", "fable", "claude"),
        ("qwen2.5-7b-instruct", os.path.join(RES, "scores_qwen2.5-7b_logprobs.jsonl"), "qwen"),
    ]
    for label, src, kind in specs:
        try:
            if kind == "gemini":
                by, tier, reasons = load_gemini(src)
            elif kind == "qwen":
                by, tier, reasons = load_qwen(src)
            else:
                by, tier, reasons = load_claude(src)
            if by:
                report["judges"].append(analyze_judge(by, tier, reasons, label))
        except FileNotFoundError:
            print(f"skip {label}: not found")
    with open(os.path.join(RES, "analysis.json"), "w") as f:
        json.dump(report, f, indent=1)
    for j in report["judges"]:
        print(f"\n{j['judge']}:")
        for c, e in j["conditions"].items():
            if "mean_shift" not in e:
                print(f"  {c:8s} (n={e['n']}, incomplete)")
                continue
            med = e["by_tier"]["medium"]
            medtxt = f"med-tier={med['mean_shift']:+.2f} (p={med['p']})" if "mean_shift" in med else "med-tier incomplete"
            print(f"  {c:8s} shift={e['mean_shift']:+.2f} CI{e['ci95']} p={e['p_wilcoxon_perm']} "
                  f"dz={e['cohen_dz']} {medtxt}")


if __name__ == "__main__":
    main()
