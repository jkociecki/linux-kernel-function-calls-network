"""
make_all_figures.py
Regeneruje wszystkie figury posterowe w spójnym DARK stylu.

Użycie:
    python src/make_all_figures.py

Output: figures/poster/styled/fig_*.png
  – ciemne tło (#0d1b2a) z przezroczystością
  – font: Open Sans
  – neonowe kolory na ciemnym tle
  – 200 dpi
"""

import argparse
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import matplotlib.ticker as mticker
import matplotlib.colors as mcolors
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath
import numpy as np
import pandas as pd
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--light", action="store_true", help="Generuj w trybie jasnym")
LIGHT = ap.parse_args().light

# ─── Odśwież cache fontów (żeby Open Sans działał) ────────────────────────────
import matplotlib.font_manager as fm
fm._load_fontmanager(try_read_cache=False)

DATA = Path("data/out")

if LIGHT:
    OUT = Path("figures/poster/light")
else:
    OUT = Path("figures/poster/styled")
OUT.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════════
# DESIGN SYSTEM — Dark / Light
# ═══════════════════════════════════════════════════════════════════════════════
if LIGHT:
    BG      = "#FFFFFF"      # tło figury
    PANEL   = "#F1F5F9"      # tło osi
    GRIDCOL = "#CBD5E1"      # linie siatki
    SPINE   = "#94A3B8"      # obramowanie osi
    C = dict(
        blue   = "#1D4ED8",
        red    = "#DC2626",
        orange = "#EA580C",
        green  = "#16A34A",
        teal   = "#0D9488",
        purple = "#7C3AED",
        yellow = "#D97706",
        ink    = "#0F172A",   # primary text (ciemny na jasnym)
        mid    = "#475569",   # secondary text
        muted  = "#94A3B8",   # muted
        border = "#94A3B8",
        fill   = "#F1F5F9",
    )
else:
    BG      = "#0d1b2a"      # tło figury
    PANEL   = "#132033"      # tło osi
    GRIDCOL = "#1e3250"      # linie siatki
    SPINE   = "#2a4a6b"      # obramowanie osi
    C = dict(
        blue   = "#4C9BE8",
        red    = "#FF4D4D",
        orange = "#FF8C42",
        green  = "#2ECC71",
        teal   = "#1ABCBA",
        purple = "#A855F7",
        yellow = "#F59E0B",
        ink    = "#F0F4F8",   # primary text (jasny na ciemnym)
        mid    = "#94A3B8",   # secondary text
        muted  = "#4A6080",   # muted
        border = SPINE,
        fill   = PANEL,
    )
PALETTE = [C["blue"], C["red"], C["orange"], C["green"], C["teal"], C["purple"], C["yellow"]]
DPI = 200
FONT = "Open Sans"

plt.rcParams.update({
    "font.family":        "sans-serif",
    "font.sans-serif":    [FONT, "DejaVu Sans"],
    "font.size":          12,
    "axes.titlesize":     15,
    "axes.titleweight":   "bold",
    "axes.titlepad":      14,
    "axes.titlecolor":    C["ink"],
    "axes.labelsize":     12,
    "axes.labelpad":      8,
    "axes.labelcolor":    C["mid"],
    "axes.facecolor":     PANEL,
    "axes.edgecolor":     SPINE,
    "figure.facecolor":   BG,
    "text.color":         C["ink"],
    "xtick.color":        C["mid"],
    "ytick.color":        C["mid"],
    "xtick.labelsize":    11,
    "ytick.labelsize":    11,
    "legend.fontsize":    10,
    "legend.framealpha":  0.85,
    "legend.facecolor":   PANEL,
    "legend.edgecolor":   SPINE,
    "legend.labelcolor":  C["ink"],
    "figure.dpi":         DPI,
})


def style_ax(ax, grid="both", spines="lb"):
    ax.set_facecolor(PANEL)
    for side in ["top", "right", "left", "bottom"]:
        ax.spines[side].set_visible(True)
        ax.spines[side].set_color(SPINE)
        ax.spines[side].set_linewidth(0.8)
    if grid == "both":
        ax.grid(True, color=GRIDCOL, lw=0.7, zorder=0)
    elif grid == "y":
        ax.yaxis.grid(True, color=GRIDCOL, lw=0.7, zorder=0)
        ax.xaxis.grid(False)
    elif grid == "x":
        ax.xaxis.grid(True, color=GRIDCOL, lw=0.7, zorder=0)
        ax.yaxis.grid(False)
    elif grid == "none":
        ax.grid(False)
    ax.set_axisbelow(True)


