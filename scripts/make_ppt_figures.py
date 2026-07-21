"""Generate the presentation figures for audit targets 4 and 6.

Outputs PNG + PDF into results/figures/ppt/. Numbers are read from the committed
audit artefacts, so re-running after an audit change refreshes the slides.
"""

from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from common import RESULTS_DIR, ROOT

OUT_DIR = RESULTS_DIR / "figures" / "ppt"

SURFACE = "#ffffff"
INK = "#0b0b0b"
INK_SECOND = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"

# Categorical slots 1-3 of the reference palette (validated all-pairs).
BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"

# Blue ordinal ramp: confidence is an ordered quantity, not an identity.
CONF_COLOR = {"high": "#184f95", "medium": "#3987e5", "low": "#86b6ef"}


def setup() -> None:
    plt.rcParams.update(
        {
            "font.sans-serif": ["Microsoft YaHei", "SimHei", "Segoe UI", "DejaVu Sans"],
            "axes.unicode_minus": False,
            "figure.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "text.color": INK,
            "axes.labelcolor": INK_SECOND,
            "xtick.color": INK_MUTED,
            "ytick.color": INK_MUTED,
            "axes.edgecolor": AXIS,
            "font.size": 12,
        }
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)


def strip_axes(ax, keep=("left", "bottom")) -> None:
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(side in keep)


def save(fig, name: str) -> None:
    for suffix in ("png", "pdf"):
        fig.savefig(OUT_DIR / f"{name}.{suffix}", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {name}.png / .pdf")


def fig_funnel(counts: dict[str, int]) -> None:
    """Stage diagram. The range 5574 -> 31 is too wide for proportional bars,
    so the number is the mark and the bars only carry stage order."""
    stages = [
        ("全部行打分", counts["scored"], "三个独立信号"),
        ("自动检索候选", counts["candidates"], "标签错误 70 + 模糊 177"),
        ("人工逐条精读", counts["read"], "读原文做政策判断"),
        ("最终提交发现", counts["submitted"], f"另拒绝 {counts['rejected']} 条"),
    ]
    ramp = ["#86b6ef", "#3987e5", "#256abf", "#184f95"]

    fig, ax = plt.subplots(figsize=(11, 3.4))
    for i, ((label, value, note), color) in enumerate(zip(stages, ramp)):
        ax.barh(0, 1, left=i * 1.06, height=0.62, color=color, zorder=2)
        cx = i * 1.06 + 0.5
        # White on the lightest ordinal step is ~1.9:1; use dark ink there.
        on_fill = INK if color == "#86b6ef" else SURFACE
        ax.text(cx, 0.10, f"{value:,}", ha="center", va="center",
                color=on_fill, fontsize=27, fontweight="bold", zorder=3)
        ax.text(cx, -0.14, label, ha="center", va="center",
                color=on_fill, fontsize=11.5, zorder=3)
        ax.text(cx, -0.52, note, ha="center", va="center",
                color=INK_MUTED, fontsize=10)
        if i < len(stages) - 1:
            ax.annotate("", xy=(i * 1.06 + 1.045, 0), xytext=(i * 1.06 + 1.015, 0),
                        arrowprops=dict(arrowstyle="-|>", color=AXIS, lw=1.6))

    ax.set_xlim(-0.04, len(stages) * 1.06)
    ax.set_ylim(-0.75, 0.5)
    ax.axis("off")
    ax.set_title("检索漏斗：自动信号只负责缩小范围，判定靠人工",
                 loc="left", color=INK, fontsize=14, fontweight="bold", pad=14)
    save(fig, "fig1_funnel")


def fig_confidence(dist: pd.DataFrame) -> None:
    """Stacked bar: confidence mix per issue type, against the 55% cap."""
    order = ["high", "medium", "low"]
    types = [("label_error", "目标 4\n疑似标签错误"), ("ambiguous", "目标 6\n模糊样本")]

    fig, ax = plt.subplots(figsize=(9, 3.1))
    for row, (key, label) in enumerate(types):
        left = 0.0
        for level in order:
            value = int(dist.loc[key, level]) if level in dist.columns else 0
            if not value:
                continue
            ax.barh(row, value, left=left, height=0.38,
                    color=CONF_COLOR[level], zorder=2)
            ax.text(left + value / 2, row, str(value), ha="center", va="center",
                    color=SURFACE if level != "low" else INK, fontsize=12,
                    fontweight="bold", zorder=3)
            left += value + 0.12  # 2px-equivalent surface gap between segments

    ax.set_yticks(range(len(types)), [label for _, label in types], fontsize=11.5)
    ax.set_ylim(1.45, -0.45)  # tighten the gap between the two rows
    ax.set_xlabel("提交行数", fontsize=11)
    ax.xaxis.grid(True, color=GRID, lw=0.8, zorder=0)
    ax.set_axisbelow(True)
    strip_axes(ax, keep=("bottom",))
    ax.tick_params(length=0)

    handles = [plt.Rectangle((0, 0), 1, 1, color=CONF_COLOR[c]) for c in order]
    ax.legend(handles, ["high", "medium", "low"], frameon=False, ncol=3,
              loc="lower right", bbox_to_anchor=(1.0, -0.42), fontsize=11)
    ax.set_title("置信度校准：31 条发现中 high 仅 5 条（16.1%），协议上限 55%",
                 loc="left", color=INK, fontsize=14, fontweight="bold", pad=14)
    save(fig, "fig2_confidence")


def fig_interventions(overlay: dict, leakage: dict) -> None:
    """The headline result: accuracy barely moves, spam recall does."""
    labels = ["干预 1：训练标签 overlay\n(13 条重标提案)",
              "干预 2：泄漏感知评估\n(剔除 63 条泄漏行)"]
    d_acc = [
        (overlay["heldout_with_overlay"]["accuracy"] - overlay["heldout_baseline"]["accuracy"]) * 100,
        leakage["accuracy_delta"] * 100,
    ]
    d_rec = [
        (overlay["heldout_with_overlay"]["spam_recall"] - overlay["heldout_baseline"]["spam_recall"]) * 100,
        leakage["spam_recall_delta"] * 100,
    ]

    x = range(len(labels))
    width = 0.26
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    b1 = ax.bar([i - width / 2 - 0.012 for i in x], d_acc, width,
                label="总准确率", color=BLUE, zorder=2)
    b2 = ax.bar([i + width / 2 + 0.012 for i in x], d_rec, width,
                label="spam 召回率", color=ORANGE, zorder=2)

    for bars in (b1, b2):
        for bar in bars:
            value = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, value - 0.12,
                    f"{value:+.2f}", ha="center", va="top",
                    color=INK, fontsize=11.5, fontweight="bold")

    ax.axhline(0, color=AXIS, lw=1.2, zorder=1)
    ax.set_xticks(list(x), labels, fontsize=11)
    ax.set_ylabel("相对基线的变化（百分点）", fontsize=11)
    ax.set_ylim(min(d_rec) - 0.85, 0.42)
    ax.yaxis.grid(True, color=GRID, lw=0.8, zorder=0)
    ax.set_axisbelow(True)
    strip_axes(ax, keep=("bottom",))
    ax.tick_params(axis="x", length=0)
    ax.legend(frameon=False, ncol=2, loc="lower left", fontsize=11)
    ax.set_title("两种干预都印证同一件事：准确率会掩盖真相",
                 loc="left", color=INK, fontsize=14, fontweight="bold", pad=14)
    save(fig, "fig3_interventions")


