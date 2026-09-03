"""Pairwise deva-vs-ascii preference for the remaining five judges, so the
pairwise battery covers all seven (Flash and Sonnet already ran). Same design:
identical content, both presentation orders, tie allowed, 300 trials/judge.
Interfaces: gemini-3.1-pro-preview native; claude-opus-5 / claude-fable-5
headless CLI; gpt-5.6-terra and qwen-2.5-7b via OpenRouter (spend-capped).

Usage: python3 run_pairwise_ext.py --judge <name>
"""
import argparse, json, os, random, re, subprocess, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_gemini_judge import call_gemini, api_key as gemini_api_key
from run_pairwise import PROMPT, parse
from run_openrouter_judge import api_key as or_api_key, log_call, PRICING

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")

OR_MODELS = {"gpt-5.6-terra": "openai/gpt-5.6-terra",
             "qwen-2.5-7b": "qwen/qwen-2.5-7b-instruct"}
CLI_MODELS = ["claude-opus-5", "claude-fable-5"]


def call_or(model, prompt, key):
    body = {"model": model, "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0, "max_tokens": 700}
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    for attempt in range(7):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                d = json.load(r)
            u = d.get("usage", {})
            log_call(model, u.get("prompt_tokens", 0), u.get("completion_tokens", 0))
            return d["choices"][0]["message"].get("content") or ""
        except Exception:
            if attempt == 6:
                raise
            time.sleep(min(5 * (2 ** attempt), 60))


def call_cli(model, prompt):
    p = subprocess.run(["claude", "-p", "--model", model], input=prompt,
                       capture_output=True, text=True, timeout=240)
    return p.stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", required=True,
                    choices=["gemini-3.1-pro-preview"] + CLI_MODELS + list(OR_MODELS))
    args = ap.parse_args()

    items = json.load(open(os.path.join(HERE, "dataset_conditions.json")))
    out_path = os.path.join(RES, f"pairwise_{args.judge}.jsonl")
    done = set()
    if os.path.exists(out_path):
        for line in open(out_path):
            r = json.loads(line)
            if r["winner"] is not None:
                done.add((r["id"], r["order"]))

    jobs = []
    for it in items:
        if not (it["conditions"].get("deva") and it["conditions"].get("ascii")):
            continue
        for order in ["deva_first", "ascii_first"]:
            if (it["id"], order) not in done:
                jobs.append((it, order))
    random.seed(41)
    random.shuffle(jobs)
    print(f"{args.judge}: {len(jobs)} pairwise calls ({len(done)} done)", flush=True)

    gkey = gemini_api_key() if args.judge == "gemini-3.1-pro-preview" else None
    okey = or_api_key() if args.judge in OR_MODELS else None

    def build(it, order):
        deva, ascii_ = it["conditions"]["deva"], it["conditions"]["ascii"]
        a, b = (deva, ascii_) if order == "deva_first" else (ascii_, deva)
        return PROMPT.format(instruction=it["instruction_deva"], a=a, b=b)

    def record(out, it, order, winner, reason):
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

    out = open(out_path, "a")
    if args.judge in CLI_MODELS:
        n = 0
        with ThreadPoolExecutor(max_workers=2) as ex:
            futs = {ex.submit(call_cli, args.judge, build(it, o)): (it, o) for it, o in jobs}
            for fut in as_completed(futs):
                it, o = futs[fut]
                try:
                    text = fut.result()
                except Exception:
                    text = ""
                winner, reason = parse(text or "")
                record(out, it, o, winner, reason)
                n += 1
                if n % 50 == 0:
                    print(f"  {n}/{len(jobs)}", flush=True)
    else:
        for n, (it, o) in enumerate(jobs, 1):
            prompt = build(it, o)
            if args.judge == "gemini-3.1-pro-preview":
                text, _, _ = call_gemini("gemini-3.1-pro-preview", prompt, 0.0, gkey)
            else:
                text = call_or(OR_MODELS[args.judge], prompt, okey)
            winner, reason = parse(text)
            record(out, it, o, winner, reason)
            if n % 50 == 0:
                print(f"  {n}/{len(jobs)}", flush=True)
    print(f"finished pairwise {args.judge}", flush=True)


if __name__ == "__main__":
    main()
