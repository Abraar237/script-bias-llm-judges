"""Sub-dimension diagnostic via NATIVE interfaces only (no OpenRouter, no Claude
billing through the OpenRouter key): Gemini Flash through its native API,
Claude Sonnet through the headless `claude -p` CLI (subscription-billed, same
interface as the primary Table 1 Sonnet numbers). Decomposed 4-way rubric
(reused verbatim from run_gemini_judge.py's RUBRIC_R1) on the MAIN (no
mitigation-instruction) condition, all four orthographies. Targets whether
Sonnet's ASCII penalty is a clarity effect or a correctness/completeness/
helpfulness effect.

Usage: python3 run_subdim_native.py --model gemini-3.6-flash
       python3 run_subdim_native.py --model claude-sonnet-5
"""
import argparse, json, os, random, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_gemini_judge import RUBRIC_R1, call_gemini, api_key as gemini_api_key

HERE = os.path.dirname(os.path.abspath(__file__))
DATASET = os.path.join(HERE, "dataset_conditions.json")
RESULTS_DIR = os.path.join(HERE, "..", "results")


def parse_sub(text):
    if not text:
        return {"correctness": None, "completeness": None, "helpfulness": None, "clarity": None}
    out = {}
    for k in ["correctness", "completeness", "helpfulness", "clarity"]:
        m = re.search(rf'"{k}"\s*:\s*(\d+)', text)
        out[k] = int(m.group(1)) if m and 0 <= int(m.group(1)) <= 25 else None
    return out


def build_jobs(items, done):
    jobs = []
    for it in items:
        for cond in ["deva", "iast", "ascii", "hinglish"]:
            if (it["id"], cond) in done or not it["conditions"].get(cond):
                continue
            instr = it["instruction_deva"] if cond == "deva" else (
                it.get("instruction_hinglish") or it["instruction_iast"] if cond == "hinglish" else it["instruction_iast"])
            prompt = RUBRIC_R1.format(mitigation="", instruction=instr, response=it["conditions"][cond])
            jobs.append((it["id"], it["tier"], cond, prompt))
    return jobs


def run_gemini(args, items, out_path, done):
    key = gemini_api_key()
    jobs = build_jobs(items, done)
    random.seed(31)
    random.shuffle(jobs)
    print(f"gemini-3.6-flash: {len(jobs)} sub-dim calls ({len(done)} done)", flush=True)
    with open(out_path, "a") as out:
        for n, (i, t, c, prompt) in enumerate(jobs, 1):
            text, _, _ = call_gemini("gemini-3.6-flash", prompt, 0.0, key)
            sub = parse_sub(text)
            out.write(json.dumps({"id": i, "tier": t, "condition": c,
                                  "model": "gemini-3.6-flash", **sub}, ensure_ascii=False) + "\n")
            out.flush()
            if n % 50 == 0:
                print(f"  {n}/{len(jobs)}", flush=True)


def judge_one_claude(model, prompt):
    p = subprocess.run(["claude", "-p", "--model", model], input=prompt,
                       capture_output=True, text=True, timeout=240)
    return p.stdout.strip()


def run_claude(args, items, out_path, done):
    jobs = build_jobs(items, done)
    random.seed(31)
    random.shuffle(jobs)
    print(f"{args.model}: {len(jobs)} sub-dim calls ({len(done)} done)", flush=True)
    out = open(out_path, "a")
    n = 0
    with ThreadPoolExecutor(max_workers=2) as ex:
        futs = {ex.submit(judge_one_claude, args.model, p): (i, t, c) for i, t, c, p in jobs}
        for fut in as_completed(futs):
            i, t, c = futs[fut]
            try:
                text = fut.result()
            except Exception as e:
                text = None
            sub = parse_sub(text)
            out.write(json.dumps({"id": i, "tier": t, "condition": c,
                                  "model": args.model, **sub}, ensure_ascii=False) + "\n")
            out.flush()
            n += 1
            if n % 50 == 0:
                print(f"  {n}/{len(jobs)}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=["gemini-3.6-flash", "claude-sonnet-5"])
    args = ap.parse_args()

    items = json.load(open(DATASET))
    safe = args.model.replace("/", "_")
    out_path = os.path.join(RESULTS_DIR, f"subdim_native_{safe}.jsonl")
    done = set()
    if os.path.exists(out_path):
        for line in open(out_path):
            r = json.loads(line)
            done.add((r["id"], r["condition"]))

    if args.model == "gemini-3.6-flash":
        run_gemini(args, items, out_path, done)
    else:
        run_claude(args, items, out_path, done)
    print(f"finished {args.model} native sub-dim battery", flush=True)


if __name__ == "__main__":
    main()
