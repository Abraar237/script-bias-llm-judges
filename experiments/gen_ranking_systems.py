"""Ranking-flip demo, step 1: three real systems answer 50 stratified Hindi
instructions in Devanagari. Systems: qwen/qwen-2.5-7b-instruct (OpenRouter),
gemini-3.6-flash and gemini-3.1-pro-preview (native API). Responses are then
rendered to ASCII deterministically (step 2 happens in run_ranking_judge.py).
Writes experiments/ranking_responses.json.

Usage: python3 gen_ranking_systems.py --system <name>   (run once per system)
       python3 gen_ranking_systems.py --finalize        (render ascii, merge)
"""
import argparse, json, os, random, sys, time, unicodedata
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_gemini_judge import call_gemini, api_key as gemini_api_key
from run_openrouter_judge import api_key as or_api_key, log_call
from indic_transliteration import sanscript

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "ranking_raw")
OUT = os.path.join(HERE, "ranking_responses.json")
os.makedirs(RAW, exist_ok=True)

GEN_PROMPT = ("निम्नलिखित निर्देश का उत्तर हिंदी में, देवनागरी लिपि में दें। "
              "उत्तर 60 से 120 शब्दों में हो।\n\nनिर्देश: {instruction}")

SYSTEMS = ["qwen-2.5-7b", "gemini-3.6-flash", "gemini-3.1-pro-preview"]


def pick_items():
    items = json.load(open(os.path.join(HERE, "dataset_conditions.json")))
    random.seed(67)
    # 50 instructions, stratified by original tier for topical spread
    return (random.sample([i for i in items if i["tier"] == "high"], 17)
            + random.sample([i for i in items if i["tier"] == "medium"], 17)
            + random.sample([i for i in items if i["tier"] == "low"], 16))


def call_qwen_or(prompt, key):
    body = {"model": "qwen/qwen-2.5-7b-instruct",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3, "max_tokens": 500}
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    for attempt in range(7):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                d = json.load(r)
            u = d.get("usage", {})
            log_call("qwen/qwen-2.5-7b-instruct", u.get("prompt_tokens", 0), u.get("completion_tokens", 0))
            return d["choices"][0]["message"].get("content") or ""
        except Exception:
            if attempt == 6:
                raise
            time.sleep(min(5 * (2 ** attempt), 60))


def gen(system):
    items = pick_items()
    path = os.path.join(RAW, f"{system}.jsonl")
    done = set()
    if os.path.exists(path):
        for line in open(path):
            done.add(json.loads(line)["id"])
    todo = [it for it in items if it["id"] not in done]
    print(f"{system}: {len(todo)} generations to run", flush=True)
    okey = or_api_key() if system == "qwen-2.5-7b" else None
    gkey = gemini_api_key() if system != "qwen-2.5-7b" else None
    with open(path, "a") as out:
        for n, it in enumerate(todo, 1):
            prompt = GEN_PROMPT.format(instruction=it["instruction_deva"])
            if system == "qwen-2.5-7b":
                text = call_qwen_or(prompt, okey)
            else:
                text, _, _ = call_gemini(system, prompt, 0.3, gkey)
            out.write(json.dumps({"id": it["id"], "system": system,
                                  "response_deva": text.strip()}, ensure_ascii=False) + "\n")
            out.flush()
            if n % 10 == 0:
                print(f"  {n}/{len(todo)}", flush=True)
    print(f"{system} generation done", flush=True)


def strip_diacritics(t):
    norm = unicodedata.normalize("NFD", t)
    return unicodedata.normalize("NFC", "".join(c for c in norm if not unicodedata.combining(c))).replace("ṁ", "m")


def finalize():
    items = {it["id"]: it for it in pick_items()}
    merged = []
    for system in SYSTEMS:
        path = os.path.join(RAW, f"{system}.jsonl")
        for line in open(path):
            r = json.loads(line)
            deva = r["response_deva"]
            iast = sanscript.transliterate(deva, sanscript.DEVANAGARI, sanscript.IAST)
            merged.append({"id": r["id"], "system": system,
                           "instruction_deva": items[r["id"]]["instruction_deva"],
                           "instruction_iast": items[r["id"]]["instruction_iast"],
                           "response_deva": deva,
                           "response_ascii": strip_diacritics(iast)})
    json.dump(merged, open(OUT, "w"), ensure_ascii=False, indent=1)
    print(f"wrote {OUT}: {len(merged)} system-responses", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", choices=SYSTEMS)
    ap.add_argument("--finalize", action="store_true")
    args = ap.parse_args()
    if args.finalize:
        finalize()
    else:
        gen(args.system)