def save(fig, name):
    plt.tight_layout(pad=2.0)
    path = OUT / name
    fig.patch.set_alpha(0.0)
    plt.savefig(path, bbox_inches="tight", transparent=True, dpi=DPI)
    plt.close(fig)
    print(f"   ✓ {path}")


# ─── Wczytaj dane ─────────────────────────────────────────────────────────────
print("Wczytuję dane...")
metrics    = pd.read_csv(DATA / "node_metrics.csv")
subsys_df  = pd.read_csv(DATA / "subsystem_stats.csv")
edges_df   = pd.read_csv(DATA / "edges.csv")

# Filter instrumentation functions (ASAN, sanitizers, etc.)
instr_mask = metrics["func_name"].str.contains(r"(sanitizer|asan|ubsan|__stack_chk)", regex=True, na=False)
real       = metrics[~instr_mask].copy()
n_nodes    = len(metrics)
n_edges    = len(edges_df)
n_filtered = instr_mask.sum()
print(f"  {n_nodes:,} węzłów  ·  {n_edges:,} krawędzi")
print(f"  (odfiltrowano {n_filtered} instrumentation functions)\n")


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  FIG A — Rozkład potęgowy (CCDF)                                          ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
print("[1/5] Power-law CCDF...")

def ccdf(arr):
    s = np.sort(arr[arr > 0])
    return s, np.arange(len(s), 0, -1) / len(s)

def pl_fit_mle(x, k_min=2):
    """MLE estymator gamma (Clauset et al.)"""
    v = x[x >= k_min]
    if len(v) < 2:
        return np.nan, np.nan
    n = len(v)
    gamma = 1 + n / np.sum(np.log(v / (k_min - 0.5)))
    return gamma, 0  # brak offsetu dla MLE

# Legacy function kept for compatibility
def pl_fit(x, y, xmin_log=0.5):
    lx, ly = np.log10(x), np.log10(y)
    cutoff = np.percentile(x, 99.9)
    mask = (lx >= xmin_log) & (x <= cutoff)
    m = np.polyfit(lx[mask], ly[mask], 1)
    return -m[0], m[1]

fig, ax = plt.subplots(figsize=(8, 5.5))

series = [
    (real["in_degree"],         C["blue"],   "o",  "in-degree"),
    (real["out_degree"],        C["orange"], "s",  "out-degree"),
    (real["in_degree"] + real["out_degree"], C["teal"], "^", "total degree"),
]

for arr, color, marker, label in series:
    vals = arr.values
    vals_pos = vals[vals > 0]
    x, y = ccdf(vals_pos)
    ax.scatter(x, y, s=8, color=color, alpha=0.35, marker=marker, zorder=3, rasterized=True)
    
    # Use MLE estimator (like in notebook)
    gamma, _ = pl_fit_mle(vals_pos, k_min=2)
    
    # Plot power-law fit line: P(X >= x) = C_norm * x^(-gamma)
    k_min_idx = np.searchsorted(x, 2)
    C_norm = y[k_min_idx] if k_min_idx < len(y) else 1.0
    xf = np.logspace(np.log10(max(2, x[0])), np.log10(x[-1]), 300)
    yf = C_norm * (xf / 2) ** (-(gamma - 1))
    
    line, = ax.plot(xf, yf, color=color, lw=2.5, ls="--",
                    label=f"{label}  (γ = {gamma:.2f})", zorder=4)
    # glow effect
    line.set_path_effects([
        pe.withStroke(linewidth=6, foreground=color, alpha=0.25),
        pe.Normal()
    ])

ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlabel("Stopień węzła  k")
ax.set_ylabel("P(K ≥ k)  [CCDF]")
ax.set_title("Sieć wywołań jądra Linux jest skalą wolną")

# Stats box
ax.text(0.97, 0.97,
        f"N = {n_nodes:,} funkcji\nE = {n_edges:,} wywołań\n"
        f"<k> = {(real['in_degree'].mean() + real['out_degree'].mean()):.1f}",
        transform=ax.transAxes, ha="right", va="top", fontsize=10,
        color=C["mid"], linespacing=1.6,
        bbox=dict(boxstyle="round,pad=0.5", fc=PANEL, ec=SPINE, alpha=0.95))

handles, labels_lg = ax.get_legend_handles_labels()
ax.legend(handles, labels_lg, ncol=1, loc="lower left")
style_ax(ax, grid="both")
save(fig, "fig_A_powerlaw.png")


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  FIG B — Bow-tie infographic                                               ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
print("[2/5] Bow-tie infographic...")

