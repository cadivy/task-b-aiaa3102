"""Create an audit-focused dataset profile and write profile.md.

This script intentionally reuses the public data helpers in common.py so the
profile is tied to the same canonical table, normalization rule, and shallow
features used by the rest of the audit pipeline.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import (
    FIGURES_DIR,
    RESULTS_DIR,
    ROOT,
    ensure_dirs,
    load_canonical,
    normalize_text,
    shallow_features,
    write_json,
)

COLORS = {"ham": "#2563EB", "spam": "#DC2626"}
PROFILE_RESULTS_DIR = RESULTS_DIR / "profile"
ARTIFACT_PATTERNS = {
    "html_escape": re.compile(r"&(?:amp|lt|gt|quot|apos|#\d+);", re.I),
    "replacement_character": re.compile("\ufffd"),
    "mojibake_marker": re.compile(r"(?:\u00e2\u20ac|\u00c3|\u00c2|\ufffd)"),
    "non_ascii": re.compile(r"[^\x00-\x7F]"),
}


def pct(value: float) -> str:
    return f"{100 * value:.2f}%"


def fmt_number(value: float | int) -> str:
    if isinstance(value, float) and not value.is_integer():
        return f"{value:.2f}"
    return str(int(value))


def style_axes(ax, title: str, ylabel: str = "") -> None:
    ax.set_title(title, loc="left", fontsize=12, fontweight="bold", pad=10)
    ax.set_ylabel(ylabel)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.18)


def read_json_if_exists(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    features = shallow_features(df)
    enriched = pd.concat([df.reset_index(drop=True), features.reset_index(drop=True)], axis=1)
    enriched["has_currency"] = (enriched["currency_count"] > 0).astype(float)
    enriched["has_promo"] = (enriched["promo_token_count"] > 0).astype(float)
    enriched["over_160_chars"] = (enriched["char_count"] > 160).astype(float)
    enriched["normalized_text"] = enriched["text"].map(normalize_text)
    return enriched


def build_profile_summary(enriched: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for split in ("all", "train", "heldout"):
        split_df = enriched if split == "all" else enriched[enriched["split"] == split]
        for label in ("all", "ham", "spam"):
            group = split_df if label == "all" else split_df[split_df["label"] == label]
            rows.append(
                {
                    "split": split,
                    "label": label,
                    "n": int(len(group)),
                    "class_fraction": len(group) / max(len(split_df), 1),
                    "char_median": group["char_count"].median(),
                    "char_q1": group["char_count"].quantile(0.25),
                    "char_q3": group["char_count"].quantile(0.75),
                    "token_median": group["token_count"].median(),
                    "digit_median": group["digit_count"].median(),
                    "has_url_rate": group["has_url"].mean(),
                    "has_phone_rate": group["has_phone"].mean(),
                    "has_currency_rate": group["has_currency"].mean(),
                    "has_promo_rate": group["has_promo"].mean(),
                    "promo_token_mean": group["promo_token_count"].mean(),
                    "over_160_chars_rate": group["over_160_chars"].mean(),
                }
            )
    return pd.DataFrame(rows)


def build_split_comparison(enriched: pd.DataFrame) -> pd.DataFrame:
    metrics = [
        ("spam_share", lambda g: (g["label"] == "spam").mean()),
        ("char_median", lambda g: g["char_count"].median()),
        ("token_median", lambda g: g["token_count"].median()),
        ("has_url_rate", lambda g: g["has_url"].mean()),
        ("has_phone_rate", lambda g: g["has_phone"].mean()),
        ("has_currency_rate", lambda g: g["has_currency"].mean()),
        ("has_promo_rate", lambda g: g["has_promo"].mean()),
        ("over_160_chars_rate", lambda g: g["over_160_chars"].mean()),
    ]
    rows = []
    for label in ("all", "ham", "spam"):
        subset = enriched if label == "all" else enriched[enriched["label"] == label]
        train = subset[subset["split"] == "train"]
        heldout = subset[subset["split"] == "heldout"]
        for metric, func in metrics:
            train_value = float(func(train)) if len(train) else math.nan
            heldout_value = float(func(heldout)) if len(heldout) else math.nan
            rows.append(
                {
                    "label": label,
                    "metric": metric,
                    "train": train_value,
                    "heldout": heldout_value,
                    "heldout_minus_train": heldout_value - train_value,
                }
            )
    return pd.DataFrame(rows)


def build_duplicate_overview(enriched: pd.DataFrame) -> pd.DataFrame:
    grouped = enriched.groupby("normalized_text", sort=False)
    clusters = grouped.agg(
        cluster_size=("id", "size"),
        labels=("label", lambda s: "|".join(sorted(s.unique()))),
        splits=("split", lambda s: "|".join(sorted(s.unique()))),
        members=("id", lambda s: "|".join(s)),
    ).reset_index()
    duplicate_clusters = clusters[clusters["cluster_size"] > 1].copy()
    exact_cluster_count = int(len(duplicate_clusters))
    duplicate_rows = int(duplicate_clusters["cluster_size"].sum())
    repeated_rows_beyond_first = int((duplicate_clusters["cluster_size"] - 1).sum())
    cross_split_clusters = int(duplicate_clusters[duplicate_clusters["splits"].str.contains("heldout") & duplicate_clusters["splits"].str.contains("train")].shape[0])
    label_conflict_clusters = int(
        duplicate_clusters[duplicate_clusters["labels"].str.contains("|", regex=False)].shape[0]
    )
    largest = duplicate_clusters.sort_values("cluster_size", ascending=False).head(1)
    largest_size = int(largest["cluster_size"].iloc[0]) if len(largest) else 0
    largest_members = largest["members"].iloc[0] if len(largest) else ""
    normalized_unique_texts = int(enriched["normalized_text"].nunique())

    return pd.DataFrame(
        [
            {"metric": "total_rows", "value": int(len(enriched))},
            {"metric": "normalized_unique_texts", "value": normalized_unique_texts},
            {"metric": "exact_duplicate_clusters", "value": exact_cluster_count},
            {"metric": "rows_in_exact_duplicate_clusters", "value": duplicate_rows},
            {"metric": "repeated_rows_beyond_first", "value": repeated_rows_beyond_first},
            {"metric": "cross_split_exact_clusters", "value": cross_split_clusters},
            {"metric": "label_conflict_exact_clusters", "value": label_conflict_clusters},
            {"metric": "largest_exact_cluster_size", "value": largest_size},
            {"metric": "largest_exact_cluster_members", "value": largest_members},
        ]
    )


def build_row_position(enriched: pd.DataFrame) -> pd.DataFrame:
    data = enriched.copy()
    data["row_bin"] = pd.cut(
        data["uci_row_number"], bins=10, labels=[str(i) for i in range(1, 11)]
    )
    return (
        data.assign(is_spam=(data["label"] == "spam").astype(float))
        .groupby("row_bin", observed=True)["is_spam"]
        .agg(["mean", "count"])
        .reset_index()
    )


def build_artifact_summary(enriched: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, pattern in ARTIFACT_PATTERNS.items():
        mask = enriched["text"].str.contains(pattern, regex=True, na=False)
        rows.append(
            {
                "artifact_type": name,
                "n": int(mask.sum()),
                "rate": float(mask.mean()),
                "example_ids": "|".join(enriched.loc[mask, "id"].head(5).tolist()),
            }
        )
    return pd.DataFrame(rows)


def write_figures(enriched: pd.DataFrame, row_rates: pd.DataFrame) -> None:
    counts = enriched.groupby(["split", "label"], observed=True).size().unstack(fill_value=0)
    ax = counts[["ham", "spam"]].plot(
        kind="bar",
        color=[COLORS["ham"], COLORS["spam"]],
        figsize=(7.2, 4.2),
        rot=0,
    )
    style_axes(ax, "Class counts by fixed split", "Messages")
    ax.legend(frameon=False, ncol=2)
    plt.tight_layout()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    plt.savefig(FIGURES_DIR / "class_distribution.png", dpi=180)
    plt.close()

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    bins = np.arange(0, min(260, int(enriched["char_count"].max()) + 10), 10)
    for label in ("ham", "spam"):
        values = enriched.loc[enriched["label"] == label, "char_count"].clip(upper=250)
        ax.hist(values, bins=bins, density=True, alpha=0.48, color=COLORS[label], label=label)
    style_axes(ax, "Message-length distribution (clipped at 250 characters)", "Density")
    ax.set_xlabel("Characters")
    ax.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "length_distribution.png", dpi=180)
    plt.close()

    feature_names = ["has_url", "has_phone", "has_currency", "has_promo", "over_160_chars"]
    rates = enriched.groupby("label", observed=True)[feature_names].mean().T
    ax = rates[["ham", "spam"]].plot(
        kind="bar",
        color=[COLORS["ham"], COLORS["spam"]],
        figsize=(7.6, 4.2),
        rot=20,
    )
    style_axes(ax, "Prevalence of shallow message cues", "Share of messages")
    ax.set_xticklabels(["URL", "Phone", "Currency", "Promo token", ">160 chars"])
    ax.legend(frameon=False)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "shallow_feature_prevalence.png", dpi=180)
    plt.close()

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.plot(row_rates["row_bin"], row_rates["mean"], color="#7C3AED", marker="o", linewidth=2)
    style_axes(ax, "Spam rate across original corpus position", "Spam share")
    ax.set_xlabel("UCI row-position decile")
    ax.set_ylim(bottom=0)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "row_position_spam_rate.png", dpi=180)
    plt.close()


def generate_markdown(
    enriched: pd.DataFrame,
    summary: pd.DataFrame,
    split_comparison: pd.DataFrame,
    duplicate_overview: pd.DataFrame,
    row_rates: pd.DataFrame,
    artifact_summary: pd.DataFrame,
) -> str:
    provenance = read_json_if_exists(RESULTS_DIR / "data_provenance.json")
    validation = read_json_if_exists(RESULTS_DIR / "data_validation.json")

    class_counts = enriched.groupby(["split", "label"], observed=True).size().unstack(fill_value=0)
    all_counts = enriched.groupby("label", observed=True).size()

    ham_all = int(all_counts.get("ham", 0))
    spam_all = int(all_counts.get("spam", 0))
    total = int(len(enriched))
    train_total = int((enriched["split"] == "train").sum())
    heldout_total = int((enriched["split"] == "heldout").sum())
    train_spam_share = class_counts.loc["train", "spam"] / class_counts.loc["train"].sum()
    heldout_spam_share = class_counts.loc["heldout", "spam"] / class_counts.loc["heldout"].sum()

    def row(split: str, label: str) -> pd.Series:
        return summary[(summary["split"] == split) & (summary["label"] == label)].iloc[0]

    ham = row("all", "ham")
    spam = row("all", "spam")
    dup = dict(zip(duplicate_overview["metric"], duplicate_overview["value"]))
    row_min = float(row_rates["mean"].min())
    row_max = float(row_rates["mean"].max())

    split_all = split_comparison[split_comparison["label"] == "all"]
    split_lines = []
    for metric in ("char_median", "has_url_rate", "has_phone_rate", "has_promo_rate", "over_160_chars_rate"):
        item = split_all[split_all["metric"] == metric].iloc[0]
        train_value = float(item["train"])
        heldout_value = float(item["heldout"])
        if metric.endswith("rate") or metric == "has_url_rate" or metric == "has_phone_rate":
            train_text = pct(train_value)
            heldout_text = pct(heldout_value)
        else:
            train_text = fmt_number(train_value)
            heldout_text = fmt_number(heldout_value)
        split_lines.append(f"| `{metric}` | {train_text} | {heldout_text} |")

    artifact_lines = []
    for _, item in artifact_summary.iterrows():
        artifact_lines.append(
            f"| `{item['artifact_type']}` | {int(item['n'])} | {pct(float(item['rate']))} | {item['example_ids'] or '-'} |"
        )

    archive_sha = provenance.get("archive_sha256", "not recorded")
    raw_sha = provenance.get("raw_file_sha256", validation.get("raw_sha256", "not recorded"))
    decoded_encoding = validation.get("decoded_encoding", "not recorded")
    normalized_unique = int(dup["normalized_unique_texts"])
    repeated_rows = int(dup["repeated_rows_beyond_first"])

    return f"""# Dataset Profile

