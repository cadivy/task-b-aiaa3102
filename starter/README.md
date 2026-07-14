# Topic B Starter: Dataset Forensics and Label Audit

This package intentionally contains no analysis or validation code. It gives the public data source, fixed
split manifest, audit vocabulary, and submission interface for Topic B. You are expected to download the data,
build your own local working files, and implement the audit yourself.

## Public Data Source

Use the public UCI SMS Spam Collection:

```text
https://archive.ics.uci.edu/dataset/228/sms+spam+collection
https://archive.ics.uci.edu/ml/machine-learning-databases/00228/smsspamcollection.zip
```

The raw file `SMSSpamCollection` is tab-separated with no header:

```text
label<TAB>message_text
```

Use a 1-based `uci_row_number` matching the raw file line number.

## Fixed Split

Use `data/split_manifest.csv` to assign each UCI row to a stable course id and split. Do not regenerate the
split.

The canonical working table you create should contain at least:

```text
id,split,uci_row_number,text,label
```

Labels should remain the public UCI values `ham` and `spam`.

## Audit Protocol

`configs/audit_protocol.json` defines the issue types, confidence values, and submission columns expected by
the course. The protocol is a format contract, not a hidden answer key.

Your `suspicious_examples.csv` should use:

```text
id,split,issue_type,rank,confidence,evidence_1,evidence_2,recommended_action,short_explanation
```

The sample file in `examples/` is a format example only.

## Expected Student Code

Create your own scripts or notebooks for:

- downloading and parsing the public UCI corpus;
- joining it with `data/split_manifest.csv`;
- implementing baselines, dataset profiles, duplicate searches, nearest-neighbor probes, and shortcut audits;
- producing `suspicious_examples.csv`, `adjudication_memo.csv`, and impact analyses.

Do not edit the public SMS labels directly. If you test relabeling or filtering, represent it as an
experimental overlay and explain the impact.
