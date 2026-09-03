"""Pairwise preference test: same content, deva vs ascii rendering, which does
the judge prefer? Content is identical by construction, so a script-blind judge
should tie (or split 50/50). Every item is judged in BOTH presentation orders
to cancel position bias. Judges: gemini-3.6-flash (native API) or
claude-sonnet-5 (headless `claude -p`, same interface as Table 1).

Usage: python3 run_pairwise.py --judge gemini-3.6-flash
       python3 run_pairwise.py --judge claude-sonnet-5
Output: results/pairwise_<judge>.jsonl (one row per item x order)
"""
import argparse, json, os, random, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_gemini_judge import call_gemini, api_key as gemini_api_key

HERE = os.path.dirname(os.path.abspath(__file__))
DATASET = os.path.join(HERE, "dataset_conditions.json")
RES = os.path.join(HERE, "..", "results")

PROMPT = (
    "You are comparing two responses to the same instruction for an "
    "instruction-following benchmark.\n"
    "Decide which response is better overall considering correctness, completeness, "
    "helpfulness, and clarity. If they are equally good, say tie.\n"
    "Instruction:\n{instruction}\n\nResponse A:\n{a}\n\nResponse B:\n{b}\n\n"
    'Reply with ONLY a JSON object: {{"winner": "A" or "B" or "tie", '
    '"reason": "<one short sentence>"}}'
)


def parse(text):
    if not text:
        return None, ""
    m = re.search(r'"winner"\s*:\s*"(A|B|tie)"', text, re.IGNORECASE)
    if m:
        rm = re.search(r'"reason"\s*:\s*"([^"]*)"', text)
        return m.group(1).lower() if m.group(1).lower() == "tie" else m.group(1).upper(), (rm.group(1) if rm else "")
    return None, text[:150]


def judge_claude(model, prompt):
    p = subprocess.run(["claude", "-p", "--model", model], input=prompt,
                       capture_output=True, text=True, timeout=240)
    return p.stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", required=True, choices=["gemini-3.6-flash", "claude-sonnet-5"])
    args = ap.parse_args()

    items = json.load(open(DATASET))
    out_path = os.path.join(RES, f"pairwise_{args.judge}.jsonl")
    done = set()
    if os.path.exists(out_path):
        for line in open(out_path):
            r = json.loads(line)
            if r["winner"] is not None:
                done.add((r["id"], r["order"]))

    # order "deva_first": A=deva B=ascii; "ascii_first": A=ascii B=deva
    jobs = []
    for it in items:
        if not (it["conditions"].get("deva") and it["conditions"].get("ascii")):
            continue
        for order in ["deva_first", "ascii_first"]:
            if (it["id"], order) in done:
                continue
            jobs.append((it, order))
    random.seed(41)
    random.shuffle(jobs)
    print(f"{args.judge}: {len(jobs)} pairwise calls ({len(done)} done)", flush=True)

    key = gemini_api_key() if args.judge == "gemini-3.6-flash" else None
    with open(out_path, "a") as out:
        for n, (it, order) in enumerate(jobs, 1):
            deva, ascii_ = it["conditions"]["deva"], it["conditions"]["ascii"]
            a, b = (deva, ascii_) if order == "deva_first" else (ascii_, deva)
            prompt = PROMPT.format(instruction=it["instruction_deva"], a=a, b=b)
            if args.judge == "gemini-3.6-flash":
                text, _, _ = call_gemini("gemini-3.6-flash", prompt, 0.0, key)
            else:
                text = judge_claude(args.judge, prompt)
            winner, reason = parse(text)
            # normalize to which SCRIPT won, independent of position
            script_winner = None
            if winner == "tie":
                script_winner = "tie"
            elif winner in ("A", "B"):
                script_winner = ("deva" if winner == "A" else "ascii") if order == "deva_first" \
                    else ("ascii" if winner == "A" else "deva")
            out.write(json.dumps({"id": it["id"], "tier": it["tier"], "order": order,
                                  "judge": args.judge, "winner": winner,
                                  "script_winner": script_winner, "reason": reason},
                                 ensure_ascii=False) + "\n")
            out.flush()
            if n % 50 == 0:
                print(f"  {n}/{len(jobs)}", flush=True)
    print(f"finished pairwise {args.judge}", flush=True)


if __name__ == "__main__":
    main()
