"""Unified single-interface judge battery via OpenRouter: every judge family
(Gemini, Qwen, Claude, GPT) called through the SAME OpenAI-compatible endpoint
at the SAME pinned temperature=0, one item per call, randomized, resume-safe.
This directly controls the interface+sampling confound the review flagged,
and adds a GPT-family judge. Kept as a SEPARATE controlled-comparison arm from
the primary Table 1 results (which used each provider's native API/CLI).

Usage: python3 run_openrouter_judge.py --model openai/gpt-5.6-terra [--limit N]
"""
import argparse, json, os, random, re, sys, time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATASET = os.path.join(HERE, "dataset_conditions.json")
RESULTS_DIR = os.path.join(HERE, "..", "results")
ENV = os.path.join(HERE, "..", ".env")

RUBRIC = (
    "You are grading one response to one instruction for an instruction-following benchmark.\n"
    "Score the response from 0 to 100 considering: correctness (facts right), "
    "completeness (covers what the instruction asks), helpfulness, and clarity.\n"
    "Judge this item on its own merits.\n"
    "Instruction:\n{instruction}\n\nResponse:\n{response}\n\n"
    'Reply with ONLY a JSON object: {{"score": <integer 0-100>, "reason": "<one short sentence>"}}'
)

# per-1M-token pricing snapshot (OpenRouter, checked 2026-09-03) for the spend tracker
PRICING = {
    "anthropic/claude-sonnet-5": {"in": 2.00, "out": 10.00},
    "anthropic/claude-opus-5":   {"in": 5.00, "out": 25.00},
    "anthropic/claude-fable-5":  {"in": 10.00, "out": 50.00},
    "google/gemini-3.6-flash":   {"in": 0.75, "out": 3.75},
    "google/gemini-3.1-pro-preview": {"in": 2.00, "out": 12.00},
    "qwen/qwen-2.5-7b-instruct": {"in": 0.10, "out": 0.20},
    "openai/gpt-5.6-terra":      {"in": 2.00, "out": 12.00},
}
CAP_USD = 20.0  # hard stop for this OpenRouter battery specifically


def api_key():
    for line in open(ENV):
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"\'')
    raise RuntimeError("OPENROUTER_API_KEY not found in research/.env")


def spend_log_path():
    return os.path.join(RESULTS_DIR, "spend_log_openrouter.jsonl")


def log_call(model, tin, tout):
    p = PRICING[model]
    cost = (tin * p["in"] + tout * p["out"]) / 1e6
    with open(spend_log_path(), "a") as f:
        f.write(json.dumps({"model": model, "in": tin, "out": tout, "cost_usd": round(cost, 6)}) + "\n")
    total = spent()
    if total > CAP_USD:
        raise RuntimeError(f"OpenRouter battery SPEND CAP HIT: ${total:.2f} > ${CAP_USD}")
    return total


def spent():
    p = spend_log_path()
    if not os.path.exists(p):
        return 0.0
    return sum(json.loads(l)["cost_usd"] for l in open(p) if l.strip())


def call_openrouter(model, prompt, key):
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": 700,
    }
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    for attempt in range(7):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                d = json.load(r)
            text = d["choices"][0]["message"].get("content") or ""
            u = d.get("usage", {})
            return text, u.get("prompt_tokens", 0), u.get("completion_tokens", 0)
        except Exception as e:
            if attempt == 6:
                raise
            time.sleep(min(5 * (2 ** attempt), 60))


def parse_score(text):
    m = re.search(r'"score"\s*:\s*(\d+)', text)
    if m:
        s = int(m.group(1))
        if 0 <= s <= 100:
            rm = re.search(r'"reason"\s*:\s*"([^"]*)"', text)
            return s, (rm.group(1) if rm else "")
    return None, text[:150]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=list(PRICING))
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    key = api_key()
    items = json.load(open(DATASET))
    if args.limit:
        items = items[: args.limit]

    safe_name = args.model.replace("/", "_")
    out_path = os.path.join(RESULTS_DIR, f"scores_openrouter_{safe_name}.jsonl")
    done = set()
    if os.path.exists(out_path):
        for line in open(out_path):
            r = json.loads(line)
            done.add((r["id"], r["condition"]))

    jobs = [(it, c) for it in items for c in ["deva", "iast", "ascii", "hinglish"]
            if it["conditions"].get(c) and (it["id"], c) not in done]
    random.seed(29)
    random.shuffle(jobs)
    print(f"{args.model}: {len(jobs)} calls to run ({len(done)} already done). Spend so far ${spent():.3f}", flush=True)

    with open(out_path, "a") as out:
        for n, (it, cond) in enumerate(jobs, 1):
            if cond == "deva":
                instr = it["instruction_deva"]
            elif cond == "hinglish":
                instr = it.get("instruction_hinglish") or it["instruction_iast"]
            else:
                instr = it["instruction_iast"]
            prompt = RUBRIC.format(instruction=instr, response=it["conditions"][cond])
            text, tin, tout = call_openrouter(args.model, prompt, key)
            total = log_call(args.model, tin, tout)
            score, reason = parse_score(text)
            out.write(json.dumps({"id": it["id"], "tier": it["tier"], "condition": cond,
                                  "model": args.model, "protocol": "openrouter-unified-temp0",
                                  "score": score, "reason": reason}, ensure_ascii=False) + "\n")
            out.flush()
            if n % 50 == 0:
                print(f"  {n}/{len(jobs)} done, ${total:.3f} spent", flush=True)
    print(f"finished {args.model}. total OpenRouter spend ${spent():.3f}", flush=True)


if __name__ == "__main__":
    main()