# Znane wartości (z notebook 07)
bowtie = {
    "IN\n(czyste odbiorniki)":   (0.904, C["blue"]),
    "SCC\n(silnie spójny rdzeń)": (0.021, C["purple"]),
    "OUT\n(czyste źródła)":       (0.005, C["orange"]),
    "Tendrils /\nodłączone":       (0.070, C["muted"]),
}

fig, (ax_bar, ax_dia) = plt.subplots(1, 2, figsize=(14, 5),
                                      gridspec_kw={"width_ratios": [1, 1.4]})

# ── lewy panel: horizontal stacked bar ──────────────────────────────────────
labels_b  = list(bowtie.keys())
vals_b    = [v[0] for v in bowtie.values()]
colors_b  = [v[1] for v in bowtie.values()]

y_pos = [0]
left  = 0
for label, val, color in zip(labels_b, vals_b, colors_b):
    bar = ax_bar.barh(0, val, left=left, height=0.55, color=color,
                      edgecolor="white", linewidth=1.5, zorder=3)
    cx = left + val / 2
    if val >= 0.03:
        ax_bar.text(cx, 0, f"{val*100:.1f}%",
                    ha="center", va="center", fontsize=12,
                    fontweight="bold", color="white",
                    path_effects=[pe.withStroke(linewidth=2, foreground=color)])
    left += val

ax_bar.set_xlim(0, 1)
ax_bar.set_ylim(-0.6, 0.6)
ax_bar.set_yticks([])
ax_bar.set_xlabel("Odsetek wszystkich funkcji")
ax_bar.set_title("Dekompozycja bow-tie")

# legenda
patches = [mpatches.Patch(color=c, label=l.replace("\n", " "))
           for l, (_, c) in bowtie.items()]
ax_bar.legend(handles=patches, loc="upper center", bbox_to_anchor=(0.5, -0.22),
              ncol=2, fontsize=10)
style_ax(ax_bar, grid="none", spines="b")
ax_bar.spines["bottom"].set_color(SPINE)
ax_bar.tick_params(axis="x", colors=C["mid"])
ax_bar.xaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))

# ── prawy panel: bow-tie — bloki proporcjonalne + trapezoidalne łączniki ─────
ax_dia.set_xlim(0, 10)
ax_dia.set_ylim(0, 6)
ax_dia.axis("off")
ax_dia.set_title("Architektura przepływu wywołań", pad=14)

cy = 3.30   # oś pozioma (nieco powyżej środka → zostawia miejsce na tendrils)

# Wysokości bloków — proporcjonalne (IN dominuje, SCC widoczny, OUT malutki)
in_h  = 5.00   # 90,4%
scc_h = 1.60   # 2,1%
out_h = 0.65   # 0,5%

# Pozycje X bloków i luk
in_x0,  in_x1  = 0.20, 2.10   # IN — szeroki
scc_x0, scc_x1 = 3.30, 5.10   # SCC
out_x0, out_x1 = 6.20, 7.35   # OUT — wąski

# ─── Pomocnicze: rysuje trapezoidalny łącznik (styl Sankey) ──────────────────
def _connector(ax, x0, x1, cy, h_l, h_r, color, alpha=0.28):
    verts = [
        (x0, cy - h_l/2), (x1, cy - h_r/2),
        (x1, cy + h_r/2), (x0, cy + h_l/2),
        (x0, cy - h_l/2),
    ]
    codes = [MPath.MOVETO, MPath.LINETO, MPath.LINETO, MPath.LINETO, MPath.CLOSEPOLY]
    ax.add_patch(PathPatch(MPath(verts, codes), fc=color, ec="none", alpha=alpha, zorder=2))

# ─── IN → łącznik → SCC ──────────────────────────────────────────────────────
_connector(ax_dia, in_x1, scc_x0, cy, in_h, scc_h, C["blue"])

# ─── SCC → łącznik → OUT ─────────────────────────────────────────────────────
_connector(ax_dia, scc_x1, out_x0, cy, scc_h, out_h, C["orange"])

# ─── blok IN ─────────────────────────────────────────────────────────────────
ax_dia.add_patch(mpatches.FancyBboxPatch(
    (in_x0, cy - in_h/2), in_x1 - in_x0, in_h,
    boxstyle="round,pad=0.12", fc=C["blue"], ec="none", alpha=0.90, zorder=3))
_bx = (in_x0 + in_x1) / 2
ax_dia.text(_bx, cy + 0.65, "IN",
    ha="center", va="center", fontsize=34, fontweight="bold", color="white", zorder=4)
ax_dia.text(_bx, cy - 0.07, "90,4%",
    ha="center", va="center", fontsize=17, fontweight="bold", color="white", zorder=4)
