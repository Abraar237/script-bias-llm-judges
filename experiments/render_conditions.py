"""Freeze the dataset and render each response in the four script conditions.
deva: original Devanagari
iast: scholarly romanization (deterministic, indic-transliteration)
ascii: iast with diacritics stripped (deterministic)
hinglish: filled in later by the naturalization pass + native-speaker audit
"""
import json, os, unicodedata
from indic_transliteration import sanscript

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(HERE, "data_gen")
OUT = os.path.join(HERE, "dataset_conditions.json")


def to_iast(t):
    return sanscript.transliterate(t, sanscript.DEVANAGARI, sanscript.IAST)


def strip_diacritics(t):
    norm = unicodedata.normalize("NFD", t)
    return unicodedata.normalize("NFC", "".join(c for c in norm if not unicodedata.combining(c))).replace("ṁ", "m")


def main():
    items = []
    for tier, fname in [("high", "tier_high.json"), ("medium", "tier_medium.json"), ("low", "tier_low.json")]:
        path = os.path.join(GEN, fname)
        for it in json.load(open(path)):
            iast = to_iast(it["response"])
            items.append({
                "id": it["id"], "tier": tier, "domain": it.get("domain", ""),
                "instruction_deva": it["instruction"],
                "instruction_iast": to_iast(it["instruction"]),
                "conditions": {
                    "deva": it["response"],
                    "iast": iast,
                    "ascii": strip_diacritics(iast),
                    "hinglish": None,
                },
            })
    json.dump(items, open(OUT, "w"), ensure_ascii=False, indent=1)
    print(f"{len(items)} items -> {OUT}")


if __name__ == "__main__":
    main()
