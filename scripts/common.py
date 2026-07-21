"""Shared paths, text normalization, features, and evaluation helpers."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "raw"
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
MODELS_DIR = ROOT / "models"
AUDIT_DIR = ROOT / "audit"

CANONICAL_PATH = DATA_DIR / "canonical_sms.csv"
TRAIN_PATH = DATA_DIR / "train.csv"
HELDOUT_PATH = DATA_DIR / "heldout.csv"
MANIFEST_PATH = ROOT / "starter" / "data" / "split_manifest.csv"
PROTOCOL_PATH = ROOT / "starter" / "configs" / "audit_protocol.json"

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
CURRENCY_RE = re.compile(r"[$£€]|\b(?:gbp|pounds?|dollars?|pence)\b", re.I)
TOKEN_RE = re.compile(r"\b\w+\b", re.UNICODE)


def ensure_dirs() -> None:
    for path in (RAW_DIR, DATA_DIR, RESULTS_DIR, FIGURES_DIR, MODELS_DIR, AUDIT_DIR):
        path.mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_text(text: str) -> str:
    """Public exact-duplicate rule: lowercase plus whitespace collapse."""
    return " ".join(str(text).lower().split())


def load_canonical() -> pd.DataFrame:
    if not CANONICAL_PATH.exists():
        raise FileNotFoundError(
            f"Canonical table not found: {CANONICAL_PATH}. Run build_dataset.py first."
        )
    return pd.read_csv(CANONICAL_PATH, keep_default_na=False)


def load_protocol() -> dict:
    return json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def shallow_features(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, float]] = []
    max_row = max(float(df["uci_row_number"].max()), 1.0)
    promo_pattern = re.compile(
        r"\b(?:" + "|".join(re.escape(token) for token in PROMO_TOKENS) + r")\b",
        re.I,
    )

    for _, row in df.iterrows():
        text = str(row["text"])
        tokens = TOKEN_RE.findall(text)
        letters = [char for char in text if char.isalpha()]
        uppercase = sum(char.isupper() for char in letters)
        digits = sum(char.isdigit() for char in text)
        token_count = len(tokens)
        rows.append(
            {
                "char_count": float(len(text)),
                "token_count": float(token_count),
                "avg_token_length": float(
                    np.mean([len(token) for token in tokens]) if tokens else 0.0
                ),
                "digit_count": float(digits),
                "digit_ratio": float(digits / max(len(text), 1)),
                "uppercase_ratio": float(uppercase / max(len(letters), 1)),
                "exclamation_count": float(text.count("!")),
                "currency_count": float(len(CURRENCY_RE.findall(text))),
                "has_url": float(bool(URL_RE.search(text))),
                "has_phone": float(bool(PHONE_RE.search(text))),
                "promo_token_count": float(len(promo_pattern.findall(text))),
                "row_position": float(row["uci_row_number"]) / max_row,
            }
        )
    return pd.DataFrame(rows, index=df.index)


def mask_promotional_tokens(text: str) -> str:
    pattern = re.compile(
        r"\b(?:" + "|".join(re.escape(token) for token in PROMO_TOKENS) + r")\b",
        re.I,
    )
    return pattern.sub(" PROMO_TOKEN ", str(text))


def classification_metrics(y_true, y_pred) -> dict[str, float | int | list[list[int]]]:
    return {
        "n": int(len(y_true)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "spam_precision": float(
            precision_score(y_true, y_pred, pos_label="spam", zero_division=0)
        ),
        "spam_recall": float(
            recall_score(y_true, y_pred, pos_label="spam", zero_division=0)
        ),
        "spam_f1": float(f1_score(y_true, y_pred, pos_label="spam", zero_division=0)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "confusion_matrix_ham_spam": confusion_matrix(
            y_true, y_pred, labels=["ham", "spam"]
        ).tolist(),
    }