ax_dia.text(_bx, cy - 0.82, "czyste\nodbiorniki",
    ha="center", va="center", fontsize=9.5, color="white", alpha=0.78, zorder=4)

# ─── blok SCC ────────────────────────────────────────────────────────────────
ax_dia.add_patch(mpatches.FancyBboxPatch(
    (scc_x0, cy - scc_h/2), scc_x1 - scc_x0, scc_h,
    boxstyle="round,pad=0.10", fc=C["purple"], ec="none", alpha=0.95, zorder=3))
_sx = (scc_x0 + scc_x1) / 2
ax_dia.text(_sx, cy + 0.22, "SCC",
    ha="center", va="center", fontsize=14, fontweight="bold", color="white", zorder=4)
ax_dia.text(_sx, cy - 0.25, "2,1%",
    ha="center", va="center", fontsize=11.5, color="white", alpha=0.92, zorder=4)
ax_dia.text(_sx, cy - scc_h/2 - 0.18,
    "rdzeń cykliczny",
    ha="center", va="top", fontsize=8.5, color=C["mid"], style="italic")

# ─── blok OUT ────────────────────────────────────────────────────────────────
ax_dia.add_patch(mpatches.FancyBboxPatch(
    (out_x0, cy - out_h/2), out_x1 - out_x0, out_h,
    boxstyle="round,pad=0.09", fc=C["orange"], ec="none", alpha=0.92, zorder=3))
_ox = (out_x0 + out_x1) / 2
ax_dia.text(_ox, cy + 0.02, "OUT",
    ha="center", va="center", fontsize=10.5, fontweight="bold", color="white", zorder=4)
ax_dia.text(_ox, cy - 0.27, "0,5%",
    ha="center", va="center", fontsize=9.5, color="white", alpha=0.90, zorder=4)
ax_dia.text(_ox, cy - out_h/2 - 0.18,
    "czyste źródła",
    ha="center", va="top", fontsize=8.5, color=C["mid"], style="italic")

# ─── Tendrils: ramka + przerywana linia do SCC ───────────────────────────────
tend_w, tend_h, tend_y0 = 4.30, 0.62, 0.18
tend_cx = _sx  # wyśrodkowana pod SCC
tend_x0 = tend_cx - tend_w / 2
# linia przerywana
ax_dia.plot([tend_cx, tend_cx], [cy - scc_h/2, tend_y0 + tend_h],
    color=C["muted"], lw=1.5, ls="--", zorder=2)
ax_dia.add_patch(mpatches.FancyBboxPatch(
    (tend_x0, tend_y0), tend_w, tend_h,
    boxstyle="round,pad=0.15", fc=C["muted"], ec=SPINE, alpha=0.48, lw=1.2, zorder=2))
ax_dia.text(tend_cx, tend_y0 + tend_h / 2,
    "Tendrils / odłączone   7,1%",
    ha="center", va="center", fontsize=10.5, color="white", alpha=0.92)

style_ax(ax_dia, grid="none", spines="")
save(fig, "fig_B_bowtie.png")


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  FIG C — Dispatcher / Bridge / Executor per subsystem                     ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
print("[3/5] Dispatchers / Bridges / Executors...")

m = metrics.copy()
m["role"] = "bridge"
m.loc[(m["out_degree"] > 0) & (m["in_degree"] == 0), "role"] = "dispatcher"
m.loc[(m["in_degree"] > 0) & (m["out_degree"] == 0), "role"] = "executor"
m.loc[(m["in_degree"] == 0) & (m["out_degree"] == 0), "role"] = "isolated"

role_counts = m["role"].value_counts()
total = len(m)

# Per subsystem — top 12
top_sys = (m.groupby("subsystem").size()
            .nlargest(12).index.tolist())
sub_roles = (m[m["subsystem"].isin(top_sys)]
              .groupby(["subsystem", "role"]).size()
              .unstack(fill_value=0))
for col in ["dispatcher", "bridge", "executor", "isolated"]:
    if col not in sub_roles.columns:
        sub_roles[col] = 0

# Sort by dispatchers desc
sub_roles = sub_roles.sort_values("dispatcher", ascending=True)

# znormalizuj do 100% per subsystem
role_order  = ["dispatcher", "bridge", "executor", "isolated"]
role_colors = [C["blue"], C["teal"], C["orange"], C["muted"]]
role_labels_short = ["Dispatcher", "Bridge", "Executor", "Isolated"]

