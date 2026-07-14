"""Build the canonical working table using the fixed course manifest."""

from __future__ import annotations

import pandas as pd

from common import (
    CANONICAL_PATH,
    DATA_DIR,
    HELDOUT_PATH,
    MANIFEST_PATH,
    RAW_DIR,
    RESULTS_DIR,
    TRAIN_PATH,
    ensure_dirs,
    normalize_text,
    sha256_file,
    write_json,
)


RAW_TEXT_PATH = RAW_DIR / "SMSSpamCollection"


def decode_raw(raw: bytes) -> tuple[str, str]:
    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise AssertionError("Unable to decode raw corpus")


def main() -> None:
    ensure_dirs()
    if not RAW_TEXT_PATH.exists():
        raise FileNotFoundError("Run scripts/download_data.py first")

    decoded, encoding = decode_raw(RAW_TEXT_PATH.read_bytes())
    records = []
    for row_number, line in enumerate(decoded.splitlines(), start=1):
        if "\t" not in line:
            raise AssertionError(f"Raw row {row_number} does not contain a tab")
        label, text = line.split("\t", 1)
        records.append(
            {"uci_row_number": row_number, "text": text, "label": label}
        )
    raw_df = pd.DataFrame(records)
    manifest = pd.read_csv(MANIFEST_PATH)

    assert len(raw_df) == 5574
    assert len(manifest) == 5574
    assert raw_df["uci_row_number"].is_unique
    assert manifest["uci_row_number"].is_unique
    assert manifest["id"].is_unique

    merged = manifest.merge(
        raw_df,
        on="uci_row_number",
        how="left",
        validate="one_to_one",
        indicator=True,
    )
    assert (merged["_merge"] == "both").all()
    merged = merged.drop(columns="_merge")
    merged = merged[["id", "split", "uci_row_number", "text", "label"]]

    assertions = {
        "total_rows": int(len(merged)),
        "train_rows": int((merged["split"] == "train").sum()),
        "heldout_rows": int((merged["split"] == "heldout").sum()),
        "unique_ids": int(merged["id"].nunique()),
        "unique_row_numbers": int(merged["uci_row_number"].nunique()),
        "empty_text_rows": int((merged["text"].str.len() == 0).sum()),
        "labels": sorted(merged["label"].unique().tolist()),
        "splits": sorted(merged["split"].unique().tolist()),
        "train_prefix_errors": int(
            ((merged["split"] == "train") & ~merged["id"].str.startswith("T")).sum()
        ),
        "heldout_prefix_errors": int(
            ((merged["split"] == "heldout") & ~merged["id"].str.startswith("H")).sum()
        ),
        "normalized_unique_texts": int(
            merged["text"].map(normalize_text).nunique()
        ),
        "raw_sha256": sha256_file(RAW_TEXT_PATH),
        "decoded_encoding": encoding,
    }

    assert assertions["total_rows"] == 5574
    assert assertions["train_rows"] == 4460
    assert assertions["heldout_rows"] == 1114
    assert assertions["unique_ids"] == 5574
    assert assertions["unique_row_numbers"] == 5574
    assert assertions["empty_text_rows"] == 0
    assert assertions["labels"] == ["ham", "spam"]
    assert assertions["splits"] == ["heldout", "train"]
    assert assertions["train_prefix_errors"] == 0
    assert assertions["heldout_prefix_errors"] == 0

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    merged.to_csv(CANONICAL_PATH, index=False)
    merged[merged["split"] == "train"].to_csv(TRAIN_PATH, index=False)
    merged[merged["split"] == "heldout"].to_csv(HELDOUT_PATH, index=False)
    write_json(RESULTS_DIR / "data_validation.json", assertions)

    print(f"Canonical rows: {len(merged)}")
    print(f"Train / heldout: {assertions['train_rows']} / {assertions['heldout_rows']}")
    print(f"Normalized unique texts: {assertions['normalized_unique_texts']}")


if __name__ == "__main__":
    main()
