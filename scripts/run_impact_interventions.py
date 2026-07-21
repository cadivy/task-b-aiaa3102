"""Compare dataset-level interventions for the Topic B audit.

This script keeps canonical data immutable. Each intervention is applied as an
experimental training view or evaluation view, then compared with the same
word TF-IDF logistic-regression baseline used by the shared project scripts.
"""

from __future__ import annotations

import json
import os
import re
from collections import defaultdict, deque
from pathlib import Path

import pandas as pd

from common import classification_metrics, load_canonical, write_json
from train_baseline import word_pipeline


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
IMPACT_DIR = RESULTS_DIR / "impact"
REPORT_PATH = ROOT / "impact_analysis.md"
DUP_DIR = RESULTS_DIR / "duplicate"
LEAKAGE_DIR = RESULTS_DIR / "leakage"
CANONICAL_PATH = DATA_DIR / "canonical_sms.csv"
MANUAL_REVIEW_PATH = ROOT / "configs" / "manual_review.json"
SEED = 42

PROMO_TOKENS = (
    "free",
    "win",
    "winner",
    "prize",
    "claim",
    "urgent",
    "call",
    "reply",
    "cash",
    "award",
    "bonus",
    "offer",
    "txt",
    "text",
    "stop",
)
URL_RE = re.compile(r"(?:https?://|www\.|\b\w+\.(?:com|co\.uk|net|org)\b)", re.I)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{6,}\d)(?!\d)")
PROMO_PATTERN = re.compile(
    r"\b(?:" + "|".join(re.escape(token) for token in PROMO_TOKENS) + r")\b",
    re.I,
)
CURRENCY_PATTERN = re.compile(
    r"(?:[$]|\b(?:gbp|ukp|pounds?|dollars?|pence|ppm|p/min|p per min|per min)\b)",
    re.I,
)
DIGIT_PATTERN = re.compile(r"\b\d[\d\s()./-]{1,}\b")


def split_ids(value: object) -> list[str]:
    if pd.isna(value):
        return []
    text = str(value).strip()
    if not text:
        return []
    return [item for item in text.split("|") if item]


def write_csv_atomic(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temp_path, index=False)
    try:
        os.replace(temp_path, path)
    except PermissionError as exc:
        raise PermissionError(
            f"Cannot replace {path}. Close the file if it is open in Excel/WPS/preview, then rerun this script."
        ) from exc


def metric_record(
    condition: str,
    intervention_family: str,
    train: pd.DataFrame,
    heldout: pd.DataFrame,
    notes: str,
    train_text_col: str = "text",
    heldout_text_col: str = "text",
) -> dict[str, object]:
    model = word_pipeline().fit(train[train_text_col], train["label"])
    prediction = model.predict(heldout[heldout_text_col])
    values = classification_metrics(heldout["label"], prediction)
    tn, fp = values["confusion_matrix_ham_spam"][0]
    fn, tp = values["confusion_matrix_ham_spam"][1]
    return {
        "condition": condition,
        "intervention_family": intervention_family,
        "evaluation_scope": "heldout",
        "random_seed": SEED,
        "train_rows": int(len(train)),
        "heldout_rows": int(len(heldout)),
        "train_spam_rows": int((train["label"] == "spam").sum()),
        "heldout_spam_rows": int((heldout["label"] == "spam").sum()),
        "accuracy": values["accuracy"],
        "spam_precision": values["spam_precision"],
        "spam_recall": values["spam_recall"],
        "spam_f1": values["spam_f1"],
        "macro_f1": values["macro_f1"],
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
        "notes": notes,
    }


def connected_components(edges: list[tuple[str, str]]) -> list[set[str]]:
    graph: dict[str, set[str]] = defaultdict(set)
    for left, right in edges:
        graph[left].add(right)
        graph[right].add(left)

    seen: set[str] = set()
    components: list[set[str]] = []
    for node in sorted(graph):
        if node in seen:
            continue
        queue = deque([node])
        seen.add(node)
        component: set[str] = set()
        while queue:
            current = queue.popleft()
            component.add(current)
            for nxt in sorted(graph[current]):
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        components.append(component)
    return components