sub_totals = sub_roles[role_order].sum(axis=1)
sub_pct = sub_roles[role_order].div(sub_totals, axis=0) * 100
# sortuj malejąco po dispatcher% (kernel na górze)
sub_pct = sub_pct.sort_values("dispatcher", ascending=True)
sub_totals = sub_totals.loc[sub_pct.index]

fig, ax = plt.subplots(figsize=(15, 6.5))

systems = sub_pct.index.tolist()
y = np.arange(len(systems))
h = 0.52
lefts = np.zeros(len(systems))

for role, color, label in zip(role_order, role_colors, role_labels_short):
    vals = sub_pct[role].values
    bars = ax.barh(y, vals, height=h, left=lefts,
                   color=color, label=label, zorder=3, edgecolor=BG, lw=0.6)
    # wstaw % wewnątrz paska jeśli > 6%
    for i, (v, l) in enumerate(zip(vals, lefts)):
        if v > 6:
            ax.text(l + v / 2, y[i], f"{v:.0f}%",
                    ha="center", va="center", fontsize=8,
                    color="white", fontweight="bold", zorder=4)
    lefts = lefts + vals

# etykiety osi y (subsystem) + liczba funkcji po prawej
ax.set_yticks(y)
ax.set_yticklabels([s.replace("drivers/", "drv/") for s in systems], fontsize=10.5)
for i, (sys, tot) in enumerate(zip(systems, sub_totals)):
    ax.text(101.5, y[i], f"{tot:,}", va="center", ha="left",
            fontsize=8.5, color=C["mid"])
ax.text(101.5, len(systems) - 0.05, "n", va="bottom", ha="left",
        fontsize=8, color=C["muted"])

ax.set_xlim(0, 100)
ax.set_xlabel("Udział funkcji w subsystemie [%]", labelpad=6)
ax.set_title("Role funkcji per subsystem (top 12 wg liczebności)", pad=42)
ax.legend(loc="lower right", framealpha=0.15, fontsize=9.5,
          labelcolor=C["ink"])

# globalne proporcje jako anotacja pod tytułem (nad wykresem)
global_summary = "  ·  ".join(
    f"{role_labels_short[i]} {role_counts.get(r,0)/total*100:.1f}%"
    for i, r in enumerate(role_order)
)
ax.text(0.5, 1.075, f"Globalnie: {global_summary}",
        transform=ax.transAxes, ha="center", va="bottom",
        fontsize=9, color=C["muted"])

style_ax(ax, grid="x", spines="lb")
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0f}%"))

save(fig, "fig_C_dispatchers.png")


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  FIG D — Krzywa Lorenza + FCI (oryginalny wynik)                          ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
print("[4/5] Lorenz + FCI...")

all_indeg = np.sort(real["in_degree"].values)
cumcalls  = np.cumsum(all_indeg) / all_indeg.sum()
cumfuncs  = np.arange(1, len(all_indeg) + 1) / len(all_indeg)
gini_val  = 1.0 - 2.0 * float(np.trapezoid(cumcalls, cumfuncs))

rev_cum = np.cumsum(all_indeg[::-1]) / all_indeg.sum()
n50     = int(np.searchsorted(rev_cum, 0.50)) + 1

real_sorted   = real.nlargest(len(real), "in_degree")["in_degree"].values
rng           = np.random.default_rng(42)
real_random   = rng.permutation(real["in_degree"].values)
total_calls_r = int(real["in_degree"].sum())

K2    = min(int(0.50 * n_nodes), len(real_sorted))
x_fci = np.arange(1, K2 + 1) / n_nodes * 100

frac_indeg = np.clip(np.cumsum(real_sorted[:K2])   / total_calls_r, 0, 1)
frac_rand  = np.clip(np.cumsum(real_random[:K2])   / total_calls_r, 0, 1)
fci_indeg  = 1 - frac_indeg
fci_rand   = 1 - frac_rand

def crit(x, fb):
    i = np.searchsorted(fb, 0.50)
    return x[i] if i < len(x) else float("inf")

p50_ind  = crit(x_fci, frac_indeg)
p50_rand = crit(x_fci, frac_rand)
ratio    = int(round(p50_rand / p50_ind)) if not np.isinf(p50_rand) else 3315

fig, axes3 = plt.subplots(1, 2, figsize=(16, 6))

# ── Lorenz ──────────────────────────────────────────────────────────────────
ax = axes3[0]
ax.plot([0, 1], [0, 1], color=C["muted"], lw=1.5, ls="--",
        label="Idealna równość", zorder=2)
ax.fill_between(cumfuncs, cumcalls, cumfuncs,
                alpha=0.15, color=C["blue"], zorder=1)
