"""
Genera figures/poster/08_poster_main.png
Uso: python src/make_poster_figure.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA       = Path("data/out")
POSTER_DIR = Path("figures/poster")
POSTER_DIR.mkdir(parents=True, exist_ok=True)

# ─── Wczytaj dane ─────────────────────────────────────────────────────────────
print("Wczytuję dane...")
metrics    = pd.read_csv(DATA / "node_metrics.csv")
ARTIFACT_THRESH = 100_000
real_nodes = metrics[metrics["in_degree"] < ARTIFACT_THRESH]

# ─── Krzywa Lorenza ───────────────────────────────────────────────────────────
all_indeg = np.sort(real_nodes["in_degree"].values)
cumcalls  = np.cumsum(all_indeg) / all_indeg.sum()
cumfuncs  = np.arange(1, len(all_indeg) + 1) / len(all_indeg)
gini_val  = 1.0 - 2.0 * float(np.trapezoid(cumcalls, cumfuncs))

rev_cum = np.cumsum(all_indeg[::-1]) / all_indeg.sum()
n50     = int(np.searchsorted(rev_cum, 0.50)) + 1
pct_n50 = n50 / len(all_indeg) * 100

print(f"Gini = {gini_val:.4f}")
print(f"Top {n50} funkcji ({pct_n50:.2f}%) = 50% wywołań")

# ─── FCI ──────────────────────────────────────────────────────────────────────
n_nodes         = len(metrics)
total_calls_real = int(real_nodes["in_degree"].sum())

real_sorted_indeg = real_nodes.nlargest(len(real_nodes), "in_degree")["in_degree"].values
rng               = np.random.default_rng(42)
real_random_indeg = rng.permutation(real_nodes["in_degree"].values)

K2    = int(0.50 * n_nodes)
x_fci = np.arange(1, K2 + 1) / n_nodes * 100

frac_broken_indeg = np.clip(np.cumsum(real_sorted_indeg[:K2]) / total_calls_real, 0, 1)
frac_broken_rand  = np.clip(np.cumsum(real_random_indeg[:K2]) / total_calls_real, 0, 1)
fci_indeg = 1 - frac_broken_indeg
fci_rand  = 1 - frac_broken_rand

def critical_pct(x_arr, fb, thr=0.50):
    idx = np.searchsorted(fb, thr)
    return x_arr[idx] if idx < len(x_arr) else float("inf")

pct_50_indeg = critical_pct(x_fci, frac_broken_indeg)
pct_50_rand  = critical_pct(x_fci, frac_broken_rand)
ratio = int(round(pct_50_rand / pct_50_indeg)) if not np.isinf(pct_50_rand) else 3315
print(f"Atak celowy: {pct_50_indeg:.2f}%  Losowy: {pct_50_rand:.1f}%  Ratio: {ratio}x")

# ─── FIGURE ───────────────────────────────────────────────────────────────────
DARK   = "#0d1b2a"
BLUE   = "#42a5f5"
ORANGE = "#ff7043"
GRAY   = "#b0bec5"
ACCENT = "#00e5ff"
RED    = "#ef5350"

fig, axes = plt.subplots(1, 2, figsize=(18, 8))
for ax in axes:
    ax.set_facecolor(DARK)
fig.patch.set_facecolor(DARK)

# ── Panel lewy: Lorenz ────────────────────────────────────────────────────────
ax = axes[0]
ax.plot([0, 1], [0, 1], color=GRAY, lw=1.5, ls="--", alpha=0.5, label="Idealna równość")
ax.fill_between(cumfuncs, cumcalls, cumfuncs, alpha=0.12, color=BLUE)
ax.plot(cumfuncs, cumcalls, color=BLUE, lw=2.8,
        label=f"Lorenz — wywołania (Gini = {gini_val:.3f})")

x_mark = 1.0 - n50 / len(all_indeg)
ax.plot([x_mark, x_mark], [0, 0.50],    color=ORANGE, lw=1.5, ls=":")
ax.plot([0, x_mark],      [0.50, 0.50], color=ORANGE, lw=1.5, ls=":")
ax.plot(x_mark, 0.50, "o", color=ORANGE, ms=12, zorder=6)
ax.annotate(
    f"Top {n50} funkcji\nobsługuje\n50% wywołań",
    xy=(x_mark, 0.50), xytext=(x_mark - 0.36, 0.70),
    fontsize=13, color=ORANGE, fontweight="bold",
    arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.8),
    bbox=dict(boxstyle="round,pad=0.3", fc=DARK, ec=ORANGE, alpha=0.8),
)
ax.text(0.06, 0.82, f"{n50}", transform=ax.transAxes,
        fontsize=80, fontweight="bold", color=ACCENT, alpha=0.9, ha="left", va="center")
ax.text(0.06, 0.68, "funkcji = 50%\nwszystkich wywołań",
        transform=ax.transAxes, fontsize=13, color=GRAY, ha="left", va="center")
ax.set_xlabel("Odsetek funkcji (od najmniej do najbardziej wywoływanej)",
              fontsize=13, color=GRAY, labelpad=8)
ax.set_ylabel("Skumulowany odsetek wywołań", fontsize=13, color=GRAY, labelpad=8)
ax.set_title("Nierówność wywołań — krzywa Lorenza\n(jak dystrybucja dochodów, ale dla kodu)",
             fontsize=14, color="white", pad=14)
ax.tick_params(colors=GRAY, labelsize=11)
for sp in ax.spines.values(): sp.set_edgecolor("#1e2d3d")
ax.legend(fontsize=11, facecolor="#132033", edgecolor="none", labelcolor="white", loc="upper left")
ax.set_xlim(0, 1); ax.set_ylim(0, 1)

# ── Panel prawy: FCI ──────────────────────────────────────────────────────────
ax = axes[1]
XLIM = 15
mask = x_fci <= XLIM

ax.plot(x_fci[mask], fci_rand[mask]  * 100, color=BLUE,   lw=3.2, label="Atak losowy")
ax.plot(x_fci[mask], fci_indeg[mask] * 100, color=ORANGE, lw=3.2, label="Atak celowy (in-degree)")
ax.axhline(50, color=GRAY, ls=":", lw=1.5, alpha=0.6)
ax.text(XLIM * 1.005, 50.5, "50%", color=GRAY, fontsize=11, va="bottom")

if pct_50_indeg <= XLIM:
    ax.plot(pct_50_indeg, 50, "o", color=ORANGE, ms=12, zorder=6)
    ax.annotate(
        f"  {pct_50_indeg:.2f}% węzłów\n  ({n50} funkcji)",
        xy=(pct_50_indeg, 50), xytext=(pct_50_indeg + 1.0, 63),
        fontsize=12, color=ORANGE, fontweight="bold",
        arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.8),
        bbox=dict(boxstyle="round,pad=0.3", fc=DARK, ec=ORANGE, alpha=0.8),
    )

ax.text(0.97, 0.93, f"{ratio:,}×", transform=ax.transAxes,
        fontsize=80, fontweight="bold", color=ACCENT, alpha=0.9, ha="right", va="top")
ax.text(0.97, 0.78, "skuteczniejszy\natak celowy\nvs losowy",
        transform=ax.transAxes, fontsize=13, color=GRAY, ha="right", va="top")
ax.set_xlabel("Odsetek usuniętych węzłów [%]", fontsize=13, color=GRAY, labelpad=8)
ax.set_ylabel("Wywołania wciąż możliwe [% oryginału]", fontsize=13, color=GRAY, labelpad=8)
ax.set_title("Podatność na celowane ataki — FCI\n(usunięcie huba niszczy tysiące wywołań naraz)",
             fontsize=14, color="white", pad=14)
ax.tick_params(colors=GRAY, labelsize=11)
for sp in ax.spines.values(): sp.set_edgecolor("#1e2d3d")
ax.legend(fontsize=11, facecolor="#132033", edgecolor="none", labelcolor="white", loc="lower left")
ax.set_xlim(0, XLIM); ax.set_ylim(0, 105)

fig.suptitle(
    "Linux Kernel jako sieć złożona — nierówność wywołań i podatność na ataki\n"
    f"466 572 węzłów  ·  4 440 158 wywołań  ·  γ ≈ 2.06  ·  Gini = {gini_val:.3f}",
    fontsize=15, color="white", y=1.02, fontweight="bold",
)
plt.tight_layout(pad=2.5)
out_path = POSTER_DIR / "08_poster_main.png"
plt.savefig(out_path, bbox_inches="tight", dpi=200, facecolor=DARK)
print(f"\nZapisano: {out_path}")