## 1. Provenance and Integrity

The profile uses `data/canonical_sms.csv`, loaded through `load_canonical()` with `keep_default_na=False` so literal SMS strings such as `NA`, `null`, or `nan` are not silently converted to missing values. The canonical table is the same public working table used by the downstream duplicate, leakage, label-noise, and shortcut audits.

| Check | Result |
|---|---:|
| Total rows | {total} |
| Train rows | {train_total} |
| Held-out rows | {heldout_total} |
| Unique IDs | {validation.get('unique_ids', enriched['id'].nunique())} |
| Unique UCI row numbers | {validation.get('unique_row_numbers', enriched['uci_row_number'].nunique())} |
| Empty text rows | {validation.get('empty_text_rows', int((enriched['text'].str.len() == 0).sum()))} |
| Decoded encoding | {decoded_encoding} |

The UCI archive SHA-256 is `{archive_sha}`. The extracted raw file SHA-256 is `{raw_sha}`. The join against the fixed manifest preserves the official split and does not regenerate row assignments.

## 2. Split and Class Balance

| Split | Ham | Spam | Total | Spam share |
|---|---:|---:|---:|---:|
| Train | {int(class_counts.loc['train', 'ham'])} | {int(class_counts.loc['train', 'spam'])} | {train_total} | {pct(train_spam_share)} |
| Held-out | {int(class_counts.loc['heldout', 'ham'])} | {int(class_counts.loc['heldout', 'spam'])} | {heldout_total} | {pct(heldout_spam_share)} |
| All | {ham_all} | {spam_all} | {total} | {pct(spam_all / total)} |