line_l, = ax.plot(cumfuncs, cumcalls, color=C["blue"], lw=2.8,
                  label=f"Lorenz  (Gini = {gini_val:.3f})", zorder=3)
line_l.set_path_effects([
    pe.withStroke(linewidth=7, foreground=C["blue"], alpha=0.2),
    pe.Normal()
])

x_mark = 1.0 - n50 / len(all_indeg)
ax.plot([x_mark, x_mark], [0, 0.50],    color=C["red"], lw=1.5, ls=":", zorder=4)
ax.plot([0, x_mark],      [0.50, 0.50], color=C["red"], lw=1.5, ls=":", zorder=4)
ax.plot(x_mark, 0.50, "o", color=C["red"], ms=9, zorder=5,
        path_effects=[pe.withStroke(linewidth=5, foreground=C["red"], alpha=0.3)])

ax.annotate(
    f"Top {n50} funkcji\n= 50% wywołań",
    xy=(x_mark, 0.50), xytext=(x_mark - 0.35, 0.68),
    fontsize=11, color=C["red"], fontweight="semibold",
    arrowprops=dict(arrowstyle="-|>", color=C["red"], lw=1.5),
    bbox=dict(boxstyle="round,pad=0.35", fc=PANEL, ec=C["red"], alpha=0.9),
)

# Hero number — w prawym dolnym rogu żeby nie nachodził
ax.text(0.98, 0.12, str(n50), transform=ax.transAxes,
        fontsize=72, fontweight="bold", color=C["blue"], alpha=0.85,
        ha="right", va="bottom",
        path_effects=[pe.withStroke(linewidth=3, foreground=BG, alpha=0.5)])
ax.text(0.98, 0.04, "funkcji = 50% wywołan",
        transform=ax.transAxes, fontsize=10, color=C["mid"],
        ha="right", va="bottom")

ax.set_xlabel("Odsetek funkcji (od najmniej do najbardziej wywoływanej)")
ax.set_ylabel("Skumulowany odsetek wywołań")
ax.set_title("Nierówność wywołań — krzywa Lorenza")
ax.set_xlim(0, 1); ax.set_ylim(0, 1)
ax.legend(loc="upper left")
style_ax(ax)

# ── FCI ─────────────────────────────────────────────────────────────────────
ax = axes3[1]
XLIM = 15
mask = x_fci <= XLIM

# Fill under curves
ax.fill_between(x_fci[mask], fci_rand[mask]  * 100, alpha=0.12, color=C["blue"])
ax.fill_between(x_fci[mask], fci_indeg[mask] * 100, alpha=0.12, color=C["red"])

line_r, = ax.plot(x_fci[mask], fci_rand[mask]  * 100,
                  color=C["blue"],   lw=3.0, label="Atak losowy")
line_i, = ax.plot(x_fci[mask], fci_indeg[mask] * 100,
                  color=C["red"],    lw=3.0, label="Atak celowy (in-degree)")
for line, col in [(line_r, C["blue"]), (line_i, C["red"])]:
    line.set_path_effects([
        pe.withStroke(linewidth=8, foreground=col, alpha=0.2),
        pe.Normal()
    ])

ax.axhline(50, color=C["muted"], ls=":", lw=1.5)
ax.text(XLIM * 0.99, 52, "50% wywołan", va="bottom", ha="right", fontsize=10, color=C["muted"])

if p50_ind <= XLIM:
    ax.plot(p50_ind, 50, "o", color=C["red"], ms=10, zorder=5,
            path_effects=[pe.withStroke(linewidth=5, foreground=C["red"], alpha=0.3)])
    ax.annotate(
        f"  {p50_ind:.2f}% usuniętych\n  = {n50} funkcji",
        xy=(p50_ind, 50), xytext=(p50_ind + 1.2, 64),
        fontsize=11, color=C["red"], fontweight="semibold",
        arrowprops=dict(arrowstyle="-|>", color=C["red"], lw=1.5),
        bbox=dict(boxstyle="round,pad=0.35", fc=PANEL, ec=C["red"], alpha=0.9),
    )

# Hero number
ax.text(0.97, 0.97, f"{ratio:,}×", transform=ax.transAxes,
        fontsize=64, fontweight="bold", color=C["red"], alpha=0.92,
        ha="right", va="top",
        path_effects=[pe.withStroke(linewidth=3, foreground=BG, alpha=0.4)])
ax.text(0.97, 0.79, "skuteczniejszy\natak celowy\nvs losowy",
        transform=ax.transAxes, fontsize=11, color=C["mid"],
        ha="right", va="top", linespacing=1.5)

