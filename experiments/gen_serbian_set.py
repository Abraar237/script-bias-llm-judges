"""Second digraphic language: Serbian. Author ~51 instruction-response pairs
in Serbian Cyrillic at the same three quality tiers as the Hindi set (Gemini
3.1 Pro authors; non-Claude, so the self-preference exposure does not recur),
then render each in Gaj's Latin alphabet via the official 1:1 mapping, which
is lossless in both directions (no diacritic-stripping objection possible).
Writes experiments/serbian_conditions.json with conditions {cyrl, latn}.
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_gemini_judge import api_key

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "serbian_conditions.json")

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


# Gaj's Latin alphabet mapping (digraphs first)
PAIRS = [("Љ", "Lj"), ("Њ", "Nj"), ("Џ", "Dž"), ("љ", "lj"), ("њ", "nj"), ("џ", "dž"),
         ("А", "A"), ("Б", "B"), ("В", "V"), ("Г", "G"), ("Д", "D"), ("Ђ", "Đ"),
         ("Е", "E"), ("Ж", "Ž"), ("З", "Z"), ("И", "I"), ("Ј", "J"), ("К", "K"),
         ("Л", "L"), ("М", "M"), ("Н", "N"), ("О", "O"), ("П", "P"), ("Р", "R"),
         ("С", "S"), ("Т", "T"), ("Ћ", "Ć"), ("У", "U"), ("Ф", "F"), ("Х", "H"),
         ("Ц", "C"), ("Ч", "Č"), ("Ш", "Š"),
         ("а", "a"), ("б", "b"), ("в", "v"), ("г", "g"), ("д", "d"), ("ђ", "đ"),
         ("е", "e"), ("ж", "ž"), ("з", "z"), ("и", "i"), ("ј", "j"), ("к", "k"),
         ("л", "l"), ("м", "m"), ("н", "n"), ("о", "o"), ("п", "p"), ("р", "r"),
         ("с", "s"), ("т", "t"), ("ћ", "ć"), ("у", "u"), ("ф", "f"), ("х", "h"),
         ("ц", "c"), ("ч", "č"), ("ш", "š")]


def to_latin(t):
    for c, l in PAIRS:
        t = t.replace(c, l)
    return t


TIER_SPECS = {
    "high": "correct, complete, well-organised, 80 to 140 words",
    "medium": "factually correct but visibly incomplete for what the instruction asks, 40 to 80 words",
    "low": "curt, vague, or trivially shallow, 15 to 40 words; one or two items may contain a minor factual error",
}
DOMAINS = ["science", "history", "cooking", "health", "technology", "culture",
           "geography", "personal finance", "daily-life advice", "education"]

GEN_PROMPT = (
    "You are creating Serbian evaluation data. Write {n} instruction-response pairs "
    "in SERBIAN, Cyrillic script only. Domains to draw from: {domains}.\n"
    "Each response must be of {tier} quality: {spec}.\n"
    "Reply with ONLY a JSON array: "
    '[{{"instruction": "<Serbian instruction in Cyrillic>", "response": "<Serbian response in Cyrillic>", "domain": "<domain>"}}, ...]'
)


def cyrillic_share(t):
    letters = [c for c in t if c.isalpha()]
    if not letters:
        return 0
    return sum(1 for c in letters if "Ѐ" <= c <= "ӿ") / len(letters)


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
                if cyrillic_share(b.get("response", "")) < 0.9:
                    continue
                got.append(b)
            print(f"{tier}: {len(got)} collected", flush=True)
        for k, it in enumerate(got[:17]):
            items.append({
                "id": f"S{tier[0].upper()}{k:02d}", "tier": tier, "domain": it.get("domain", ""),
                "author_model": "gemini-3.1-pro-preview",
                "instruction_cyrl": it["instruction"],
                "instruction_latn": to_latin(it["instruction"]),
                "conditions": {"cyrl": it["response"], "latn": to_latin(it["response"])},
            })
    json.dump(items, open(OUT, "w"), ensure_ascii=False, indent=1)
    print(f"wrote {OUT}: {len(items)} items", flush=True)


if __name__ == "__main__":
    main()
