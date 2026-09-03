"""Temperature decomposition within a fixed interface: Sonnet via the OpenRouter
gateway with NO temperature parameter (provider default sampling), deva+ascii
only. With gateway@t0 (-3.64) and CLI@default (-12.29) already measured, this
supplies the third cell of the interface x temperature decomposition the
review asked for (the fourth, CLI@t0, is impossible: the CLI has no knob)."""
import json, os, random, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_gemini_judge import RUBRIC, parse_score
from run_openrouter_judge import api_key, log_call

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")

def call_or_default(prompt, key):
    body = {"model": "anthropic/claude-sonnet-5",
            "messages": [{"role": "user", "content": prompt}], "max_tokens": 700}
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    for attempt in range(7):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                d = json.load(r)
            u = d.get("usage", {})
            log_call("anthropic/claude-sonnet-5", u.get("prompt_tokens", 0), u.get("completion_tokens", 0))
            return d["choices"][0]["message"].get("content") or ""
        except Exception:
            if attempt == 6:
                raise
            time.sleep(min(5 * (2 ** attempt), 60))

items = json.load(open(os.path.join(HERE, "dataset_conditions.json")))
out_path = os.path.join(RES, "gateway_default_claude-sonnet-5.jsonl")
done = set()
if os.path.exists(out_path):
    for line in open(out_path):
        r = json.loads(line)
        if r["score"] is not None:
            done.add((r["id"], r["condition"]))
key = api_key()
jobs = []
for it in items:
    for cond in ["deva", "ascii"]:
        if (it["id"], cond) in done:
            continue
        instr = it["instruction_deva"] if cond == "deva" else it["instruction_iast"]
        jobs.append((it["id"], it["tier"], cond,
                     RUBRIC.format(mitigation="", instruction=instr, response=it["conditions"][cond])))
random.seed(79)
random.shuffle(jobs)
print(f"{len(jobs)} gateway-default calls", flush=True)
with open(out_path, "a") as out:
    for n, (i, t, c, prompt) in enumerate(jobs, 1):
        text = call_or_default(prompt, key)
        score, reason = parse_score(text)
        out.write(json.dumps({"id": i, "tier": t, "condition": c,
                              "score": score, "reason": reason}, ensure_ascii=False) + "\n")
        out.flush()
        if n % 50 == 0:
            print(f"  {n}/{len(jobs)}", flush=True)
print("gateway-default arm done", flush=True)
