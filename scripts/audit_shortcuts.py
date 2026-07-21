"""Audit shallow shortcut features against the fixed held-out text baseline.

The shallow probes never receive raw token order.  They use only derived
surface features from ``common.shallow_features``.  The existing word-model
predictions are treated as the frozen full-text control, so this script does
not overwrite or retrain the shared baseline.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from common import (
    FIGURES_DIR,
    RESULTS_DIR,
    ROOT,
    classification_metrics,
    ensure_dirs,
    load_canonical,
    load_protocol,
    mask_promotional_tokens,
    shallow_features,
    write_json,
)


SEED = 42
SHORTCUT_RESULTS_DIR = RESULTS_DIR / "shortcut"
REVIEW_LEDGER_PATH = ROOT / "configs" / "shortcut_manual_review.csv"
REPORT_PATH = ROOT / "audit" / "shortcut_features.md"

SHAPE_FEATURES = [
    "char_count",
    "token_count",
    "avg_token_length",
    "uppercase_ratio",
    "exclamation_count",
]
CONTACT_PROMO_FEATURES = [
    "digit_count",
    "digit_ratio",
    "currency_count",
    "has_url",
    "has_phone",
    "promo_token_count",
]
ALL_SHALLOW_FEATURES = SHAPE_FEATURES + CONTACT_PROMO_FEATURES
FEATURE_SETS = {
    "shape_only": SHAPE_FEATURES,
    "contact_promo_only": CONTACT_PROMO_FEATURES,
    "all_shallow": ALL_SHALLOW_FEATURES,
    "row_position_only": ["row_position"],
    "all_shallow_plus_position": ALL_SHALLOW_FEATURES + ["row_position"],
}

METRIC_COLUMNS = [
    "condition",
    "model_family",
    "feature_set",
    "n",
    "accuracy",
    "spam_precision",
    "spam_recall",
    "spam_f1",
    "macro_f1",
    "tn",
    "fp",
    "fn",
    "tp",
    "warning_threshold",
    "above_warning_threshold",
]


def shallow_logistic_pipeline() -> Pipeline:
    """Match the baseline classifier family while standardizing numeric cues."""
    return Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "model",
                LogisticRegression(
                    C=4.0,
                    max_iter=2000,
                    solver="liblinear",
                    random_state=SEED,
                ),
            ),
        ]
    )


def masked_text_pipeline() -> Pipeline:
    """Baseline-family stress test after masking the small promo lexicon."""
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    strip_accents="unicode",
                    ngram_range=(1, 2),
                    min_df=2,
                    max_df=0.995,
                    sublinear_tf=True,
                ),
            ),
            (
                "model",
                LogisticRegression(
                    C=4.0,
                    max_iter=2000,
                    solver="liblinear",
                    random_state=SEED,
                ),
            ),
        ]
    )


def metric_row(
    condition: str,
    model_family: str,
    feature_set: str,
    y_true: pd.Series,
    y_pred: np.ndarray | pd.Series,
    warning_threshold: float,
) -> dict[str, object]:
    values = classification_metrics(y_true, y_pred)
    confusion = values.pop("confusion_matrix_ham_spam")
    tn, fp = confusion[0]
    fn, tp = confusion[1]
    return {
        "condition": condition,
        "model_family": model_family,
        "feature_set": feature_set,
        **values,
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
        "warning_threshold": warning_threshold,
        "above_warning_threshold": bool(values["accuracy"] >= warning_threshold),
    }


def load_frozen_baseline(heldout: pd.DataFrame) -> pd.DataFrame:
    path = RESULTS_DIR / "heldout_predictions.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing frozen baseline: {path}")

    baseline = pd.read_csv(path, keep_default_na=False)
    required = {"id", "label", "text", "word_p_spam", "word_pred", "prediction_source"}
    missing = required.difference(baseline.columns)
    if missing:
        raise AssertionError(f"Frozen baseline is missing columns: {sorted(missing)}")
    if baseline["id"].duplicated().any():
        raise AssertionError("Frozen baseline contains duplicate ids")

    aligned = heldout[["id", "label", "text"]].merge(
        baseline[
            ["id", "label", "text", "word_p_spam", "word_pred", "prediction_source"]
        ],
        on="id",
        how="left",
        validate="one_to_one",
        suffixes=("_canonical", "_baseline"),
    )
    if aligned["word_p_spam"].isna().any():
        raise AssertionError("Frozen baseline does not cover every held-out id")
    if not (aligned["label_canonical"] == aligned["label_baseline"]).all():
        raise AssertionError("Baseline labels do not match the canonical held-out labels")
    if not (aligned["text_canonical"] == aligned["text_baseline"]).all():
        raise AssertionError("Baseline text does not match the canonical held-out text")
    if set(aligned["prediction_source"]) != {"fit-all-train"}:
        raise AssertionError("Held-out baseline must come from the shared fit-all-train model")

    return aligned[
        ["id", "word_p_spam", "word_pred", "prediction_source"]
    ].rename(
        columns={
            "word_p_spam": "full_text_p_spam",
            "word_pred": "full_text_pred",
            "prediction_source": "full_text_prediction_source",
        }
    )


def feature_prevalence_table(
    df: pd.DataFrame, features: pd.DataFrame
) -> pd.DataFrame:
    joined = pd.concat(
        [df[["split", "label"]].reset_index(drop=True), features.reset_index(drop=True)],
        axis=1,
    )
    rows: list[dict[str, object]] = []
    for split in ("train", "heldout"):
        for label in ("ham", "spam"):
            group = joined[(joined["split"] == split) & (joined["label"] == label)]
            for feature in ALL_SHALLOW_FEATURES + ["row_position"]:
                values = group[feature]
                rows.append(
                    {
                        "split": split,
                        "label": label,
                        "feature": feature,
                        "n": int(len(values)),
                        "mean": float(values.mean()),
                        "median": float(values.median()),
                        "q75": float(values.quantile(0.75)),
                        "nonzero_rate": float((values > 0).mean()),
                    }
                )
    return pd.DataFrame(rows)


def fit_probes(
    train: pd.DataFrame,
    heldout: pd.DataFrame,
    train_features: pd.DataFrame,
    heldout_features: pd.DataFrame,
    frozen_baseline: pd.DataFrame,
    warning_threshold: float,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    predictions = heldout[["id", "split", "uci_row_number", "label", "text"]].copy()
    predictions = predictions.merge(frozen_baseline, on="id", how="left", validate="one_to_one")
    metric_rows: list[dict[str, object]] = []
    coefficient_rows: list[dict[str, object]] = []

    majority = np.repeat(train["label"].mode().iat[0], len(heldout))
    predictions["majority_ham_pred"] = majority
    metric_rows.append(
        metric_row(
            "majority_ham",
            "constant",
            "training majority label only",
            heldout["label"],
            majority,
            warning_threshold,
        )
    )

    for condition, columns in FEATURE_SETS.items():
        model = shallow_logistic_pipeline()
        model.fit(train_features[columns], train["label"])
        spam_index = list(model.classes_).index("spam")
        probability = model.predict_proba(heldout_features[columns])[:, spam_index]
        predicted = np.where(probability >= 0.5, "spam", "ham")
        predictions[f"{condition}_p_spam"] = probability
        predictions[f"{condition}_pred"] = predicted
        metric_rows.append(
            metric_row(
                condition,
                "standardized logistic regression",
                ";".join(columns),
                heldout["label"],
                predicted,
                warning_threshold,
            )
        )

        coefficients = model.named_steps["model"].coef_[0]
        ordered = sorted(
            zip(columns, coefficients, strict=True),
            key=lambda item: abs(item[1]),
            reverse=True,
        )
        for rank, (feature, coefficient) in enumerate(ordered, start=1):
            coefficient_rows.append(
                {
                    "condition": condition,
                    "feature": feature,
                    "standardized_coefficient": float(coefficient),
                    "absolute_coefficient": float(abs(coefficient)),
                    "absolute_rank": rank,
                }
            )

    masked_model = masked_text_pipeline()
    masked_model.fit(train["text"].map(mask_promotional_tokens), train["label"])
    masked_spam_index = list(masked_model.classes_).index("spam")
    masked_probability = masked_model.predict_proba(
        heldout["text"].map(mask_promotional_tokens)
    )[:, masked_spam_index]
    masked_predicted = np.where(masked_probability >= 0.5, "spam", "ham")
    predictions["masked_text_p_spam"] = masked_probability
    predictions["masked_text_pred"] = masked_predicted
    metric_rows.append(
        metric_row(
            "masked_text",
            "TF-IDF word/bigram logistic regression",
            "raw text with 15 promotional tokens replaced",
            heldout["label"],
            masked_predicted,
            warning_threshold,
        )
    )

    metric_rows.append(
        metric_row(
            "full_text",
            "frozen TF-IDF word/bigram logistic regression",
            "results/heldout_predictions.csv",
            heldout["label"],
            predictions["full_text_pred"],
            warning_threshold,
        )
    )

    metrics = pd.DataFrame(metric_rows)[METRIC_COLUMNS]
    coefficients = pd.DataFrame(coefficient_rows)
    return metrics, coefficients, predictions


def cue_snapshot(row: pd.Series) -> str:
    return ";".join(
        [
            f"digits={int(row['digit_count'])}",
            f"currency={int(row['currency_count'])}",
            f"url={int(row['has_url'])}",
            f"phone={int(row['has_phone'])}",
            f"promo_tokens={int(row['promo_token_count'])}",
            f"chars={int(row['char_count'])}",
        ]
    )


def build_review_queue(
    predictions: pd.DataFrame, heldout_features: pd.DataFrame
) -> pd.DataFrame:
    table = pd.concat(
        [predictions.reset_index(drop=True), heldout_features.reset_index(drop=True)], axis=1
    )
    table["probability_gap"] = (
        table["all_shallow_p_spam"] - table["full_text_p_spam"]
    )
    table["cue_snapshot"] = table.apply(cue_snapshot, axis=1)

    definitions = [
        (
            "shallow_false_positive",
            (table["label"] == "ham")
            & (table["all_shallow_pred"] == "spam")
            & (table["full_text_pred"] == "ham"),
            table["probability_gap"],
        ),
        (
            "shallow_false_negative",
            (table["label"] == "spam")
            & (table["all_shallow_pred"] == "ham")
            & (table["full_text_pred"] == "spam"),
            -table["probability_gap"],
        ),
        (
            "shallow_rescues_full_text_miss",
            (table["label"] == "spam")
            & (table["all_shallow_pred"] == "spam")
            & (table["full_text_pred"] == "ham"),
            table["probability_gap"],
        ),
        (
            "both_models_miss_spam",
            (table["label"] == "spam")
            & (table["all_shallow_pred"] == "ham")
            & (table["full_text_pred"] == "ham"),
            1.0 - table[["all_shallow_p_spam", "full_text_p_spam"]].max(axis=1),
        ),
    ]

    queue_parts = []
    for reason, mask, score in definitions:
        subset = table.loc[mask].copy()
        subset["candidate_reason"] = reason
        subset["priority_score"] = score.loc[mask]
        queue_parts.append(subset.sort_values("priority_score", ascending=False).head(15))

    queue = pd.concat(queue_parts, ignore_index=True)
    queue = queue.sort_values(
        ["candidate_reason", "priority_score"], ascending=[True, False]
    ).reset_index(drop=True)
    queue.insert(0, "queue_rank", np.arange(1, len(queue) + 1))
    columns = [
        "queue_rank",
        "id",
        "label",
        "candidate_reason",
        "priority_score",
        "all_shallow_p_spam",
        "all_shallow_pred",
        "full_text_p_spam",
        "full_text_pred",
        "masked_text_p_spam",
        "masked_text_pred",
        "cue_snapshot",
        "text",
    ]
    return queue[columns]


def load_review_ledger(predictions: pd.DataFrame) -> pd.DataFrame:
    required = ["id", "decision", "confidence", "recommended_action", "review_note"]
    if not REVIEW_LEDGER_PATH.exists():
        return pd.DataFrame(columns=required)

    ledger = pd.read_csv(REVIEW_LEDGER_PATH, keep_default_na=False)
    if list(ledger.columns) != required:
        raise AssertionError(
            f"Review ledger must have columns {required}; found {list(ledger.columns)}"
        )
    if ledger["id"].duplicated().any():
        raise AssertionError("Shortcut review ledger contains duplicate ids")
    if not set(ledger["decision"]).issubset({"include", "exclude"}):
        raise AssertionError("Review decisions must be include or exclude")
    if not set(ledger["confidence"]).issubset({"low", "medium", "high"}):
        raise AssertionError("Review confidence must be low, medium, or high")
    missing_ids = set(ledger["id"]).difference(predictions["id"])
    if missing_ids:
        raise AssertionError(f"Review ledger contains unknown held-out ids: {sorted(missing_ids)}")
    return ledger


def build_findings(
    predictions: pd.DataFrame,
    heldout_features: pd.DataFrame,
    ledger: pd.DataFrame,
) -> pd.DataFrame:
    schema = load_protocol()["suspicious_examples_schema"]
    if ledger.empty:
        return pd.DataFrame(columns=schema)

    evidence = pd.concat(
        [predictions.reset_index(drop=True), heldout_features.reset_index(drop=True)], axis=1
    ).set_index("id")
    rows = []
    included = ledger[ledger["decision"] == "include"].reset_index(drop=True)
    for rank, review in included.iterrows():
        row = evidence.loc[review["id"]]
        rows.append(
            {
                "id": review["id"],
                "split": "heldout",
                "issue_type": "shortcut",
                "rank": rank + 1,
                "confidence": review["confidence"],
                "evidence_1": (
                    f"all_shallow_p_spam={row['all_shallow_p_spam']:.3f};"
                    f"all_shallow_pred={row['all_shallow_pred']};label={row['label']}"
                ),
                "evidence_2": (
                    f"full_text_p_spam={row['full_text_p_spam']:.3f};"
                    f"full_text_pred={row['full_text_pred']};{cue_snapshot(row)}"
                ),
                "recommended_action": review["recommended_action"],
                "short_explanation": review["review_note"],
            }
        )
    return pd.DataFrame(rows, columns=schema)


def plot_metrics(metrics: pd.DataFrame, warning_threshold: float) -> None:
    order = [
        "majority_ham",
        "shape_only",
        "contact_promo_only",
        "all_shallow",
        "row_position_only",
        "all_shallow_plus_position",
        "masked_text",
        "full_text",
    ]
    plot_df = metrics.set_index("condition").loc[order, ["accuracy", "spam_f1"]]
    ax = plot_df.plot(
        kind="bar",
        figsize=(10.5, 5.2),
        color=["#2563EB", "#DC2626"],
        rot=24,
    )
    ax.axhline(
        warning_threshold,
        color="#111827",
        linestyle="--",
        linewidth=1.1,
        label=f"protocol accuracy warning ({warning_threshold:.0%})",
    )
    ax.set_title("Shallow shortcut probes versus the frozen text baseline", loc="left", fontweight="bold")
    ax.set_ylabel("Score")
    ax.set_ylim(0, 1.03)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.18)
    ax.legend(frameon=False, ncol=3)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "shortcut_metrics.png", dpi=180)
    plt.close()


def plot_coefficients(coefficients: pd.DataFrame) -> None:
    subset = coefficients[coefficients["condition"] == "all_shallow"].copy()
    subset = subset.sort_values("standardized_coefficient")
    colors = np.where(subset["standardized_coefficient"] >= 0, "#DC2626", "#2563EB")
    ax = subset.plot.barh(
        x="feature",
        y="standardized_coefficient",
        figsize=(8.4, 5.4),
        color=colors,
        legend=False,
    )
    ax.axvline(0, color="#111827", linewidth=0.8)
    ax.set_title("All-shallow standardized coefficients", loc="left", fontweight="bold")
    ax.set_xlabel("Coefficient toward spam")
    ax.set_ylabel("")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", alpha=0.18)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "shortcut_coefficients.png", dpi=180)
    plt.close()


def plot_cue_prevalence(prevalence: pd.DataFrame) -> None:
    cues = ["currency_count", "has_url", "has_phone", "promo_token_count"]
    subset = prevalence[
        (prevalence["split"] == "heldout") & prevalence["feature"].isin(cues)
    ].pivot(index="feature", columns="label", values="nonzero_rate")
    subset = subset[["ham", "spam"]]
    ax = subset.plot.bar(
        figsize=(8.6, 4.8), color=["#2563EB", "#DC2626"], rot=20
    )
    ax.set_title("Held-out prevalence of contact and promotion cues", loc="left", fontweight="bold")
    ax.set_ylabel("Fraction with non-zero cue")
    ax.set_xlabel("")
    ax.set_ylim(0, 1.0)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.18)
    ax.legend(frameon=False, title="label")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "shortcut_cue_prevalence.png", dpi=180)
    plt.close()


def percentage(value: float) -> str:
    return f"{100 * value:.2f}%"


def write_report(
    metrics: pd.DataFrame,
    coefficients: pd.DataFrame,
    findings: pd.DataFrame,
    ledger: pd.DataFrame,
    warning_threshold: float,
) -> None:
    metric_lookup = metrics.set_index("condition")
    conditions = [
        ("Majority ham", "majority_ham"),
        ("Shape only", "shape_only"),
        ("Contact/promotion only", "contact_promo_only"),
        ("All shallow", "all_shallow"),
        ("Row position only", "row_position_only"),
        ("All shallow + position", "all_shallow_plus_position"),
        ("Masked promotional tokens", "masked_text"),
        ("Frozen full text", "full_text"),
    ]
    table_lines = [
        "| Condition | Accuracy | Spam precision | Spam recall | Spam F1 | Macro-F1 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for label, condition in conditions:
        row = metric_lookup.loc[condition]
        table_lines.append(
            "| "
            + " | ".join(
                [
                    label,
                    percentage(row["accuracy"]),
                    percentage(row["spam_precision"]),
                    percentage(row["spam_recall"]),
                    percentage(row["spam_f1"]),
                    percentage(row["macro_f1"]),
                ]
            )
            + " |"
        )

    top_coefficients = coefficients[coefficients["condition"] == "all_shallow"].nsmallest(
        6, "absolute_rank"
    )
    coefficient_text = ", ".join(
        f"`{row.feature}` ({row.standardized_coefficient:+.3f})"
        for row in top_coefficients.itertuples()
    )

    case_lines = [
        "| ID | Confidence | Evidence pattern |",
        "|---|---|---|",
    ]
    for row in findings.itertuples():
        case_lines.append(
            f"| `{row.id}` | {row.confidence} | {row.short_explanation} |"
        )
    if findings.empty:
        case_lines.append("| — | — | Manual review ledger not yet supplied. |")

    excluded = ledger[ledger["decision"] == "exclude"] if not ledger.empty else ledger
    excluded_lines = []
    for row in excluded.itertuples():
        excluded_lines.append(f"- `{row.id}`: {row.review_note}")
    if not excluded_lines:
        excluded_lines.append("- No rejected candidates were recorded.")

    majority_acc = metric_lookup.loc["majority_ham", "accuracy"]
    shallow = metric_lookup.loc["all_shallow"]
    contact = metric_lookup.loc["contact_promo_only"]
    position = metric_lookup.loc["row_position_only"]
    masked = metric_lookup.loc["masked_text"]
    full = metric_lookup.loc["full_text"]
    report = f"""# Shortcut-Feature Audit