ax.set_xlabel("Odsetek usuniętych węzłów [%]")
ax.set_ylabel("Wywołania wciąż możliwe [% oryginału]")
ax.set_title("Podatność na ataki — FCI")
ax.set_xlim(0, XLIM); ax.set_ylim(0, 105)
ax.legend(loc="lower left")
style_ax(ax)

save(fig, "fig_D_lorenz_fci.png")


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  FIG E — Coupling matrix (znormalizowana)                                  ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
print("[5/5] Coupling matrix...")

node_sub = metrics[["id", "subsystem"]].set_index("id")
e = edges_df.join(node_sub.rename(columns={"subsystem": "src"}), on="source")
e = e.join(node_sub.rename(columns={"subsystem": "tgt"}), on="target")
e = e.dropna(subset=["src", "tgt"])
e = e[e["src"] != e["tgt"]]

cross = (e.groupby(["src", "tgt"]).size()
          .unstack(fill_value=0))

# Top 15 subsystems by total flow
top15 = (cross.sum(axis=1) + cross.sum(axis=0)).nlargest(15).index
cross = cross.reindex(index=top15, columns=top15, fill_value=0)

# Normalize per row (source)
row_sums = cross.sum(axis=1).replace(0, 1)
norm = cross.div(row_sums, axis=0)

# Custom colormap: panel → blue/purple
if LIGHT:
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "poster_light", [PANEL, "#BFDBFE", "#3B82F6", "#7C3AED", "#C026D3"], N=256
    )
else:
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "poster_dark", [PANEL, "#1e3a6e", "#2563EB", "#7C3AED", "#C026D3"], N=256
    )

fig, ax = plt.subplots(figsize=(10, 8.5))
im = ax.imshow(norm.values, cmap=cmap, aspect="auto", vmin=0, vmax=0.5)

labels15 = [l.replace("drivers/", "drv/") for l in top15]
ax.set_xticks(range(len(top15))); ax.set_xticklabels(labels15, rotation=45, ha="right", fontsize=9)
ax.set_yticks(range(len(top15))); ax.set_yticklabels(labels15, fontsize=9)
ax.set_xlabel("Subsystem CELU (callee)")
ax.set_ylabel("Subsystem ŹRÓDŁA (caller)")
ax.set_title("Macierz zależności subsystemów (znormalizowana)\n"
             "Wiersz = skąd idą wywołania danego subsystemu")

cbar = plt.colorbar(im, ax=ax, fraction=0.038, pad=0.02)
cbar.set_label("Frakcja wywołań wychodzących", fontsize=10, color=C["mid"])
cbar.ax.tick_params(labelsize=9, colors=C["mid"])
cbar.outline.set_edgecolor(SPINE)

# Zaznacz przekątną
for i in range(len(top15)):
    ax.add_patch(plt.Rectangle((i - 0.5, i - 0.5), 1, 1,
                                fill=False, ec=C["mid"], lw=1.2, ls="--"))

# Adnotacja: kernel dominuje
ker_idx = list(top15).index("kernel") if "kernel" in list(top15) else None
if ker_idx is not None:
    ax.annotate("kernel\nbetweenness\n= 0.993",
                xy=(ker_idx, 2), xytext=(ker_idx + 2.5, 5),
                fontsize=9, color=C["purple"], fontweight="semibold",
                arrowprops=dict(arrowstyle="-|>", color=C["purple"], lw=1.2),
                annotation_clip=False)

for sp in ax.spines.values():
    sp.set_edgecolor(SPINE); sp.set_linewidth(0.8)
ax.tick_params(colors=C["mid"])

save(fig, "fig_E_coupling.png")


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  FIG F — Paradoks PageRank: popularność ≠ wpływ                           ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
print("[6/6] PageRank paradox...")

# Odfiltruj sanitizery i artefakty — chcemy prawdziwe funkcje
FILT = real[
    (real["in_degree"] >= 1) &
    (real["pagerank"] > 0) &
    (~real["func_name"].str.startswith("__sanitizer")) &
    (~real["func_name"].str.startswith("__ubsan")) &
    (~real["func_name"].str.startswith("__kcov")) &
    (real["subsystem"] != "external")
].copy()

# Top subsystems do kolorowania
top_subs = FILT.groupby("subsystem").size().nlargest(8).index.tolist()
FILT["sub_color"] = FILT["subsystem"].apply(lambda s: s if s in top_subs else "inne")

sub_palette = {
    s: PALETTE[i % len(PALETTE)] for i, s in enumerate(top_subs)
}
sub_palette["inne"] = C["muted"]

