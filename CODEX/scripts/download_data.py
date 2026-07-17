"""Download and extract the official UCI SMS Spam Collection."""

from __future__ import annotations

import datetime as dt
import urllib.request
import zipfile
from pathlib import Path

from common import RAW_DIR, RESULTS_DIR, ensure_dirs, sha256_file, write_json


URL = (
    "https://archive.ics.uci.edu/ml/machine-learning-databases/00228/"
    "smsspamcollection.zip"
)
ARCHIVE_PATH = RAW_DIR / "smsspamcollection.zip"
RAW_TEXT_PATH = RAW_DIR / "SMSSpamCollection"


def download(url: str, destination: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "AIAA3102-dataset-audit/1.0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        destination.write_bytes(response.read())


def main() -> None:
    ensure_dirs()
    if not ARCHIVE_PATH.exists():
        print(f"Downloading {URL}")
        download(URL, ARCHIVE_PATH)
    else:
        print(f"Using existing archive: {ARCHIVE_PATH}")

    with zipfile.ZipFile(ARCHIVE_PATH) as archive:
        names = archive.namelist()
        if "SMSSpamCollection" not in names:
            raise AssertionError(f"Expected SMSSpamCollection in archive, found: {names}")
        RAW_TEXT_PATH.write_bytes(archive.read("SMSSpamCollection"))

    line_count = len(RAW_TEXT_PATH.read_bytes().splitlines())
    if line_count != 5574:
        raise AssertionError(f"Expected 5574 raw lines, found {line_count}")

    provenance = {
        "source_url": URL,
        "dataset_page": "https://archive.ics.uci.edu/dataset/228/sms+spam+collection",
        "dataset_doi": "10.24432/C5CC84",
        "license": "CC BY 4.0",
        "downloaded_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "archive_sha256": sha256_file(ARCHIVE_PATH),
        "raw_file_sha256": sha256_file(RAW_TEXT_PATH),
        "raw_line_count": line_count,
    }
    write_json(RESULTS_DIR / "data_provenance.json", provenance)
    print(f"Raw rows: {line_count}")
    print(f"Archive SHA-256: {provenance['archive_sha256']}")


if __name__ == "__main__":
    main()