## Scope and Controls

This audit tests whether surface cues explain an excessive share of SMS spam performance. The shallow probes receive only derived numeric features: message shape, digits, currency, URL/phone indicators, promotional-token counts and, in a separate probe, normalized UCI row position. They never receive raw token order. Every learned comparison uses Logistic Regression; numeric probes are standardized, and the `full_text` result is read from the frozen shared held-out predictions rather than retrained.

## Results

{chr(10).join(table_lines)}

The protocol's {warning_threshold:.0%} accuracy warning is not meaningful on its own because the majority-ham classifier already reaches {percentage(majority_acc)} while detecting no spam. The stronger evidence is that contact/promotion cues alone reach {percentage(contact['accuracy'])} accuracy and {percentage(contact['spam_f1'])} spam F1. Combining all shallow cues reaches {percentage(shallow['accuracy'])} accuracy and {percentage(shallow['spam_f1'])} spam F1, close to the frozen full-text model's {percentage(full['accuracy'])} accuracy and {percentage(full['spam_f1'])} spam F1.

Row position alone reaches {percentage(position['accuracy'])} accuracy and {percentage(position['spam_f1'])} spam F1, so corpus order adds no useful spam discrimination. This is evidence against a row-order shortcut.

## Which Cues Matter

The largest absolute standardized coefficients in the all-shallow model are {coefficient_text}. Positive coefficients point toward spam; negative coefficients point toward ham. Because inputs are standardized, their magnitudes are comparable within this fitted probe.

