"""Figure 1 teaser, academic style (vector, serif, no hand-drawn elements).
Mirrors the presentation of arXiv:2401.06373 Fig.1/Fig.2: labeled condition cards
with real example text, flow into the judge, measured outcomes on the right."""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

SERIF = "Times New Roman"
DEVA = "Tiro Devanagari Hindi"
INK = "#16130d"; MUTED = "#6d665a"; RULE = "#b9b2a4"
SLATE = "#155e8c"; SHELF = "#c0641a"; GOOD = "#1c7a55"; HOT = "#b3006b"
SLATE_BG = "#e8eff5"; SHELF_BG = "#f7ece1"; GOOD_BG = "#e7f2ec"; HOT_BG = "#f7e4ee"
GREY_BG = "#f2f0ea"

fig, ax = plt.subplots(figsize=(9.6, 4.4))
ax.set_xlim(0, 100); ax.set_ylim(0, 46); ax.axis("off")


def card(x, y, w, h, bg, edge, title, title_color, lines, line_font=SERIF, fs=9.2):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6,rounding_size=1.2",
                         fc=bg, ec=edge, lw=1.0)
    ax.add_patch(box)
    ax.text(x + w / 2, y + h - 2.0, title, ha="center", va="top", fontsize=8.6,
            family=SERIF, style="italic", color=title_color, fontweight="bold")
    for i, (txt, f) in enumerate(lines):
        ax.text(x + w / 2, y + h - 5.6 - i * 3.4, txt, ha="center", va="top",
                fontsize=fs, family=f, color=INK)


def arrow(x1, y1, x2, y2, color=MUTED, lw=1.3):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=13, color=color, lw=lw,
                                 shrinkA=2, shrinkB=2))

# left: the fixed item
card(1, 15, 17, 16, GREY_BG, RULE, "fixed Hindi response", MUTED,
     [("प्रकाश संश्लेषण", DEVA),
      ("वह प्रक्रिया है ...", DEVA),
      ("(identical content,", SERIF), ("quality tier fixed)", SERIF)], fs=9.6)

# four condition cards
conds = [
    ("Devanagari (native)", SLATE_BG, SLATE,
     [("प्रकाश संश्लेषण वह ...", DEVA)]),
    ("IAST (scholarly)", SHELF_BG, SHELF, [("prakāśa saṃśleṣaṇa vaha ...", SERIF)]),
    ("ASCII (stripped)", GOOD_BG, GOOD, [("prakasa samslesana vaha ...", SERIF)]),
    ("Hinglish (user-style)", HOT_BG, HOT, [("prakash sanshleshan vah ...", SERIF)]),
]
ys = [36.5, 27.5, 18.5, 9.5]
for (title, bg, edge, lines), y in zip(conds, ys):
    card(24, y, 24, 8.2, bg, edge, title, edge, lines, fs=9.0)
    arrow(18.5, 23 + (y - 22) * 0.28 + 0.0, 23.4, y + 4.1)

# judge box
card(55, 16.5, 16, 13, "#ffffff", INK, "LLM judge", INK,
     [("0–100 rubric,", SERIF), ("one item per call,", SERIF),
      ("blind to pairing", SERIF)], fs=8.8)
for y in ys:
    arrow(48.8, y + 4.1, 54.4, 23 + (y - 22) * 0.18)

# outcomes
ax.text(81.5, 43.5, "measured shift vs. Devanagari", ha="center", fontsize=8.8,
        family=SERIF, style="italic", color=MUTED)
rows = [
    ("Gemini 3.6 Flash", "+2.2 to +3.4", HOT),
    ("Gemini 3.1 Pro", "+1.1", HOT),
    ("Qwen2.5-7B", "+6.0 to +7.6*", HOT),
    ("Claude Sonnet/Opus/Fable", "≈0", GOOD),
]
for i, (name, val, c) in enumerate(rows):
    y = 36.0 - i * 6.6
    box = FancyBboxPatch((72, y), 26.5, 5.4, boxstyle="round,pad=0.4,rounding_size=0.9",
                         fc="#ffffff", ec=RULE, lw=0.9)
    ax.add_patch(box)
    ax.text(73.2, y + 2.7, name, ha="left", va="center", fontsize=8.6, family=SERIF, color=INK)
    ax.text(97.4, y + 2.7, val, ha="right", va="center", fontsize=9.4,
            family=SERIF, fontweight="bold", color=c)
    arrow(71.6, y + 2.7, 72.0, y + 2.7, color=RULE, lw=0.9)
for i in range(4):
    arrow(69.2, 23, 71.6, 38.7 - i * 6.6 - 3.0 + 0.0, color=RULE, lw=0.9)

ax.text(84.5, 7.6, "*flat on Hinglish; inflation concentrated\nin formal romanizations of low-quality items",
        ha="center", fontsize=7.6, family=SERIF, color=MUTED)
ax.text(9.5, 11.5, "150 items\n3 quality tiers", ha="center", fontsize=8.0,
        family=SERIF, color=MUTED)

fig.tight_layout()
fig.savefig("fig1_schematic.png", dpi=300, bbox_inches="tight", facecolor="white")
print("academic fig1 written")
