"""Author a 51-item replication set with a NON-Claude model (Gemini 3.1 Pro)
to break the self-preference confound: the original 150 items were authored by
a Claude-family model, and a self-recognition account predicts the Claude
judges' Devanagari preference. If Sonnet's ASCII penalty replicates on items
no Claude model wrote, self-preference is excluded as the driver.

17 items per tier, same tier definitions as the original set, Devanagari.
IAST/ASCII rendered deterministically (same code as render_conditions.py).
Hinglish omitted: the replication targets the ASCII penalty specifically.
Writes experiments/replication_conditions.json.
"""
import json, os, re, sys, unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_gemini_judge import api_key
from indic_transliteration import sanscript

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "replication_conditions.json")

def call_gen(model, prompt, temp, key):
    """Generation-sized call: authoring needs far more output room than judging."""
    import urllib.request, time as _time
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temp, "maxOutputTokens": 8000,
                             "thinkingConfig": {"thinkingLevel": "LOW"}},
    }
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        data=json.dumps(body).encode(),
        headers={"x-goog-api-key": key, "Content-Type": "application/json"})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.load(r)
            return d["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            if attempt == 5:
                raise
            _time.sleep(min(5 * (2 ** attempt), 60))


TIER_SPECS = {
    "high": "correct, complete, well-organised, 80 to 140 words",
    "medium": "factually correct but visibly incomplete for what the instruction asks, 40 to 80 words",
    "low": "curt, vague, or trivially shallow, 15 to 40 words; one or two items may contain a minor factual error",
}
DOMAINS = ["science", "history", "cooking", "health", "technology", "culture",
           "geography", "personal finance", "daily-life advice", "education"]

GEN_PROMPT = (
    "You are creating Hindi evaluation data. Write {n} instruction-response pairs "
    "in HINDI (Devanagari script only). Domains to draw from: {domains}.\n"
    "Each response must be of {tier} quality: {spec}.\n"
    "Do not number them in the text. Reply with ONLY a JSON array: "
    '[{{"instruction": "<Hindi instruction in Devanagari>", "response": "<Hindi response in Devanagari>", "domain": "<domain>"}}, ...]'
)


def to_iast(t):
    return sanscript.transliterate(t, sanscript.DEVANAGARI, sanscript.IAST)


def strip_diacritics(t):
    norm = unicodedata.normalize("NFD", t)
    return unicodedata.normalize("NFC", "".join(c for c in norm if not unicodedata.combining(c))).replace("ṁ", "m")


def main():
    key = api_key()
    items = []
    for tier, spec in TIER_SPECS.items():
        got = []
        attempts = 0
        while len(got) < 17 and attempts < 6:
            attempts += 1
            prompt = GEN_PROMPT.format(n=5, domains=", ".join(DOMAINS), tier=tier, spec=spec)
            text = call_gen("gemini-3.1-pro-preview", prompt, 0.9, key)
            m = re.search(r"\[.*\]", text, re.S)
            if not m:
                continue
            try:
                batch = json.loads(m.group(0))
            except json.JSONDecodeError:
                continue
            for b in batch:
                instr, resp = b.get("instruction", ""), b.get("response", "")
                # must actually be Devanagari
                if sum(1 for c in resp if "ऀ" <= c <= "ॿ") < len(resp) * 0.5:
                    continue
                got.append({"instruction": instr, "response": resp,
                            "domain": b.get("domain", "")})
            print(f"{tier}: {len(got)} collected", flush=True)
        for k, it in enumerate(got[:17]):
            iast = to_iast(it["response"])
            items.append({
                "id": f"R{tier[0].upper()}{k:02d}", "tier": tier, "domain": it["domain"],
                "author_model": "gemini-3.1-pro-preview",
                "instruction_deva": it["instruction"],
                "instruction_iast": to_iast(it["instruction"]),
                "conditions": {
                    "deva": it["response"],
                    "iast": iast,
                    "ascii": strip_diacritics(iast),
                },
            })
    json.dump(items, open(OUT, "w"), ensure_ascii=False, indent=1)
    print(f"wrote {OUT}: {len(items)} items", flush=True)


if __name__ == "__main__":
    main()
