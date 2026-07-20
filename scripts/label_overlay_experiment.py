"""Measure what the training-label overlay does, and analyse held-out errors."""

from __future__ import annotations

import json

import pandas as pd

from common import (
    RESULTS_DIR,
    classification_metrics,
    load_canonical,
    write_json,
)
from train_baseline import SEED, word_pipeline


def main() -> None:
    canonical = load_canonical()
    overlay = pd.read_csv(RESULTS_DIR / "training_label_overlay.csv", keep_default_na=False)

    train = canonical[canonical["split"] == "train"].reset_index(drop=True)
    heldout = canonical[canonical["split"] == "heldout"].reset_index(drop=True)

    corrected = train.copy()
    mapping = dict(zip(overlay["id"], overlay["overlay_label"]))
    corrected["label"] = corrected.apply(
        lambda row: mapping.get(row["id"], row["label"]), axis=1
    )
    changed = int((corrected["label"] != train["label"]).sum())
    assert changed == len(overlay), "overlay did not apply cleanly"

    baseline_model = word_pipeline().fit(train["text"], train["label"])
    overlay_model = word_pipeline().fit(corrected["text"], corrected["label"])

    baseline_pred = baseline_model.predict(heldout["text"])
    overlay_pred = overlay_model.predict(heldout["text"])

    baseline_metrics = classification_metrics(heldout["label"], baseline_pred)
    overlay_metrics = classification_metrics(heldout["label"], overlay_pred)
    flipped = int((baseline_pred != overlay_pred).sum())

    errors = heldout[baseline_pred != heldout["label"]].copy()
    errors["word_pred"] = baseline_pred[baseline_pred != heldout["label"]]

    review = json.loads((RESULTS_DIR.parent / "configs" / "manual_review.json").read_text(encoding="utf-8"))
    flagged_label_error = {entry["id"] for entry in review["label_errors"]}
    flagged_ambiguous = {entry["id"] for entry in review["ambiguous"]}
    errors["audit_status"] = errors["id"].map(
        lambda row_id: "likely_label_error"
        if row_id in flagged_label_error
        else ("ambiguous_policy_case" if row_id in flagged_ambiguous else "model_error")
    )

    payload = {
        "seed": SEED,
        "overlay_rows_applied": changed,
        "heldout_baseline": baseline_metrics,
        "heldout_with_overlay": overlay_metrics,
        "heldout_predictions_changed": flipped,
        "heldout_baseline_errors": int(len(errors)),
        "heldout_error_breakdown": errors["audit_status"].value_counts().to_dict(),
    }
    write_json(RESULTS_DIR / "label_overlay_experiment.json", payload)
    errors[["id", "label", "word_pred", "audit_status", "text"]].to_csv(
        RESULTS_DIR / "heldout_baseline_errors.csv", index=False
    )

    print(f"overlay rows applied      : {changed}")
    print(f"heldout accuracy baseline : {baseline_metrics['accuracy']:.6f}")
    print(f"heldout accuracy overlay  : {overlay_metrics['accuracy']:.6f}")
    print(f"spam recall baseline      : {baseline_metrics['spam_recall']:.6f}")
    print(f"spam recall overlay       : {overlay_metrics['spam_recall']:.6f}")
    print(f"heldout predictions changed: {flipped}")
    print(f"heldout baseline errors   : {len(errors)}")
    print(errors["audit_status"].value_counts().to_string())


if __name__ == "__main__":
    main()