def duplicate_dedup_remove_ids(train: pd.DataFrame) -> set[str]:
    train_ids = set(train["id"])
    row_order = train.set_index("id")["uci_row_number"].to_dict()
    edges: list[tuple[str, str]] = []

    exact_path = DUP_DIR / "exact_duplicate_members.csv"
    if exact_path.exists():
        exact = pd.read_csv(exact_path, keep_default_na=False)
        train_exact = exact[exact["split"] == "train"]
        for _, group in train_exact.groupby("cluster_id", sort=True):
            ids = sorted(group["id"], key=lambda item: (row_order.get(item, 10**9), item))
            if len(ids) > 1:
                root = ids[0]
                edges.extend((root, other) for other in ids[1:])

    decisions_path = DUP_DIR / "near_duplicate_manual_review_decisions.csv"
    if decisions_path.exists():
        decisions = pd.read_csv(decisions_path, keep_default_na=False)
        accepted = decisions[decisions["review_decision"] == "accepted"]
        for row in accepted.sort_values(["pair_key", "id_a", "id_b"]).itertuples():
            if row.id_a in train_ids and row.id_b in train_ids:
                edges.append((row.id_a, row.id_b))

    remove_ids: set[str] = set()
    for component in connected_components(edges):
        train_component = component.intersection(train_ids)
        if len(train_component) <= 1:
            continue
        keep = min(train_component, key=lambda item: (row_order.get(item, 10**9), item))
        remove_ids.update(train_component - {keep})
    return remove_ids


def leakage_train_partner_ids() -> set[str]:
    path = LEAKAGE_DIR / "leakage_heldout_rows.csv"
    if not path.exists():
        return set()
    leakage = pd.read_csv(path, keep_default_na=False)
    ids: set[str] = set()
    for value in leakage["train_partner_ids"]:
        ids.update(split_ids(value))
    return {item for item in ids if item.startswith("T")}


def leakage_heldout_ids() -> set[str]:
    path = LEAKAGE_DIR / "leakage_heldout_rows.csv"
    if not path.exists():
        return set()
    leakage = pd.read_csv(path, keep_default_na=False)
    return set(leakage["heldout_id"])


def load_manual_review() -> dict[str, object]:
    if MANUAL_REVIEW_PATH.exists():
        return json.loads(MANUAL_REVIEW_PATH.read_text(encoding="utf-8"))
    return {}


def label_overlay_mapping() -> dict[str, str]:
    path = RESULTS_DIR / "training_label_overlay.csv"
    if path.exists():
        overlay = pd.read_csv(path, keep_default_na=False)
        return dict(zip(overlay["id"], overlay["overlay_label"]))

    payload = load_manual_review()
    mapping: dict[str, str] = {}
    for entry in payload.get("label_errors", []):
        row_id = str(entry.get("id", ""))
        proposed_label = str(entry.get("proposed_label", ""))
        if row_id.startswith("T") and proposed_label in {"ham", "spam"}:
            mapping[row_id] = proposed_label
    return mapping