## Promotional-Token Stress Test

Masking the fixed 15-token promotional lexicon gives {percentage(masked['accuracy'])} accuracy and {percentage(masked['spam_f1'])} spam F1, versus {percentage(full['accuracy'])} and {percentage(full['spam_f1'])} for full text. The small change shows that the baseline is not explained by that lexicon alone, although broader contact and promotional structure remains highly predictive.

## Example-Level Findings

{chr(10).join(case_lines)}

These rows are stress cases, not requests to change held-out labels. They show where shallow cues either overwhelm benign context or rescue/miss spam for the wrong reason.

## Rejected Candidates

{chr(10).join(excluded_lines)}

Rejected rows remain in the review ledger so model disagreement is not silently converted into a high-confidence audit claim.

## Interpretation and Limitations

Digits, prices, URLs, telephone numbers and promotional wording are legitimate spam evidence, so their predictive value is not direct leakage. They are shortcuts because they can work without sentence meaning and fail under distribution shift: ordinary price discussions can trigger false positives, while solicitations without familiar numeric markers can be missed. Coefficients describe association, not causation. The held-out labels remain untouched, and possible label-policy cases should be adjudicated jointly with the label-noise audit.

## Reproducible Evidence

- `scripts/audit_shortcuts.py`
- `configs/shortcut_manual_review.csv`
- `results/shortcut/shortcut_metrics.csv`
- `results/shortcut/shortcut_coefficients.csv`
- `results/shortcut/shortcut_predictions.csv`
- `results/shortcut/shortcut_review_queue.csv`
- `results/shortcut/shortcut_findings.csv`
- `results/figures/shortcut_metrics.png`
- `results/figures/shortcut_coefficients.png`
- `results/figures/shortcut_cue_prevalence.png`
"""
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> None:
    ensure_dirs()
    SHORTCUT_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    protocol = load_protocol()
    warning_threshold = float(protocol["shortcut_warning_accuracy"])

    canonical = load_canonical().reset_index(drop=True)
    train = canonical[canonical["split"] == "train"].copy().reset_index(drop=True)
    heldout = canonical[canonical["split"] == "heldout"].copy().reset_index(drop=True)
    if len(train) != 4460 or len(heldout) != 1114:
        raise AssertionError("Canonical split sizes do not match the fixed manifest")

    all_features = shallow_features(canonical).reset_index(drop=True)
    train_features = all_features[canonical["split"] == "train"].reset_index(drop=True)
    heldout_features = all_features[canonical["split"] == "heldout"].reset_index(drop=True)
    frozen_baseline = load_frozen_baseline(heldout)

    metrics, coefficients, predictions = fit_probes(
        train,
        heldout,
        train_features,
        heldout_features,
        frozen_baseline,
        warning_threshold,
    )
    prevalence = feature_prevalence_table(canonical, all_features)
    review_queue = build_review_queue(predictions, heldout_features)
    ledger = load_review_ledger(predictions)
    findings = build_findings(predictions, heldout_features, ledger)

    metrics.to_csv(SHORTCUT_RESULTS_DIR / "shortcut_metrics.csv", index=False)
    coefficients.to_csv(SHORTCUT_RESULTS_DIR / "shortcut_coefficients.csv", index=False)
    predictions.to_csv(SHORTCUT_RESULTS_DIR / "shortcut_predictions.csv", index=False)
    prevalence.to_csv(SHORTCUT_RESULTS_DIR / "shortcut_feature_prevalence.csv", index=False)
    review_queue.to_csv(SHORTCUT_RESULTS_DIR / "shortcut_review_queue.csv", index=False)
    findings.to_csv(SHORTCUT_RESULTS_DIR / "shortcut_findings.csv", index=False)

    plot_metrics(metrics, warning_threshold)
    plot_coefficients(coefficients)
    plot_cue_prevalence(prevalence)
    write_report(metrics, coefficients, findings, ledger, warning_threshold)

    metric_lookup = metrics.set_index("condition")
    all_shallow = metric_lookup.loc["all_shallow"]
    full_text = metric_lookup.loc["full_text"]
    write_json(
        SHORTCUT_RESULTS_DIR / "shortcut_summary.json",
        {
            "source_script": "scripts/audit_shortcuts.py",
            "method_version": "shortcut-audit-v1.0",
            "protocol_version": protocol["version"],
            "random_seed": SEED,
            "shared_baseline_retrained": False,
            "warning_threshold": warning_threshold,
            "majority_accuracy": float(metric_lookup.loc["majority_ham", "accuracy"]),
            "all_shallow_accuracy": float(all_shallow["accuracy"]),
            "all_shallow_spam_f1": float(all_shallow["spam_f1"]),
            "full_text_accuracy": float(full_text["accuracy"]),
            "full_text_spam_f1": float(full_text["spam_f1"]),
            "review_queue_rows": int(len(review_queue)),
            "manual_review_rows": int(len(ledger)),
            "included_findings": int(len(findings)),
            "rejected_candidates": int((ledger["decision"] == "exclude").sum())
            if not ledger.empty
            else 0,
            "report": "audit/shortcut_features.md",
        },
    )

    print(metrics[["condition", "accuracy", "spam_recall", "spam_f1", "macro_f1"]].to_string(index=False))
    print(f"Review queue rows: {len(review_queue)}")
    print(f"Manual findings: {len(findings)}")
    if ledger.empty:
        print(f"Manual ledger not found yet: {REVIEW_LEDGER_PATH}")


if __name__ == "__main__":
    main()
