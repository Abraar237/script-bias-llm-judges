"""Rerun the Claude judge arm the way the reviewer demanded: headless `claude -p`,
one item per call, fresh context every call, pinned model id, randomized order.
Resume-safe: skips (id, condition) pairs already in the output file.

Usage: python3 run_claude_headless.py --model claude-sonnet-5 [--workers 6] [--limit N]
"""
import argparse, json, os, random, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor, as_completed

HERE = os.path.dirname(os.path.abspath(__file__))
DATASET = os.path.join(HERE, "dataset_conditions.json")
RES = os.path.join(HERE, "..", "results")

RUBRIC = (
    "You are grading one response to one instruction for an instruction-following benchmark.\n"
    "Score the response from 0 to 100 considering: correctness (facts right), "
    "completeness (covers what the instruction asks), helpfulness, and clarity.\n"
    "Judge this item on its own merits.\n"
    "Instruction:\n{instruction}\n\nResponse:\n{response}\n\n"
    'Reply with ONLY a JSON object: {{"score": <integer 0-100>, "reason": "<one short sentence>"}}'
)


def judge_one(model, prompt):
    p = subprocess.run(["claude", "-p", "--model", model], input=prompt,
                       capture_output=True, text=True, timeout=240)
    return p.stdout.strip()


def parse(text):
    m = re.search(r'"score"\s*:\s*(\d+)', text)
    if m and 0 <= int(m.group(1)) <= 100:
        rm = re.search(r'"reason"\s*:\s*"([^"]*)"', text)
        return int(m.group(1)), (rm.group(1) if rm else "")
    return None, text[:150]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    items = json.load(open(DATASET))
    out_path = os.path.join(RES, f"scores_claude-api_{args.model}.jsonl")
    done = set()
    if os.path.exists(out_path):
        for line in open(out_path):
            r = json.loads(line)
            done.add((r["id"], r["condition"]))

    jobs = []
    for it in items:
        for cond in ["deva", "iast", "ascii", "hinglish"]:
            if (it["id"], cond) in done or not it["conditions"].get(cond):
                continue
            if cond == "deva":
                instr = it["instruction_deva"]
            elif cond == "hinglish":
                instr = it.get("instruction_hinglish") or it["instruction_iast"]
            else:
                instr = it["instruction_iast"]
            prompt = RUBRIC.format(instruction=instr, response=it["conditions"][cond])
            jobs.append((it["id"], it["tier"], cond, prompt))
    random.seed(23)
    random.shuffle(jobs)
    if args.limit:
        jobs = jobs[: args.limit]
    print(f"{args.model}: {len(jobs)} calls to run ({len(done)} already done)", flush=True)

    out = open(out_path, "a")
    n_ok = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(judge_one, args.model, p): (i, t, c) for i, t, c, p in jobs}
        for k, fut in enumerate(as_completed(futs), 1):
            i, t, c = futs[fut]
            try:
                text = fut.result()
                score, reason = parse(text)
            except Exception as e:
                score, reason = None, f"ERROR {e}"
            out.write(json.dumps({"id": i, "tier": t, "condition": c,
                                  "model": args.model, "protocol": "headless-one-per-call",
                                  "score": score, "reason": reason}, ensure_ascii=False) + "\n")
            out.flush()
            n_ok += score is not None
            if k % 50 == 0:
                print(f"  {k}/{len(jobs)} done ({n_ok} parsed)", flush=True)
    print(f"finished {args.model}: {n_ok}/{len(jobs)} parsed", flush=True)


if __name__ == "__main__":
    main()
