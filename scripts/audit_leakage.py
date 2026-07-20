"""Build leakage evidence from reviewed duplicate results without retraining.

This script is intentionally a consumer of earlier stages:
- exact duplicate evidence comes from results/duplicate/exact_duplicate_*.csv
- near duplicate evidence comes only from accepted rows in the reviewed queue
- metrics reuse existing heldout predictions and exclude affected rows for sensitivity

It does not modify data, retrain models, or perform another manual review.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from common import (
    FIGURES_DIR,
    RESULTS_DIR,
    ROOT,
    classification_metrics,
    ensure_dirs,
    write_json,
)

METHOD_VERSION = "leakage-audit-v1.1"
DUPLICATE_RESULTS_DIR = RESULTS_DIR / "duplicate"
LEAKAGE_RESULTS_DIR = RESULTS_DIR / "leakage"

EXACT_CLUSTERS_PATH = DUPLICATE_RESULTS_DIR / "exact_duplicate_clusters.csv"
EXACT_MEMBERS_PATH = DUPLICATE_RESULTS_DIR / "exact_duplicate_members.csv"
NEAR_REVIEW_QUEUE_PATH = DUPLICATE_RESULTS_DIR / "near_duplicate_review_queue.csv"
NEAR_REVIEW_SUMMARY_PATH = DUPLICATE_RESULTS_DIR / "near_duplicate_review_summary.json"
HELDOUT_PREDICTIONS_PATH = RESULTS_DIR / "heldout_predictions.csv"

LEAKAGE_CASES_PATH = LEAKAGE_RESULTS_DIR / "leakage_cases.csv"
LEAKAGE_HELDOUT_ROWS_PATH = LEAKAGE_RESULTS_DIR / "leakage_heldout_rows.csv"
LEAKAGE_METRICS_PATH = LEAKAGE_RESULTS_DIR / "leakage_metrics.csv"
LEAKAGE_EXAMPLES_PATH = LEAKAGE_RESULTS_DIR / "leakage_representative_examples.csv"
LEAKAGE_SUMMARY_PATH = LEAKAGE_RESULTS_DIR / "leakage_summary.json"
REPORT_PATH = ROOT / "leakage.md"

LEAKAGE_TYPE_FIGURE_PATH = FIGURES_DIR / "leakage_heldout_by_type.png"
LEAKAGE_LABEL_FIGURE_PATH = FIGURES_DIR / "leakage_heldout_by_label.png"
LEAKAGE_METRIC_FIGURE_PATH = FIGURES_DIR / "leakage_metric_sensitivity.png"


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def leakage_severity(leakage_type: str, confidence_values: list[str]) -> str:
    if "exact" in leakage_type:
        return "high"
    confidences = {str(value).strip().lower() for value in confidence_values if value}
    if "high" in confidences:
        return "medium_high"
    return "medium"


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required input not found: {path}")
    return pd.read_csv(path, keep_default_na=False)


def require_review_complete() -> dict[str, Any]:
    if not NEAR_REVIEW_SUMMARY_PATH.exists():
        raise FileNotFoundError(
            f"Near-duplicate review summary not found: {NEAR_REVIEW_SUMMARY_PATH}. "
            "Run scripts/review_near_duplicates.py first."
        )
    summary = json.loads(NEAR_REVIEW_SUMMARY_PATH.read_text(encoding="utf-8"))
    remaining = int(summary.get("remaining_needs_review_pairs", -1))
    if remaining != 0:
        raise ValueError(
            "Near-duplicate review is not complete: "
            f"remaining_needs_review_pairs={remaining}."
        )
    return summary


def build_exact_leakage_cases(clusters: pd.DataFrame, members: pd.DataFrame) -> pd.DataFrame:
    cross_split_cluster_ids = set(
        clusters.loc[clusters["cross_split"].map(as_bool), "cluster_id"].astype(str)
    )
    rows: list[dict[str, Any]] = []
    for cluster_id, group in members.groupby("cluster_id", sort=True):
        if str(cluster_id) not in cross_split_cluster_ids:
            continue
        heldout_rows = group[group["split"] == "heldout"]
        train_rows = group[group["split"] == "train"]
        for _, heldout in heldout_rows.sort_values("id").iterrows():
            for _, train in train_rows.sort_values("id").iterrows():
                rows.append(
                    {
                        "case_id": f"L_EXACT_{cluster_id}_{heldout['id']}_{train['id']}",
                        "match_type": "exact",
                        "heldout_id": heldout["id"],
                        "train_id": train["id"],
                        "heldout_label": heldout["label"],
                        "train_label": train["label"],
                        "label_conflict": heldout["label"] != train["label"],
                        "heldout_uci_row_number": int(heldout["uci_row_number"]),
                        "train_uci_row_number": int(train["uci_row_number"]),
                        "cluster_id": cluster_id,
                        "pair_id": "",
                        "word_cosine": 1.0,
                        "char_cosine": 1.0,
                        "max_cosine": 1.0,
                        "review_decision": "not_applicable_exact_duplicate",
                        "review_category": "exact_duplicate",
                        "confidence": "high",
                        "heldout_text": heldout["text"],
                        "train_text": train["text"],
                        "source_script": "scripts/audit_leakage.py",
                        "method_version": METHOD_VERSION,
                    }
                )
    return pd.DataFrame(rows)


def orient_near_pair(row: pd.Series) -> dict[str, Any]:
    if row["split_a"] == "heldout" and row["split_b"] == "train":
        return {
            "heldout_id": row["id_a"],
            "train_id": row["id_b"],
            "heldout_label": row["label_a"],
            "train_label": row["label_b"],
            "heldout_uci_row_number": int(row["uci_row_number_a"]),
            "train_uci_row_number": int(row["uci_row_number_b"]),
            "heldout_text": row["text_a"],
            "train_text": row["text_b"],
        }
    if row["split_a"] == "train" and row["split_b"] == "heldout":
        return {
            "heldout_id": row["id_b"],
            "train_id": row["id_a"],
            "heldout_label": row["label_b"],
            "train_label": row["label_a"],
            "heldout_uci_row_number": int(row["uci_row_number_b"]),
            "train_uci_row_number": int(row["uci_row_number_a"]),
            "heldout_text": row["text_b"],
            "train_text": row["text_a"],
        }
    raise ValueError(
        "Near leakage requires a train-heldout pair, got "
        f"{row['split_a']} / {row['split_b']} for pair_id={row['pair_id']}"
    )


def build_near_leakage_cases(queue: pd.DataFrame) -> pd.DataFrame:
    mask = queue["cross_split"].map(as_bool) & (
        queue["review_decision"].astype(str) == "accepted"
    )
    accepted = queue.loc[mask].copy().sort_values("pair_id")
    rows: list[dict[str, Any]] = []
    for _, row in accepted.iterrows():
        oriented = orient_near_pair(row)
        rows.append(
            {
                "case_id": f"L_NEAR_{row['pair_id']}",
                "match_type": "near_reviewed_accepted",
                **oriented,
                "label_conflict": row["label_a"] != row["label_b"],
                "cluster_id": "",
                "pair_id": row["pair_id"],
                "word_cosine": float(row["word_cosine"]),
                "char_cosine": float(row["char_cosine"]),
                "max_cosine": float(row["max_cosine"]),
                "review_decision": row["review_decision"],
                "review_category": row["review_category"],
                "confidence": row["confidence"],
                "source_script": "scripts/audit_leakage.py",
                "method_version": METHOD_VERSION,
            }
        )
    return pd.DataFrame(rows)


def build_heldout_rows(cases: pd.DataFrame, heldout_predictions: pd.DataFrame) -> pd.DataFrame:
    prediction_lookup = heldout_predictions.set_index("id", drop=False)
    exact_ids = set(cases.loc[cases["match_type"] == "exact", "heldout_id"])
    near_ids = set(cases.loc[cases["match_type"] == "near_reviewed_accepted", "heldout_id"])
    rows: list[dict[str, Any]] = []
    for heldout_id in sorted(exact_ids | near_ids):
        subset = cases[cases["heldout_id"] == heldout_id]
        exact_subset = subset[subset["match_type"] == "exact"]
        near_subset = subset[subset["match_type"] == "near_reviewed_accepted"]
        if heldout_id in exact_ids and heldout_id in near_ids:
            leakage_type = "exact_and_near_reviewed_accepted"
        elif heldout_id in exact_ids:
            leakage_type = "exact"
        else:
            leakage_type = "near_reviewed_accepted"
        pred = prediction_lookup.loc[heldout_id]
        train_partner_ids = sorted(set(subset["train_id"].astype(str)))
        rows.append(
            {
                "heldout_id": heldout_id,
                "label": pred["label"],
                "uci_row_number": int(pred["uci_row_number"]),
                "leakage_type": leakage_type,
                "severity": leakage_severity(leakage_type, list(near_subset["confidence"].astype(str))),
                "n_exact_train_partners": int(exact_subset["train_id"].nunique()),
                "n_near_train_partners": int(near_subset["train_id"].nunique()),
                "n_total_train_partners": len(train_partner_ids),
                "train_partner_ids": "|".join(train_partner_ids),
                "exact_cluster_ids": "|".join(sorted(set(exact_subset["cluster_id"].astype(str)) - {""})),
                "near_pair_ids": "|".join(sorted(set(near_subset["pair_id"].astype(str)) - {""})),
                "review_categories": "|".join(sorted(set(near_subset["review_category"].astype(str)) - {""})),
                "max_similarity": float(subset["max_cosine"].max()),
                "word_pred": pred["word_pred"],
                "char_pred": pred["char_pred"],
                "word_p_spam": float(pred["word_p_spam"]),
                "char_p_spam": float(pred["char_p_spam"]),
                "text": pred["text"],
            }
        )
    return pd.DataFrame(rows)


def build_representative_examples(cases: pd.DataFrame) -> pd.DataFrame:
    example_specs = [
        ("exact_duplicate", cases["match_type"] == "exact"),
        (
            "near_spam_campaign_template",
            (cases["match_type"] == "near_reviewed_accepted")
            & (cases["review_category"] == "same_spam_campaign_template"),
        ),
        (
            "near_ham_personalization",
            (cases["match_type"] == "near_reviewed_accepted")
            & (cases["review_category"] == "minor_personalization_change"),
        ),
    ]
    rows: list[dict[str, Any]] = []
    for example_type, mask in example_specs:
        subset = cases.loc[mask].sort_values(
            ["max_cosine", "heldout_id", "train_id"], ascending=[False, True, True]
        )
        if subset.empty:
            continue
        row = subset.iloc[0].to_dict()
        rows.append(
            {
                "example_type": example_type,
                "case_id": row["case_id"],
                "match_type": row["match_type"],
                "heldout_id": row["heldout_id"],
                "train_id": row["train_id"],
                "heldout_label": row["heldout_label"],
                "train_label": row["train_label"],
                "cluster_id": row["cluster_id"],
                "pair_id": row["pair_id"],
                "max_cosine": row["max_cosine"],
                "review_category": row["review_category"],
                "confidence": row["confidence"],
                "heldout_text": row["heldout_text"],
                "train_text": row["train_text"],
            }
        )
    return pd.DataFrame(rows)


def build_metrics(heldout_predictions: pd.DataFrame, exact_ids: set[str], near_ids: set[str]) -> pd.DataFrame:
    conditions = [
        ("original_heldout", set()),
        ("exclude_exact_leakage", exact_ids),
        ("exclude_exact_and_reviewed_near_leakage", exact_ids | near_ids),
    ]
    rows: list[dict[str, Any]] = []
    original_n = len(heldout_predictions)
    for condition, excluded_ids in conditions:
        data = heldout_predictions[~heldout_predictions["id"].isin(excluded_ids)]
        excluded = heldout_predictions[heldout_predictions["id"].isin(excluded_ids)]
        for pred_col in ("word_pred", "char_pred"):
            metrics = classification_metrics(data["label"], data[pred_col])
            rows.append(
                {
                    "condition": condition,
                    "prediction_column": pred_col,
                    "original_n": original_n,
                    "excluded_rows": int(len(excluded)),
                    "excluded_ham": int((excluded["label"] == "ham").sum()),
                    "excluded_spam": int((excluded["label"] == "spam").sum()),
                    **metrics,
                }
            )
    return pd.DataFrame(rows)


def counts_by_label(df: pd.DataFrame, label_col: str = "heldout_label") -> dict[str, int]:
    if df.empty:
        return {}
    return {str(k): int(v) for k, v in df[label_col].value_counts().sort_index().items()}


def plot_bar(counts: pd.Series, title: str, ylabel: str, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    counts.plot(kind="bar", ax=ax, color="#4C78A8")
    ax.set_title(title)
    ax.set_xlabel("")
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=20)
    for container in ax.containers:
        ax.bar_label(container, fmt="%d", padding=3)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_metric_sensitivity(metrics: pd.DataFrame) -> None:
    primary = metrics[metrics["prediction_column"] == "word_pred"].copy()
    metric_cols = ["accuracy", "spam_recall", "spam_f1", "macro_f1"]
    labels = primary["condition"].tolist()
    x = range(len(labels))
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    for metric in metric_cols:
        ax.plot(x, primary[metric], marker="o", label=metric)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=15, ha="right")
    ax.set_ylim(0.88, 1.0)
    ax.set_ylabel("score")
    ax.set_title("Held-out metric sensitivity after excluding leakage rows")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(loc="lower left", ncols=2)
    fig.tight_layout()
    fig.savefig(LEAKAGE_METRIC_FIGURE_PATH, dpi=160)
    plt.close(fig)


def write_figures(heldout_rows: pd.DataFrame, metrics: pd.DataFrame) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    plot_bar(
        heldout_rows["leakage_type"].value_counts().sort_index(),
        "Affected held-out rows by leakage type",
        "held-out rows",
        LEAKAGE_TYPE_FIGURE_PATH,
    )
    plot_bar(
        heldout_rows["label"].value_counts().sort_index(),
        "Affected held-out rows by label",
        "held-out rows",
        LEAKAGE_LABEL_FIGURE_PATH,
    )
    plot_metric_sensitivity(metrics)


def build_summary(
    exact_cases: pd.DataFrame,
    near_cases: pd.DataFrame,
    heldout_rows: pd.DataFrame,
    metrics: pd.DataFrame,
    examples: pd.DataFrame,
    review_summary: dict[str, Any],
) -> dict[str, Any]:
    exact_ids = set(exact_cases.get("heldout_id", pd.Series(dtype=str)).astype(str))
    near_ids = set(near_cases.get("heldout_id", pd.Series(dtype=str)).astype(str))
    all_ids = exact_ids | near_ids
    return {
        "source_script": "scripts/audit_leakage.py",
        "method_version": METHOD_VERSION,
        "scope": "leakage check only; no retraining, data intervention, or new manual review",
        "inputs": {
            "exact_duplicate_clusters": rel(EXACT_CLUSTERS_PATH),
            "exact_duplicate_members": rel(EXACT_MEMBERS_PATH),
            "near_duplicate_review_queue": rel(NEAR_REVIEW_QUEUE_PATH),
            "near_duplicate_review_summary": rel(NEAR_REVIEW_SUMMARY_PATH),
            "heldout_predictions": rel(HELDOUT_PREDICTIONS_PATH),
        },
        "outputs": {
            "leakage_cases": rel(LEAKAGE_CASES_PATH),
            "leakage_heldout_rows": rel(LEAKAGE_HELDOUT_ROWS_PATH),
            "leakage_metrics": rel(LEAKAGE_METRICS_PATH),
            "leakage_representative_examples": rel(LEAKAGE_EXAMPLES_PATH),
            "leakage_summary": rel(LEAKAGE_SUMMARY_PATH),
            "leakage_heldout_by_type_figure": rel(LEAKAGE_TYPE_FIGURE_PATH),
            "leakage_heldout_by_label_figure": rel(LEAKAGE_LABEL_FIGURE_PATH),
            "leakage_metric_sensitivity_figure": rel(LEAKAGE_METRIC_FIGURE_PATH),
            "report": rel(REPORT_PATH),
        },
        "review_dependency": {
            "source_script": review_summary.get("source_script", ""),
            "review_version": review_summary.get("review_version", ""),
            "remaining_needs_review_pairs": int(review_summary.get("remaining_needs_review_pairs", 0)),
        },
        "exact_cross_split_cases": int(len(exact_cases)),
        "exact_unique_heldout_ids": int(len(exact_ids)),
        "near_reviewed_accepted_cross_split_cases": int(len(near_cases)),
        "near_reviewed_accepted_unique_heldout_ids": int(len(near_ids)),
        "all_leakage_unique_heldout_ids": int(len(all_ids)),
        "heldout_rows_by_leakage_type": {str(k): int(v) for k, v in heldout_rows["leakage_type"].value_counts().sort_index().items()},
        "heldout_rows_by_severity": {str(k): int(v) for k, v in heldout_rows["severity"].value_counts().sort_index().items()},
        "heldout_rows_by_label": counts_by_label(heldout_rows, "label"),
        "case_rows_by_match_type": {"exact": int(len(exact_cases)), "near_reviewed_accepted": int(len(near_cases))},
        "representative_examples": int(len(examples)),
        "metrics_rows": int(len(metrics)),
    }


def markdown_table(df: pd.DataFrame, columns: list[str], rename: dict[str, str] | None = None) -> str:
    rename = rename or {}
    table = df.loc[:, columns].rename(columns=rename).copy()
    for col in table.columns:
        if pd.api.types.is_float_dtype(table[col]):
            table[col] = table[col].map(lambda value: f"{value:.4f}")
    lines = ["| " + " | ".join(table.columns) + " |"]
    lines.append("|" + "|".join(["---"] * len(table.columns)) + "|")
    for _, row in table.iterrows():
        values = [str(row[col]).replace("\n", " ") for col in table.columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def summary_rows(summary: dict[str, int], key_col: str, value_col: str) -> pd.DataFrame:
    rows = [{key_col: key, value_col: value} for key, value in summary.items()]
    return pd.DataFrame(rows, columns=[key_col, value_col])


def short_text(text: str, limit: int = 120) -> str:
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def write_report(
    summary: dict[str, Any],
    heldout_rows: pd.DataFrame,
    metrics: pd.DataFrame,
    examples: pd.DataFrame,
) -> None:
    leakage_type_rows = summary_rows(summary["heldout_rows_by_leakage_type"], "leakage_type", "heldout_rows")
    label_rows = summary_rows(summary["heldout_rows_by_label"], "label", "heldout_rows")
    severity_rows = summary_rows(summary["heldout_rows_by_severity"], "severity", "heldout_rows")

    primary_metrics = metrics[metrics["prediction_column"] == "word_pred"].copy()
    primary_metrics = primary_metrics[["condition", "n", "excluded_rows", "excluded_ham", "excluded_spam", "accuracy", "spam_precision", "spam_recall", "spam_f1", "macro_f1"]]

    example_report = examples.copy()
    if not example_report.empty:
        example_report["heldout_text"] = example_report["heldout_text"].map(short_text)
        example_report["train_text"] = example_report["train_text"].map(short_text)

    lines = [
        "# Leakage Analysis",
        "",
        "## Scope",
        "",
        "This leakage workflow is a check-only stage. It does not rewrite the dataset, retrain any model, or perform a second manual near-duplicate review.",
        "",
        "Leakage evidence is defined as held-out messages that have training-set duplicate evidence from either exact cross-split duplicates or accepted cross-split near duplicates from the completed duplicate review.",
        "",
        "## Leakage Types",
        "",
        "| Type | Meaning | Included here |",
        "|---|---|---|",
        "| `exact` | Held-out text appears in train under the exact duplicate rule: lowercase plus whitespace collapse. | Yes, direct leakage. |",
        "| `near_reviewed_accepted` | Held-out and train texts are not exact duplicates, but duplicate-stage review accepted them as substantively the same message, campaign, or template. | Yes, template leakage. |",
        "| rejected near candidate | A high-similarity candidate that duplicate review rejected as too generic or not substantively duplicated. | No. |",
        "",
        "Severity is a lightweight reporting field: exact leakage is `high`; near leakage with high review confidence is `medium_high`; other accepted near leakage is `medium`.",
        "",
        "## Inputs",
        "",
        f"- `{summary['inputs']['exact_duplicate_clusters']}` and `{summary['inputs']['exact_duplicate_members']}` provide exact duplicate clusters and members.",
        f"- `{summary['inputs']['near_duplicate_review_queue']}` provides reviewed near-duplicate pairs; only `review_decision=accepted` and `cross_split=True` rows are used.",
        f"- `{summary['inputs']['near_duplicate_review_summary']}` is checked to require `remaining_needs_review_pairs=0`.",
        f"- `{summary['inputs']['heldout_predictions']}` provides existing held-out predictions for metric sensitivity. These predictions are reused as-is.",
        "",
        "## Findings",
        "",
        "| Finding | Result |",
        "|---|---|",
        f"| Cross-split exact leakage pairs | {summary['exact_cross_split_cases']} |",
        f"| Unique held-out rows with exact leakage | {summary['exact_unique_heldout_ids']} |",
        f"| Accepted cross-split near leakage pairs | {summary['near_reviewed_accepted_cross_split_cases']} |",
        f"| Unique held-out rows with accepted near leakage | {summary['near_reviewed_accepted_unique_heldout_ids']} |",
        f"| Unique held-out rows with any duplicate leakage evidence | {summary['all_leakage_unique_heldout_ids']} |",
        "",
        "Held-out rows by leakage type:",
        "",
        markdown_table(leakage_type_rows, ["leakage_type", "heldout_rows"]),
        "",
        "Held-out rows by label:",
        "",
        markdown_table(label_rows, ["label", "heldout_rows"]),
        "",
        "Held-out rows by severity:",
        "",
        markdown_table(severity_rows, ["severity", "heldout_rows"]),
        "",
        "## Representative Examples",
        "",
        markdown_table(example_report, ["example_type", "case_id", "heldout_id", "train_id", "max_cosine", "review_category", "confidence", "heldout_text", "train_text"]),
        "",
        "## Metric Sensitivity",
        "",
        "The table below keeps the trained baseline predictions fixed and only removes affected held-out rows from scoring. This estimates how much reported performance depends on contaminated evaluation rows without retraining or changing data.",
        "",
        markdown_table(primary_metrics, list(primary_metrics.columns), {"n": "scored_n"}),
        "",
        "`word_pred` is shown as the primary baseline signal. `results/leakage/leakage_metrics.csv` also includes the same sensitivity rows for `char_pred`.",
        "",
        "Because the affected rows are mostly spam, spam recall and spam F1 are more sensitive than accuracy. Accuracy changes little because the held-out set is dominated by ham rows, so a small number of removed spam rows has limited effect on the overall correct/incorrect ratio.",
        "",
        "## Related Files",
        "",
        f"- `scripts/audit_leakage.py`: rebuilds the leakage check, evidence tables, metric sensitivity table, figures, and this report. It consumes reviewed duplicate outputs and does not retrain or adjudicate pairs.",
        f"- `{summary['outputs']['leakage_cases']}`: pair-level leakage evidence. One row is one train-heldout duplicate relationship, with exact cluster IDs or reviewed near pair IDs.",
        f"- `{summary['outputs']['leakage_heldout_rows']}`: sample-level leakage summary. One row is one affected held-out sample, including leakage type, severity, train partners, prediction fields, and text.",
        f"- `{summary['outputs']['leakage_metrics']}`: metric sensitivity results for `word_pred` and `char_pred` under original, exact-excluded, and exact-plus-near-excluded scoring conditions.",
        f"- `{summary['outputs']['leakage_representative_examples']}`: a small fixed set of example pairs for report illustration: exact duplicate, spam template near duplicate, and ham personalization near duplicate when available.",
        f"- `{summary['outputs']['leakage_summary']}`: machine-readable aggregate counts, input paths, output paths, and review dependency metadata.",
        f"- `{summary['outputs']['leakage_heldout_by_type_figure']}`: bar chart of affected held-out rows by leakage type.",
        f"- `{summary['outputs']['leakage_heldout_by_label_figure']}`: bar chart of affected held-out rows by label.",
        f"- `{summary['outputs']['leakage_metric_sensitivity_figure']}`: line chart showing how core held-out metrics change after excluding leakage rows.",
        "",
        "## Interpretation",
        "",
        "Exact cross-split duplicates are direct evaluation-independence problems: the held-out text already appears in training under the same normalization rule used by the duplicate audit.",
        "",
        "Accepted cross-split near duplicates are template leakage findings: the held-out message is not exactly identical under the public rule, but the duplicate-stage review accepted it as substantively the same message, campaign, or template. Rejected near candidates are intentionally excluded here.",
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    LEAKAGE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    review_summary = require_review_complete()
    clusters = read_csv(EXACT_CLUSTERS_PATH)
    members = read_csv(EXACT_MEMBERS_PATH)
    queue = read_csv(NEAR_REVIEW_QUEUE_PATH)
    heldout_predictions = read_csv(HELDOUT_PREDICTIONS_PATH)

    exact_cases = build_exact_leakage_cases(clusters, members)
    near_cases = build_near_leakage_cases(queue)
    cases = pd.concat([exact_cases, near_cases], ignore_index=True).sort_values(
        ["match_type", "heldout_id", "train_id", "pair_id", "cluster_id"]
    )
    exact_ids = set(exact_cases.get("heldout_id", pd.Series(dtype=str)).astype(str))
    near_ids = set(near_cases.get("heldout_id", pd.Series(dtype=str)).astype(str))
    heldout_rows = build_heldout_rows(cases, heldout_predictions).sort_values(["leakage_type", "heldout_id"])
    examples = build_representative_examples(cases)
    metrics = build_metrics(heldout_predictions, exact_ids, near_ids)
    summary = build_summary(exact_cases, near_cases, heldout_rows, metrics, examples, review_summary)

    cases.to_csv(LEAKAGE_CASES_PATH, index=False, lineterminator="\n")
    heldout_rows.to_csv(LEAKAGE_HELDOUT_ROWS_PATH, index=False, lineterminator="\n")
    examples.to_csv(LEAKAGE_EXAMPLES_PATH, index=False, lineterminator="\n")
    metrics.to_csv(LEAKAGE_METRICS_PATH, index=False, lineterminator="\n")
    write_figures(heldout_rows, metrics)
    write_json(LEAKAGE_SUMMARY_PATH, summary)
    write_report(summary, heldout_rows, metrics, examples)

    print(f"Wrote {rel(LEAKAGE_CASES_PATH)} ({len(cases)} rows)")
    print(f"Wrote {rel(LEAKAGE_HELDOUT_ROWS_PATH)} ({len(heldout_rows)} rows)")
    print(f"Wrote {rel(LEAKAGE_EXAMPLES_PATH)} ({len(examples)} rows)")
    print(f"Wrote {rel(LEAKAGE_METRICS_PATH)} ({len(metrics)} rows)")
    print(f"Wrote {rel(LEAKAGE_SUMMARY_PATH)}")
    print(f"Wrote {rel(REPORT_PATH)}")


if __name__ == "__main__":
    main()