# Losowa próbka żeby nie malować 466k punktów
sample = FILT.sample(n=min(15_000, len(FILT)), random_state=42)

fig, axes_f = plt.subplots(1, 2, figsize=(16, 6))

# ── Lewy panel: scatter in_degree vs PageRank ────────────────────────────────
ax = axes_f[0]

for sub, grp in sample.groupby("sub_color"):
    ax.scatter(grp["in_degree"], grp["pagerank"],
               s=10, alpha=0.35, color=sub_palette[sub],
               label=sub.replace("drivers/", "drv/"), zorder=3, rasterized=True)

ax.set_xscale("log"); ax.set_yscale("log")

# Zaznacz paradoksalne przykłady — stałe pozycje etykiet żeby nie nachodziły
# xytext w przestrzeni danych (log skala): (in_degree, pagerank)
highlights = [
    # (func_name, color, xytext_indeg, xytext_pr, ha, va)
    ("kasan_report",  C["green"],   5,      1.5e-2,  "left",  "center"),
    ("memset",        C["orange"],  5000,   3e-3,    "left",  "center"),
    ("_printk",       C["teal"],    8000,   5e-3,    "left",  "center"),
    ("panic",         C["purple"],  80,     2e-3,    "left",  "center"),
]
for fname, col, tx, ty, ha_, va_ in highlights:
    row = FILT[FILT["func_name"] == fname]
    if len(row) == 0:
        continue
    r = row.iloc[0]
    ax.scatter(r["in_degree"], r["pagerank"],
               s=120, color=col, zorder=6, edgecolors="white", linewidths=1.2,
               path_effects=[pe.withStroke(linewidth=4, foreground=col, alpha=0.3)])
    ax.annotate(fname,
                xy=(r["in_degree"], r["pagerank"]),
                xytext=(tx, ty),
                ha=ha_, va=va_,
                fontsize=9, color=col, fontweight="semibold",
                arrowprops=dict(arrowstyle="-", color=col, lw=1.0,
                                connectionstyle="arc3,rad=0.2"),
                bbox=dict(boxstyle="round,pad=0.25", fc=PANEL, ec=col, alpha=0.88))

# Zaznacz strefę paradoksu — wysoki PR, niski in_degree
ax.axvline(100, color=C["muted"], lw=1.0, ls=":", alpha=0.6)
ax.axhline(1e-4, color=C["muted"], lw=1.0, ls=":", alpha=0.6)

ax.set_xlabel("In-degree  (liczba bezpośrednich wywołań)")
ax.set_ylabel("PageRank  (wpływ w całej sieci)")
ax.set_title("Paradoks PageRank:\npopularność ≠ wpływ")
ax.legend(ncol=2, fontsize=8, markerscale=1.5,
          loc="lower right", bbox_to_anchor=(1.0, 0.0))
style_ax(ax, grid="both")

# ── Prawy panel: diverging bar — importerzy vs eksporterzy subsystemów ────────
ax = axes_f[1]

s_df = pd.read_csv(DATA / "subsystem_stats.csv")
s_df["balance"] = s_df["incoming_cross_edges"] - s_df["outgoing_cross_edges"]
top_bal = pd.concat([
    s_df.nlargest(8, "balance"),
    s_df.nsmallest(8, "balance")
]).drop_duplicates("subsystem").sort_values("balance")

names  = [n.replace("drivers/", "drv/") for n in top_bal["subsystem"]]
vals   = top_bal["balance"].values
colors_div = [C["blue"] if v > 0 else C["red"] for v in vals]
y_pos  = np.arange(len(vals))

bars = ax.barh(y_pos, vals / 1_000, color=colors_div, height=0.65,
               edgecolor=PANEL, linewidth=0.5, zorder=3)
# glow on positive bars
for bar, col in zip(bars, colors_div):
    bar.set_path_effects([
        pe.withStroke(linewidth=4, foreground=col, alpha=0.15),
        pe.Normal()
    ])

ax.axvline(0, color=C["ink"], lw=1.2, zorder=4)
ax.set_yticks(y_pos)
ax.set_yticklabels(names, fontsize=9)
ax.set_title("Kto jest fundamentem, kto buduje?\n(bilans = wejściowe − wyjściowe wywołania)")
ax.set_xlabel("Bilans wywołań między-subsystemowych [tys.]\n"
              r"$\leftarrow$ eksporter (woła innych)        importer (fundament) $\rightarrow$")

style_ax(ax, grid="x", spines="lb")

save(fig, "fig_F_pagerank_paradox.png")

print(f"\nWszystko gotowe w: {OUT}/")

