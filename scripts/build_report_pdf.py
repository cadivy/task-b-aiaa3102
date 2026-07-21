"""Render report.md to report.pdf.

Pipeline: pandoc converts the Markdown to a standalone HTML file, then a
headless Chromium browser prints that HTML to PDF. This avoids a LaTeX
dependency, which is not available on the project machines.

Requires pandoc on PATH and either Microsoft Edge or Google Chrome installed.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "report.md"
STYLESHEET = Path(__file__).resolve().parent / "report.css"
OUTPUT = ROOT / "report.pdf"

TITLE = "Dataset Forensics and Label Audit"

BROWSER_CANDIDATES = (
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
)


def find_browser() -> Path:
    for candidate in BROWSER_CANDIDATES:
        if candidate.exists():
            return candidate
    for name in ("msedge", "chrome", "chromium"):
        found = shutil.which(name)
        if found:
            return Path(found)
    raise SystemExit("No Chromium-based browser found; install Edge or Chrome.")


def main() -> None:
    if not shutil.which("pandoc"):
        raise SystemExit("pandoc not found on PATH.")
    if not SOURCE.exists():
        raise SystemExit(f"Missing source document: {SOURCE}")

    browser = find_browser()

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        html = work / "report.html"
        shutil.copyfile(STYLESHEET, work / "report.css")

        subprocess.run(
            [
                "pandoc",
                str(SOURCE),
                "-f",
                "gfm",
                "-t",
                "html5",
                "--standalone",
                "--metadata",
                f"title={TITLE}",
                "--css",
                "report.css",
                "-o",
                str(html),
            ],
            check=True,
        )

        subprocess.run(
            [
                str(browser),
                "--headless=new",
                "--disable-gpu",
                "--no-pdf-header-footer",
                f"--print-to-pdf={OUTPUT}",
                html.resolve().as_uri(),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    if not OUTPUT.exists():
        raise SystemExit("Browser did not produce a PDF.")

    size_kb = OUTPUT.stat().st_size // 1024
    print(f"Wrote {OUTPUT.relative_to(ROOT)} ({size_kb} KB)")


if __name__ == "__main__":
    main()