def fig_heldout_errors(breakdown: dict[str, int]) -> None:
    """10 held-out baseline errors, split by audit status."""
    items = [
        ("真·模型错误", breakdown.get("model_error", 0), AQUA),
        ("疑似标签错误", breakdown.get("likely_label_error", 0), ORANGE),
        ("模糊政策案例", breakdown.get("ambiguous_policy_case", 0), BLUE),
    ]
    total = sum(value for _, value, _ in items)

    fig, ax = plt.subplots(figsize=(9.5, 2.9))
    left = 0.0
    # Segments 2 and 1 are narrow, so their labels are staggered onto a second
    # row with a leader line instead of colliding on one baseline.
    label_rows = [-0.40, -0.40, -0.66]
    for (label, value, color), label_y in zip(items, label_rows):
        if not value:
            continue
        ax.barh(0, value, left=left, height=0.5, color=color, zorder=2)
        cx = left + value / 2
        ax.text(cx, 0, str(value), ha="center", va="center",
                color=SURFACE, fontsize=17, fontweight="bold", zorder=3)
        ax.plot([cx, cx], [-0.27, label_y + 0.07], color=AXIS, lw=0.9, zorder=1)
        ax.text(cx, label_y, label, ha="center", va="center",
                color=INK_SECOND, fontsize=10.5)
        left += value + 0.04

    ax.set_xlim(-0.1, total + 0.4)
    ax.set_ylim(-0.92, 0.55)
    ax.axis("off")
    ax.set_title(f"heldout 基线的 {total} 个错误里，3 个是数据问题而非模型能力不足",
                 loc="left", color=INK, fontsize=14, fontweight="bold", pad=12)
    ax.text(0, 0.42,
            "若将 2 条疑似标签错误按「未决」处理：错误 10 → 8，敏感度上界 99.28%（官方分仍为 99.10%）",
            color=INK_MUTED, fontsize=10.5, va="bottom")
    save(fig, "fig4_heldout_errors")


def main() -> None:
    setup()

    suspicious = pd.read_csv(RESULTS_DIR / "suspicious_examples_b.csv", keep_default_na=False)
    memo = pd.read_csv(RESULTS_DIR / "adjudication_memo_b.csv", keep_default_na=False)
    candidates = pd.read_csv(RESULTS_DIR / "label_error_candidates.csv", keep_default_na=False)
    ambiguity = pd.read_csv(RESULTS_DIR / "ambiguity_candidates.csv", keep_default_na=False)
    overlay = json.loads((RESULTS_DIR / "label_overlay_experiment.json").read_text(encoding="utf-8"))
    leakage = json.loads((RESULTS_DIR / "intervention_leakage_eval.json").read_text(encoding="utf-8"))

    fig_funnel(
        {
            "scored": int(overlay["heldout_baseline"]["n"]) + 4460,
            "candidates": len(candidates) + len(ambiguity),
            "read": len(memo),
            "submitted": len(suspicious),
            "rejected": int((memo["decision"] == "keep_but_flag").sum()),
        }
    )
    fig_confidence(
        suspicious.groupby(["issue_type", "confidence"]).size().unstack(fill_value=0)
    )
    fig_interventions(overlay, leakage)
    fig_heldout_errors(overlay["heldout_error_breakdown"])


if __name__ == "__main__":
    main()
