"""ASCII-instruction control: the review noted the ascii response cell pairs
with the IAST (diacritic-bearing) instruction, a residual within-romanization
mismatch. Rerun the ascii condition with the instruction ALSO diacritic-
stripped, so instruction and response share the identical orthography.
Judges: gemini-3.6-flash (native) and claude-sonnet-5 (CLI). 150 calls each.

Usage: python3 run_ascii_instr.py --judge gemini-3.6-flash|claude-sonnet-5
"""
import argparse, json, os, random, subprocess, sys, unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_gemini_judge import RUBRIC, call_gemini, parse_score, api_key

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")


def strip_diacritics(t):
    norm = unicodedata.normalize("NFD", t)
    return unicodedata.normalize("NFC", "".join(c for c in norm if not unicodedata.combining(c))).replace("ṁ", "m")


def judge_claude(prompt):
    p = subprocess.run(["claude", "-p", "--model", "claude-sonnet-5"], input=prompt,
                       capture_output=True, text=True, timeout=240)
    return p.stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", required=True, choices=["gemini-3.6-flash", "claude-sonnet-5"])
    args = ap.parse_args()

    items = json.load(open(os.path.join(HERE, "dataset_conditions.json")))
    out_path = os.path.join(RES, f"ascii_instr_{args.judge}.jsonl")
    done = set()
    if os.path.exists(out_path):
        for line in open(out_path):
            r = json.loads(line)
            if r["score"] is not None:
                done.add(r["id"])

    jobs = []
    for it in items:
        if it["id"] in done or not it["conditions"].get("ascii"):
            continue
        instr = strip_diacritics(it["instruction_iast"])
        prompt = RUBRIC.format(mitigation="", instruction=instr,
                               response=it["conditions"]["ascii"])
        jobs.append((it["id"], it["tier"], prompt))
    random.seed(73)
    random.shuffle(jobs)
    print(f"{args.judge}: {len(jobs)} ascii-instruction calls", flush=True)

    out = open(out_path, "a")
    if args.judge == "gemini-3.6-flash":
        key = api_key()
        for n, (i, t, prompt) in enumerate(jobs, 1):
            text, _, _ = call_gemini("gemini-3.6-flash", prompt, 0.0, key)
            score, reason = parse_score(text)
            out.write(json.dumps({"id": i, "tier": t, "condition": "ascii_instr_ascii",
                                  "judge": args.judge, "score": score, "reason": reason},
                                 ensure_ascii=False) + "\n")
            out.flush()
            if n % 50 == 0:
                print(f"  {n}/{len(jobs)}", flush=True)
    else:
        n = 0
        with ThreadPoolExecutor(max_workers=2) as ex:
            futs = {ex.submit(judge_claude, p): (i, t) for i, t, p in jobs}
            for fut in as_completed(futs):
                i, t = futs[fut]
                try:
                    text = fut.result()
                except Exception:
                    text = ""
                score, reason = parse_score(text or "")
                out.write(json.dumps({"id": i, "tier": t, "condition": "ascii_instr_ascii",
                                      "judge": args.judge, "score": score, "reason": reason},
                                     ensure_ascii=False) + "\n")
                out.flush()
                n += 1
                if n % 50 == 0:
                    print(f"  {n}/{len(jobs)}", flush=True)
    print(f"finished ascii-instruction {args.judge}", flush=True)


if __name__ == "__main__":
    main()