def apply_label_overlay(train: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    output = train.copy()
    output["label"] = output.apply(lambda row: mapping.get(row["id"], row["label"]), axis=1)
    return output


def ambiguous_train_ids() -> set[str]:
    payload = load_manual_review()
    return {
        str(entry.get("id", ""))
        for entry in payload.get("ambiguous", [])
        if str(entry.get("id", "")).startswith("T")
    }


def mask_shortcut_cues(text: object) -> str:
    output = str(text)
    output = URL_RE.sub(" URL_TOKEN ", output)
    output = PHONE_RE.sub(" PHONE_TOKEN ", output)
    output = CURRENCY_PATTERN.sub(" MONEY_TOKEN ", output)
    output = DIGIT_PATTERN.sub(" NUMBER_TOKEN ", output)
    output = PROMO_PATTERN.sub(" PROMO_TOKEN ", output)
    return " ".join(output.split())


def add_text_masks(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    output["masked_text"] = output["text"].map(mask_shortcut_cues)
    return output


def pct(value: float) -> str:
    return f"{100 * value:.2f}%"


def write_report(metrics: pd.DataFrame, summary: dict[str, object]) -> None:
    display = metrics.copy()
    for column in ["accuracy", "spam_precision", "spam_recall", "spam_f1", "macro_f1"]:
        display[column] = display[column].map(pct)

    by_condition = metrics.set_index("condition")
    baseline = by_condition.loc["baseline_public_labels"]
    leakage_clean = by_condition.loc["baseline_excluding_leaked_heldout"]
    leakage_remove = by_condition.loc["remove_leakage_train_partners"]
    overlay = by_condition.loc["training_label_overlay"]
    ambiguous = by_condition.loc["exclude_ambiguous_training_rows"]
    shortcut = by_condition.loc["shortcut_cue_masking"]
    dedup = by_condition.loc["duplicate_deduplication"]
    combined = by_condition.loc["combined_training_view"]
    adjudication_path = RESULTS_DIR / "intervention_ambiguity_eval.json"
    adjudication = (
        json.loads(adjudication_path.read_text(encoding="utf-8"))
        if adjudication_path.exists()
        else None
    )

    lines = [
        "# Impact Analysis",
        "",
        "## Scope",
        "",
        "The unified experiment compares five data-intervention families: leakage handling, training-label overlay, ambiguous-row handling, shortcut masking, and duplicate de-duplication. A separate adjudication-aware evaluation is produced by `scripts/intervention_ambiguity_eval.py`. Canonical data and held-out labels are never edited.",
        "",
        "The impact model is the shared word TF-IDF + Logistic Regression baseline from `scripts/train_baseline.py` (`word_pipeline`: unigram/bigram TF-IDF, `C=4.0`, `solver='liblinear'`, `random_state=42`). Each condition retrains the same pipeline on the relevant intervention view.",
        "",
        "## Intervention Results",
        "",
        "| Condition | Family | Train rows | Held-out rows | Accuracy | Spam precision | Spam recall | Spam F1 | Macro-F1 | Notes |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in display.itertuples():
        lines.append(
            f"| `{row.condition}` | {row.intervention_family} | {row.train_rows} | {row.heldout_rows} | "
            f"{row.accuracy} | {row.spam_precision} | {row.spam_recall} | {row.spam_f1} | {row.macro_f1} | {row.notes} |"
        )
    if adjudication is not None:
        final_adjudication = adjudication["conditions"][
            "exclude_ambiguous_and_suspected_label_errors"
        ]
        lines.append(
            "| `adjudication_aware_evaluation` | adjudication_aware_evaluation | 4460 | "
            f"{final_adjudication['n']} | {pct(final_adjudication['accuracy'])} | "
            f"{pct(final_adjudication['spam_precision'])} | {pct(final_adjudication['spam_recall'])} | "
            f"{pct(final_adjudication['spam_f1'])} | {pct(final_adjudication['macro_f1'])} | "
            "Frozen baseline after excluding two policy-ambiguous and two suspected-label-error held-out rows. |"
        )

    lines.extend(
        [
            "",
            "## Conclusions",
            "",
            f"The public-label reference reaches {pct(baseline['accuracy'])} accuracy, {pct(baseline['spam_recall'])} spam recall, and {pct(baseline['spam_f1'])} spam F1 on all held-out rows. This is the comparison anchor: every intervention uses the same word TF-IDF + Logistic Regression pipeline, so metric changes mainly reflect the changed data view rather than a changed model family.",
            "",
            "### Leakage Handling",
            "",
            f"Leakage-aware evaluation removes {summary['leaked_heldout_rows']} held-out rows that have exact or reviewed near-duplicate partners in training, leaving {int(leakage_clean['heldout_rows'])} held-out rows and {pct(leakage_clean['accuracy'])} accuracy. This view asks how much of the headline score depends on examples that are partly recoverable from training. The drop in spam F1 from {pct(baseline['spam_f1'])} to {pct(leakage_clean['spam_f1'])} suggests that leaked held-out rows make the original evaluation look cleaner than a fully independent held-out set would.",
            "",
            f"The training-side leakage intervention removes {summary['leakage_train_partner_rows_removed']} training partners and retrains on {int(leakage_remove['train_rows'])} rows, reaching {pct(leakage_remove['accuracy'])} accuracy and {pct(leakage_remove['spam_f1'])} spam F1. This does not edit held-out labels; it estimates whether the model was benefiting from memorized or near-memorized training rows. The result shows that leakage is a data-quality risk for performance interpretation even when aggregate accuracy remains high.",
            "",
            "### Label Overlay",
            "",
            f"The training-label overlay applies {summary['label_overlay_rows']} training-only relabel proposals and reaches {pct(overlay['accuracy'])} accuracy with {pct(overlay['spam_f1'])} spam F1. The limited metric movement means the baseline is not highly sensitive to the small reviewed label-error set, but the intervention still matters for audit validity: mislabeled training rows can distort feature weights, error analysis, and any qualitative claim about what the classifier learned.",
            "",
            "### Ambiguous Rows",
            "",
            f"Ambiguous-row handling excludes {summary['ambiguous_training_rows_excluded']} policy-ambiguous training rows and retrains on {int(ambiguous['train_rows'])} rows, again reaching {pct(ambiguous['accuracy'])} accuracy and {pct(ambiguous['spam_f1'])} spam F1. The stable score should not be read as ambiguity being irrelevant. Instead, it means the ambiguous set is small enough not to move this particular aggregate metric, while still lowering confidence in row-level adjudication and in any strict claim that the public label policy is perfectly consistent.",
            "",
            "### Adjudication-Aware Evaluation",
            "",
            (
                f"The separate frozen-model evaluation removes two policy-ambiguous held-out rows and two suspected held-out label errors, leaving {adjudication['conditions']['exclude_ambiguous_and_suspected_label_errors']['n']} rows. Accuracy becomes {pct(adjudication['conditions']['exclude_ambiguous_and_suspected_label_errors']['accuracy'])} and spam recall becomes {pct(adjudication['conditions']['exclude_ambiguous_and_suspected_label_errors']['spam_recall'])}. This increase must be interpreted cautiously: the two suspected label errors were retrieved because model signals oppose their labels, so removing them is partly circular. The ambiguity-only step is more informative because those rows were selected by policy reading rather than by model failure."
                if adjudication is not None
                else "Run `scripts/intervention_ambiguity_eval.py` to produce the adjudication-aware evaluation."
            ),
            "",
            "### Shortcut Masking",
            "",
            f"Shortcut cue masking replaces URLs, phone-like strings, money/rate markers, digit runs, and fixed promotional words before both training and evaluation. It reaches {pct(shortcut['accuracy'])} accuracy and {pct(shortcut['spam_f1'])} spam F1. The model still performs well, so the task is not solved only by one obvious token family; however, the lower precision and F1 show that shallow artifacts are part of the learned signal. This affects data-quality interpretation because strong shortcut cues can inflate apparent generalization while hiding weaker semantic robustness.",
            "",
            "### Duplicate De-Duplication",
            "",
            f"Duplicate de-duplication removes {summary['duplicate_training_rows_removed']} repeated training rows by keeping the earliest training member in each exact or accepted train-train near-duplicate component. The retrained model uses {int(dedup['train_rows'])} rows and reaches {pct(dedup['accuracy'])} accuracy with {pct(dedup['spam_f1'])} spam F1. This intervention tests whether repeated messages overweight common templates. The small but visible movement means duplicates are not the sole driver of performance, but they do affect the effective training distribution and can make certain message templates count more than independent examples should.",
            "",
            "### Combined View",
            "",
            f"The combined training view removes leakage partners, removes duplicate repeats, excludes ambiguous training rows, applies remaining training-label overlay entries, and masks shortcut cues. It trains on {int(combined['train_rows'])} rows and reaches {pct(combined['accuracy'])} accuracy with {pct(combined['spam_f1'])} spam F1. This is a conservative stress test rather than a proposed replacement dataset. Its lower score summarizes the cumulative impact of data-quality issues: each issue is individually modest, but together they reduce confidence that the original headline metric fully represents clean, independent generalization.",
            "",
            "## Reproducible Artifacts",
            "",
            "- `scripts/run_impact_interventions.py`: builds all intervention views and rewrites this report.",
            "- `results/impact/intervention_metrics.csv`: one row per condition with metrics and confusion counts.",
            "- `results/impact/intervention_summary.json`: row counts, seed, and source files used by the interventions.",
            "- `scripts/intervention_ambiguity_eval.py` and `results/intervention_ambiguity_eval.json`: adjudication-aware frozen-model evaluation.",
            "- `impact_analysis.md`: narrative interpretation of the intervention comparison.",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    IMPACT_DIR.mkdir(parents=True, exist_ok=True)

    canonical = load_canonical().reset_index(drop=True)
    train = canonical[canonical["split"] == "train"].copy().reset_index(drop=True)
    heldout = canonical[canonical["split"] == "heldout"].copy().reset_index(drop=True)

    rows: list[dict[str, object]] = []
    rows.append(metric_record("baseline_public_labels", "baseline", train, heldout, "Original public training labels evaluated on all held-out rows."))

    leaked_heldout = leakage_heldout_ids()
    clean_heldout = heldout[~heldout["id"].isin(leaked_heldout)].reset_index(drop=True)
    rows.append(metric_record("baseline_excluding_leaked_heldout", "leakage_aware_evaluation", train, clean_heldout, "Evaluation sensitivity after excluding held-out rows with exact or reviewed near train partners."))

    leakage_train_ids = leakage_train_partner_ids()
    leakage_removed_train = train[~train["id"].isin(leakage_train_ids)].reset_index(drop=True)
    rows.append(metric_record("remove_leakage_train_partners", "leakage_removal", leakage_removed_train, heldout, "Retrain after removing training rows that are exact or reviewed near partners of held-out rows."))

    label_mapping = label_overlay_mapping()
    overlay_train = apply_label_overlay(train, label_mapping)
    rows.append(metric_record("training_label_overlay", "label_overlay", overlay_train, heldout, "Apply training-only label-error overlay; held-out labels remain unchanged."))

    ambiguous_ids = ambiguous_train_ids()
    no_ambiguous_train = train[~train["id"].isin(ambiguous_ids)].reset_index(drop=True)
    rows.append(metric_record("exclude_ambiguous_training_rows", "ambiguous_row_handling", no_ambiguous_train, heldout, "Retrain after excluding training rows adjudicated as ambiguous policy cases."))

    masked_train = add_text_masks(train)
    masked_heldout = add_text_masks(heldout)
    rows.append(metric_record("shortcut_cue_masking", "shortcut_masking", masked_train, masked_heldout, "Replace URLs, phone-like strings, money/rate markers, digit runs, and promotional lexicon before training and evaluation.", train_text_col="masked_text", heldout_text_col="masked_text"))

    duplicate_remove_ids = duplicate_dedup_remove_ids(train)
    dedup_train = train[~train["id"].isin(duplicate_remove_ids)].reset_index(drop=True)
    rows.append(metric_record("duplicate_deduplication", "duplicate_deduplication", dedup_train, heldout, "Keep the earliest training row in each exact or reviewed train-train near-duplicate component."))

    combined_remove = leakage_train_ids | ambiguous_ids | duplicate_remove_ids
    combined_train = train[~train["id"].isin(combined_remove)].reset_index(drop=True)
    combined_train = apply_label_overlay(combined_train, label_mapping)
    combined_train = add_text_masks(combined_train)
    combined_heldout = add_text_masks(heldout)
    rows.append(metric_record("combined_training_view", "combined", combined_train, combined_heldout, "Apply leakage-partner removal, duplicate de-duplication, ambiguous-row exclusion, remaining label overlay, and shortcut cue masking.", train_text_col="masked_text", heldout_text_col="masked_text"))

    metrics = pd.DataFrame(rows)
    write_csv_atomic(metrics, IMPACT_DIR / "intervention_metrics.csv")

    summary = {
        "source_script": "scripts/run_impact_interventions.py",
        "impact_model": "word TF-IDF + Logistic Regression from scripts/train_baseline.py::word_pipeline",
        "random_seed": SEED,
        "canonical_rows": int(len(canonical)),
        "train_rows": int(len(train)),
        "heldout_rows": int(len(heldout)),
        "source_files": {
            "canonical": "data/canonical_sms.csv",
            "duplicates_exact": "results/duplicate/exact_duplicate_members.csv",
            "duplicates_near_review": "results/duplicate/near_duplicate_manual_review_decisions.csv",
            "leakage": "results/leakage/leakage_heldout_rows.csv",
            "label_overlay": "results/training_label_overlay.csv if present, otherwise configs/manual_review.json",
            "manual_review": str(MANUAL_REVIEW_PATH.relative_to(ROOT)) if MANUAL_REVIEW_PATH.exists() else "missing",
        },
        "leaked_heldout_rows": int(len(leaked_heldout)),
        "leakage_train_partner_rows_removed": int(len(leakage_train_ids)),
        "label_overlay_rows": int((overlay_train["label"] != train["label"]).sum()),
        "ambiguous_training_rows_excluded": int(len(ambiguous_ids)),
        "duplicate_training_rows_removed": int(len(duplicate_remove_ids)),
        "combined_training_rows_removed_before_overlay": int(len(combined_remove)),
        "outputs": ["results/impact/intervention_metrics.csv", "results/impact/intervention_summary.json", "impact_analysis.md"],
    }
    write_json(IMPACT_DIR / "intervention_summary.json", summary)
    write_report(metrics, summary)

    columns = ["condition", "train_rows", "heldout_rows", "accuracy", "spam_recall", "spam_f1"]
    print(metrics[columns].to_string(index=False))


if __name__ == "__main__":
    main()
