"""Judge the Serbian set: cyrl and latn conditions, one item per call,
script-matched instructions, same rubric and statistics as the Hindi arms.

Usage: python3 run_serbian_judge.py --judge gemini-3.6-flash
       python3 run_serbian_judge.py --judge claude-sonnet-5
"""
import argparse, json, os, random, subprocess, sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_gemini_judge import RUBRIC, call_gemini, parse_score, api_key

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")


def judge_claude(model, prompt):
    p = subprocess.run(["claude", "-p", "--model", model], input=prompt,
                       capture_output=True, text=True, timeout=240)
    return p.stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", required=True, choices=["gemini-3.6-flash", "claude-sonnet-5"])
    args = ap.parse_args()

    items = json.load(open(os.path.join(HERE, "serbian_conditions.json")))
    out_path = os.path.join(RES, f"serbian_{args.judge}.jsonl")
    done = set()
    if os.path.exists(out_path):
        for line in open(out_path):
            r = json.loads(line)
            if r["score"] is not None:
                done.add((r["id"], r["condition"]))

    jobs = []
    for it in items:
        for cond in ["cyrl", "latn"]:
            if (it["id"], cond) in done:
                continue
            instr = it["instruction_cyrl"] if cond == "cyrl" else it["instruction_latn"]
            prompt = RUBRIC.format(mitigation="", instruction=instr,
                                   response=it["conditions"][cond])
            jobs.append((it["id"], it["tier"], cond, prompt))
    random.seed(61)
    random.shuffle(jobs)
    print(f"{args.judge}: {len(jobs)} Serbian calls ({len(done)} done)", flush=True)

    out = open(out_path, "a")
    if args.judge == "gemini-3.6-flash":
        key = api_key()
        for n, (i, t, c, prompt) in enumerate(jobs, 1):
            text, _, _ = call_gemini("gemini-3.6-flash", prompt, 0.0, key)
            score, reason = parse_score(text)
            out.write(json.dumps({"id": i, "tier": t, "condition": c, "judge": args.judge,
                                  "score": score, "reason": reason}, ensure_ascii=False) + "\n")
            out.flush()
            if n % 50 == 0:
                print(f"  {n}/{len(jobs)}", flush=True)
    else:
        n = 0
        with ThreadPoolExecutor(max_workers=2) as ex:
            futs = {ex.submit(judge_claude, args.judge, p): (i, t, c) for i, t, c, p in jobs}
            for fut in as_completed(futs):
                i, t, c = futs[fut]
                try:
                    text = fut.result()
                except Exception:
                    text = ""
                score, reason = parse_score(text or "")
                out.write(json.dumps({"id": i, "tier": t, "condition": c, "judge": args.judge,
                                      "score": score, "reason": reason}, ensure_ascii=False) + "\n")
                out.flush()
                n += 1
                if n % 50 == 0:
                    print(f"  {n}/{len(jobs)}", flush=True)
    print(f"finished Serbian {args.judge}", flush=True)


if __name__ == "__main__":
    main()
