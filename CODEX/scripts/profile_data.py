"""Create dataset profiles, shallow-feature summaries, and report figures."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import FIGURES_DIR, RESULTS_DIR, ensure_dirs, load_canonical, shallow_features


COLORS = {"ham": "#3B82F6", "spam": "#EF4444"}


def style_axes(ax, title: str, ylabel: str = "") -> None:
    ax.set_title(title, loc="left", fontsize=12, fontweight="bold", pad=10)
    ax.set_ylabel(ylabel)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.18)


def main() -> None:
    ensure_dirs()
    df = load_canonical()
    features = shallow_features(df)
    enriched = pd.concat([df.reset_index(drop=True), features.reset_index(drop=True)], axis=1)

    rows = []
    for split in ("all", "train", "heldout"):
        split_df = enriched if split == "all" else enriched[enriched["split"] == split]
        for label in ("all", "ham", "spam"):
            group = split_df if label == "all" else split_df[split_df["label"] == label]
            rows.append(
                {
                    "split": split,
                    "label": label,
                    "n": len(group),
                    "class_fraction": len(group) / max(len(split_df), 1),
                    "char_median": group["char_count"].median(),
                    "char_q1": group["char_count"].quantile(0.25),
                    "char_q3": group["char_count"].quantile(0.75),
                    "token_median": group["token_count"].median(),
                    "digit_median": group["digit_count"].median(),
                    "has_url_rate": group["has_url"].mean(),
                    "has_phone_rate": group["has_phone"].mean(),
                    "has_currency_rate": (group["currency_count"] > 0).mean(),
                    "promo_token_mean": group["promo_token_count"].mean(),
                }
            )
    summary = pd.DataFrame(rows)
    summary.to_csv(RESULTS_DIR / "profile_summary.csv", index=False)
    enriched.to_csv(RESULTS_DIR / "shallow_features.csv", index=False)

    counts = (
        df.groupby(["split", "label"], observed=True).size().unstack(fill_value=0)
    )
    ax = counts[["ham", "spam"]].plot(
        kind="bar",
        color=[COLORS["ham"], COLORS["spam"]],
        figsize=(7.2, 4.2),
        rot=0,
    )
    style_axes(ax, "Class counts by fixed split", "Messages")
    ax.legend(frameon=False, ncol=2)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "class_distribution.png", dpi=180)
    plt.close()

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    bins = np.arange(0, min(260, int(enriched["char_count"].max()) + 10), 10)
    for label in ("ham", "spam"):
        values = enriched.loc[enriched["label"] == label, "char_count"].clip(upper=250)
        ax.hist(
            values,
            bins=bins,
            density=True,
            alpha=0.48,
            color=COLORS[label],
            label=label,
        )
    style_axes(ax, "Message-length distribution (clipped at 250 characters)", "Density")
    ax.set_xlabel("Characters")
    ax.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "length_distribution.png", dpi=180)
    plt.close()

    feature_names = ["has_url", "has_phone", "has_currency", "has_promo"]
    plot_df = enriched.assign(
        has_currency=(enriched["currency_count"] > 0).astype(float),
        has_promo=(enriched["promo_token_count"] > 0).astype(float),
    )
    rates = plot_df.groupby("label", observed=True)[feature_names].mean().T
    ax = rates[["ham", "spam"]].plot(
        kind="bar",
        color=[COLORS["ham"], COLORS["spam"]],
        figsize=(7.2, 4.2),
        rot=0,
    )
    style_axes(ax, "Prevalence of shallow message cues", "Share of messages")
    ax.set_xticklabels(["URL", "Phone", "Currency", "Promo token"])
    ax.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "shallow_feature_prevalence.png", dpi=180)
    plt.close()

    enriched["row_bin"] = pd.cut(
        enriched["uci_row_number"], bins=10, labels=[str(i) for i in range(1, 11)]
    )
    row_rates = (
        enriched.assign(is_spam=(enriched["label"] == "spam").astype(float))
        .groupby("row_bin", observed=True)["is_spam"]
        .agg(["mean", "count"])
        .reset_index()
    )
    row_rates.to_csv(RESULTS_DIR / "row_position_spam_rate.csv", index=False)
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.plot(
        row_rates["row_bin"],
        row_rates["mean"],
        color="#7C3AED",
        marker="o",
        linewidth=2,
    )
    style_axes(ax, "Spam rate across original corpus position", "Spam share")
    ax.set_xlabel("UCI row-position decile")
    ax.set_ylim(bottom=0)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "row_position_spam_rate.png", dpi=180)
    plt.close()

    print(summary.to_string(index=False))
    print(f"Saved profile tables to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
