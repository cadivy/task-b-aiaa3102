# Data Dictionary

Topic B uses the public UCI SMS Spam Collection. The starter does not ship the raw messages. Download the UCI
archive yourself and align it with `split_manifest.csv` by 1-based row number.

## Files

- `split_manifest.csv`: maps each public UCI raw row to a stable course id and split.

## Canonical Working Columns

After downloading the public corpus, create a local working table with at least these columns:

| Column | Type | Description |
|---|---|---|
| `id` | string | Stable course identifier from `split_manifest.csv`. Training ids start with `T`; held-out ids start with `H`. |
| `split` | string | `train` or `heldout`, from `split_manifest.csv`. |
| `uci_row_number` | integer | 1-based line number in the raw UCI `SMSSpamCollection` file. |
| `text` | string | SMS message text from the public UCI corpus. |
| `label` | string | Public UCI class label: `ham` or `spam`. |

You may add derived columns such as normalized text, length, token counts, digit counts, URL/contact markers,
nearest-neighbor ids, model predictions, or manual adjudication notes.

## Notes For Audits

- Preserve stable ids in all generated artifacts.
- The same or near-identical `text` string may appear more than once.
- Some held-out examples may be exact or near matches to training examples.
- Shortcut probes should focus on features you can derive from the public raw text or row metadata, such as
  message length, digits, contact tokens, promotional phrases, or corpus-position artifacts.
- Ambiguity is not automatically a label error. Use evidence and explain the limitation.
