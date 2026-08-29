"""House figure style for the script-bias paper. Import in every build script."""
import matplotlib as mpl
import matplotlib.pyplot as plt

SLATE = "#155e8c"   # untouched condition / primary series (Devanagari, Gemini Flash)
HOT   = "#b3006b"   # intervention / attention series (mitigation, the finding)
SHELF = "#c0641a"   # second comparison series (ascii)
GOOD  = "#1c7a55"   # third comparison series (hinglish)
INK   = "#16130d"
INK2  = "#3a352b"
MUTED = "#6d665a"
FAINT = "#a49c8c"
RULE  = "#e7e2d5"
SURFACE = "#ffffff"

COND_COLORS = {"iast": SLATE, "ascii": SHELF, "hinglish": GOOD}
COND_LABELS = {"iast": "IAST", "ascii": "ASCII", "hinglish": "Hinglish"}


def apply():
    mpl.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE, "savefig.dpi": 300,
        "font.family": "Helvetica", "font.size": 9.5,
        "axes.edgecolor": RULE, "axes.linewidth": 0.8,
        "axes.labelcolor": MUTED, "axes.labelsize": 9.5,
        "xtick.color": MUTED, "ytick.color": MUTED,
        "xtick.labelsize": 9, "ytick.labelsize": 9,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": False,
        "lines.linewidth": 2.2, "lines.solid_capstyle": "round",
    })


def eyebrow(ax, text, y=1.06):
    ax.text(0, y, text.upper(), transform=ax.transAxes, ha="left",
            fontsize=9, color=MUTED, fontweight="medium", letterspacing_hack=None) \
        if False else ax.text(0, y, " ".join(text.upper()), transform=ax.transAxes,
                              ha="left", fontsize=8.6, color=MUTED)


def zero_rule(ax, axis="x"):
    if axis == "x":
        ax.axvline(0, ls=(0, (4, 3)), lw=0.9, color=FAINT, zorder=1)
    else:
        ax.axhline(0, ls=(0, (4, 3)), lw=0.9, color=FAINT, zorder=1)
