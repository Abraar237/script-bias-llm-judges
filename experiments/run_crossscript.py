"""Cross-script control: the reviewer's leading benign explanation was that a
romanized response to a Devanagari instruction is a script MISMATCH the judge
correctly flags. Our main arms actually script-match instruction and response
(deva-deva, iast/ascii-iast, hinglish-hinglish), so that explanation does not
apply; this battery measures the mismatch effect directly with the two
deliberately mismatched cells:
  X1: Devanagari instruction + ASCII response   (mismatch)
  X2: IAST instruction + Devanagari response    (mismatch)
The matched baselines (deva-deva, iast-ascii) already exist in the core arms.
Judges: gemini-3.6-flash (native API) and claude-sonnet-5 (headless CLI).

Usage: python3 run_crossscript.py --judge gemini-3.6-flash
       python3 run_crossscript.py --judge claude-sonnet-5
"""
import argparse, json, os, random, subprocess, sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_gemini_judge import RUBRIC, call_gemini, parse_score, api_key as gemini_api_key

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")

CELLS = {
    "deva_instr_ascii_resp": ("instruction_deva", "ascii"),
    "iast_instr_deva_resp": ("instruction_iast", "deva"),
}


def judge_claude(model, prompt):
    p = subprocess.run(["claude", "-p", "--model", model], input=prompt,
                       capture_output=True, text=True, timeout=240)
    return p.stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", required=True, choices=["gemini-3.6-flash", "claude-sonnet-5"])
    args = ap.parse_args()

    items = json.load(open(os.path.join(HERE, "dataset_conditions.json")))
    out_path = os.path.join(RES, f"crossscript_{args.judge}.jsonl")
    done = set()
    if os.path.exists(out_path):
        for line in open(out_path):
            r = json.loads(line)
            if r["score"] is not None:
                done.add((r["id"], r["cell"]))

    jobs = []
    for it in items:
        for cell, (ikey, rcond) in CELLS.items():
            if (it["id"], cell) in done or not it["conditions"].get(rcond):
                continue
            prompt = RUBRIC.format(mitigation="", instruction=it[ikey],
                                   response=it["conditions"][rcond])
            jobs.append((it["id"], it["tier"], cell, prompt))
    random.seed(47)
    random.shuffle(jobs)
    print(f"{args.judge}: {len(jobs)} cross-script calls ({len(done)} done)", flush=True)

    out = open(out_path, "a")
    if args.judge == "gemini-3.6-flash":
        key = gemini_api_key()
        for n, (i, t, cell, prompt) in enumerate(jobs, 1):
            text, _, _ = call_gemini("gemini-3.6-flash", prompt, 0.0, key)
            score, reason = parse_score(text)
            out.write(json.dumps({"id": i, "tier": t, "cell": cell, "judge": args.judge,
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
                out.write(json.dumps({"id": i, "tier": t, "cell": c, "judge": args.judge,
                                      "score": score, "reason": reason}, ensure_ascii=False) + "\n")
                out.flush()
                n += 1
                if n % 50 == 0:
                    print(f"  {n}/{len(jobs)}", flush=True)
    print(f"finished cross-script {args.judge}", flush=True)


if __name__ == "__main__":
    main()
