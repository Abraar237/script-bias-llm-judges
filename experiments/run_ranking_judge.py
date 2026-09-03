"""Ranking-flip demo, step 2: Claude Sonnet 5 (not one of the three systems,
so no self-judging) scores every system response in both scripts, one item per
call, script-matched instructions. 3 systems x 50 items x 2 scripts = 300
calls. The analysis then compares the system ranking on the Devanagari slice
with the ranking on the ASCII slice.
"""
import json, os, random, subprocess, sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_gemini_judge import RUBRIC, parse_score

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")

rows = json.load(open(os.path.join(HERE, "ranking_responses.json")))
out_path = os.path.join(RES, "ranking_claude-sonnet-5.jsonl")
done = set()
if os.path.exists(out_path):
    for line in open(out_path):
        r = json.loads(line)
        if r["score"] is not None:
            done.add((r["id"], r["system"], r["script"]))


def judge(prompt):
    p = subprocess.run(["claude", "-p", "--model", "claude-sonnet-5"], input=prompt,
                       capture_output=True, text=True, timeout=240)
    return p.stdout.strip()


jobs = []
for r in rows:
    for script in ["deva", "ascii"]:
        if (r["id"], r["system"], script) in done:
            continue
        instr = r["instruction_deva"] if script == "deva" else r["instruction_iast"]
        resp = r["response_deva"] if script == "deva" else r["response_ascii"]
        prompt = RUBRIC.format(mitigation="", instruction=instr, response=resp)
        jobs.append((r["id"], r["system"], script, prompt))
random.seed(71)
random.shuffle(jobs)
print(f"{len(jobs)} ranking-judge calls ({len(done)} done)", flush=True)

out = open(out_path, "a")
n = 0
with ThreadPoolExecutor(max_workers=2) as ex:
    futs = {ex.submit(judge, p): (i, sysname, sc) for i, sysname, sc, p in jobs}
    for fut in as_completed(futs):
        i, sysname, sc = futs[fut]
        try:
            text = fut.result()
        except Exception:
            text = ""
        score, reason = parse_score(text or "")
        out.write(json.dumps({"id": i, "system": sysname, "script": sc,
                              "score": score, "reason": reason}, ensure_ascii=False) + "\n")
        out.flush()
        n += 1
        if n % 50 == 0:
            print(f"  {n}/{len(jobs)}", flush=True)
print("ranking-judge battery done", flush=True)