Train and held-out have nearly identical spam prevalence, so the fixed split is not visibly shifted in its label prior. The strong class imbalance still matters: because spam is only {pct(spam_all / total)} of the corpus, later model summaries should emphasize spam recall, spam F1, and macro-F1 rather than accuracy alone.

## 3. Message Length and Surface Cues

| Quantity | Ham | Spam |
|---|---:|---:|
| Median characters | {fmt_number(float(ham['char_median']))} | {fmt_number(float(spam['char_median']))} |
| Median tokens | {fmt_number(float(ham['token_median']))} | {fmt_number(float(spam['token_median']))} |
| Median digits | {fmt_number(float(ham['digit_median']))} | {fmt_number(float(spam['digit_median']))} |
| Contains URL | {pct(float(ham['has_url_rate']))} | {pct(float(spam['has_url_rate']))} |
| Contains phone-like number | {pct(float(ham['has_phone_rate']))} | {pct(float(spam['has_phone_rate']))} |
| Contains currency cue | {pct(float(ham['has_currency_rate']))} | {pct(float(spam['has_currency_rate']))} |
| Contains promotional token | {pct(float(ham['has_promo_rate']))} | {pct(float(spam['has_promo_rate']))} |
| Over 160 characters | {pct(float(ham['over_160_chars_rate']))} | {pct(float(spam['over_160_chars_rate']))} |
| Mean promotional-token count | {float(ham['promo_token_mean']):.2f} | {float(spam['promo_token_mean']):.2f} |

