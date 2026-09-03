"""Judge the Gemini-authored replication set (deva/iast/ascii, one item per
call, script-matched instructions) with the two judges whose results carry the
self-preference question: claude-sonnet-5 (headless CLI, the judge with the
-12.3 penalty) and gemini-3.6-flash (native API, the judge with the inflation).

Usage: python3 run_replication_judge.py --judge claude-sonnet-5
       python3 run_replication_judge.py --judge gemini-3.6-flash
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

    items = json.load(open(os.path.join(HERE, "replication_conditions.json")))
    out_path = os.path.join(RES, f"replication_{args.judge}.jsonl")
    done = set()
    if os.path.exists(out_path):
        for line in open(out_path):
            r = json.loads(line)
            if r["score"] is not None:
                done.add((r["id"], r["condition"]))

    jobs = []
    for it in items:
        for cond in ["deva", "iast", "ascii"]:
            if (it["id"], cond) in done or not it["conditions"].get(cond):
                continue
            instr = it["instruction_deva"] if cond == "deva" else it["instruction_iast"]
            prompt = RUBRIC.format(mitigation="", instruction=instr,
                                   response=it["conditions"][cond])
            jobs.append((it["id"], it["tier"], cond, prompt))
    random.seed(59)
    random.shuffle(jobs)
    print(f"{args.judge}: {len(jobs)} replication calls ({len(done)} done)", flush=True)

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
    print(f"finished replication {args.judge}", flush=True)


if __name__ == "__main__":
    main()