Spam messages are much longer and have far stronger contact, currency, digit, and promotional cues. This is a descriptive profile finding, not by itself a claim that labels are wrong. It motivates the separate shortcut audit.

## 4. Train/Held-out Comparability Beyond Labels

| Metric | Train | Held-out |
|---|---:|---:|
{chr(10).join(split_lines)}

The held-out set is broadly similar to train on these coarse surface metrics. The most important visible difference is slightly higher phone-like-number prevalence in held-out, which is useful context when interpreting spam recall on the fixed split.

## 5. Duplicate Overview

Applying the public exact-duplicate rule through `normalize_text()` leaves {normalized_unique} unique normalized texts. That means {repeated_rows} rows are repetitions beyond the first occurrence.

| Metric | Result |
|---|---:|
| Exact duplicate clusters | {int(dup['exact_duplicate_clusters'])} |
| Rows in exact duplicate clusters | {int(dup['rows_in_exact_duplicate_clusters'])} |
| Cross-split exact clusters | {int(dup['cross_split_exact_clusters'])} |
| Exact clusters with label conflict | {int(dup['label_conflict_exact_clusters'])} |
| Largest exact cluster size | {int(dup['largest_exact_cluster_size'])} |

This section is only a profile-level overview. The full cluster lists, near-duplicate search, threshold sensitivity, and manual accept/reject decisions belong in `audit/duplicates.md` and `audit/leakage.md`.

## 6. Row Position and Encoding Artifacts

The original UCI row position was checked by decile. Spam prevalence ranges from {pct(row_min)} to {pct(row_max)} across deciles, so row position does not show a strong label leak in this profile pass.

| Artifact type | Rows | Rate | Example IDs |
|---|---:|---:|---|
{chr(10).join(artifact_lines)}

HTML escapes and non-ASCII characters are retained because they are part of the released corpus. The profile stage records them rather than cleaning them away, so later scripts continue to audit the same public text.

## 7. Implications for the Audit

The data foundation is internally consistent, but three properties shape the rest of the audit: spam is a minority class, spam has strong surface cues, and repeated normalized texts are common. The next steps should therefore keep duplicate/leakage findings separate from shortcut findings, and should avoid interpreting high accuracy without class-specific metrics and leakage-aware sensitivity checks.

## Reproducible Evidence

- `results/data_provenance.json`
- `results/data_validation.json`
- `results/profile/profile_summary.csv`
- `results/profile/split_comparison.csv`
- `results/profile/encoding_artifact_summary.csv`
- `results/profile/row_position_spam_rate.csv`
- `results/profile/shallow_features.csv`
- `results/figures/class_distribution.png`
- `results/figures/length_distribution.png`
- `results/figures/shallow_feature_prevalence.png`
- `results/figures/row_position_spam_rate.png`
"""


def main() -> None:
    ensure_dirs()
    PROFILE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    enriched = add_derived_features(load_canonical())
    summary = build_profile_summary(enriched)
    split_comparison = build_split_comparison(enriched)
    duplicate_overview = build_duplicate_overview(enriched)
    row_rates = build_row_position(enriched)
    artifact_summary = build_artifact_summary(enriched)

    summary.to_csv(PROFILE_RESULTS_DIR / "profile_summary.csv", index=False)
    split_comparison.to_csv(PROFILE_RESULTS_DIR / "split_comparison.csv", index=False)
    row_rates.to_csv(PROFILE_RESULTS_DIR / "row_position_spam_rate.csv", index=False)
    artifact_summary.to_csv(PROFILE_RESULTS_DIR / "encoding_artifact_summary.csv", index=False)
    enriched.drop(columns=["normalized_text"]).to_csv(PROFILE_RESULTS_DIR / "shallow_features.csv", index=False)
    write_json(
        PROFILE_RESULTS_DIR / "profile_manifest.json",
        {
            "source_script": "scripts/profile_data.py",
            "inputs": ["data/canonical_sms.csv", "results/data_provenance.json", "results/data_validation.json"],
            "outputs": [
                "audit/profile.md",
                "results/profile/profile_summary.csv",
                "results/profile/split_comparison.csv",
                "results/profile/encoding_artifact_summary.csv",
                "results/profile/row_position_spam_rate.csv",
                "results/profile/shallow_features.csv",
                "results/figures/class_distribution.png",
                "results/figures/length_distribution.png",
                "results/figures/shallow_feature_prevalence.png",
                "results/figures/row_position_spam_rate.png",
            ],
            "uses_common_helpers": ["load_canonical", "shallow_features", "normalize_text", "write_json"],
        },
    )

    write_figures(enriched, row_rates)
    profile_text = generate_markdown(
        enriched, summary, split_comparison, duplicate_overview, row_rates, artifact_summary
    )
    (ROOT / "audit" / "profile.md").write_text(profile_text, encoding="utf-8")

    print(summary.to_string(index=False))
    print(f"Wrote {(ROOT / 'profile.md')}")


if __name__ == "__main__":
    main()
