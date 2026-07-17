# AI and Assistant Usage Log

This log supports the final AI usage declaration. Add an entry whenever an AI tool materially influences project structure, code, analysis choices, sample judgments or report wording.

## Entry template

### YYYY-MM-DD — Short task name

- **Tool/model:**
- **Team member:**
- **Purpose:**
- **Input scope:**
- **Output used:**
- **Verification performed:**
- **Files affected:**
- **Known limitation:**

## 2026-07-14 — V1 repository and documentation design

- **Tool/model:** OpenAI Codex
- **Team member:** To be assigned
- **Purpose:** Interpret the supplied handout and starter protocol, initialize a documentation-first project structure, and draft reproducible audit and collaboration plans.
- **Input scope:** Local course handout, translated handout, starter README, data dictionary, split manifest summary, sample submission and public audit protocol.
- **Output used:** Root README, research plan, six audit-method documents, adjudication protocol, three-person workflow, intervention plan and report outline.
- **Verification performed:** Requirements were cross-checked against the local `topic-b-handout-zh.md`, `starter/README.md` and `starter/configs/audit_protocol.json`. No sample-level audit finding or experimental metric was generated or claimed.
- **Files affected:** `README.md`, `docs/`, `audit/`, `impact_analysis.md`, `.gitignore`, and this log.
- **Known limitation:** The documents specify methods and placeholders only. Data-download, analysis scripts, numerical results and final human adjudication remain to be implemented and verified.

## 2026-07-14 — Complete independent project execution

- **Tool/model:** OpenAI Codex
- **Team member:** Independent AI-assisted implementation requested by the user
- **Purpose:** Complete the project rather than leave a documentation skeleton: download and validate the dataset, implement every analysis stage, run six audits, produce ranked findings, run interventions, replace result placeholders, and create the final PDF.
- **Input scope:** Official UCI archive, fixed course manifest, public audit protocol, all raw message texts, model outputs, similarity tables, shallow-feature results and intervention metrics.
- **Output used:** Complete `scripts/` pipeline, tracked `results/` tables and figures, 51-row `suspicious_examples.csv`, 51-row `adjudication_memo.csv`, nine-row training label overlay, six completed audit reports, final impact analysis and 12-page `report.pdf`.
- **Verification performed:** The raw archive and extracted text were SHA-256 recorded; 5574 rows were joined one-to-one to the manifest; training evidence used five-fold OOF prediction; held-out labels were never edited; public schema and calibration constraints were programmatically checked. Threshold false positives were compared against original texts. The PDF was rendered to 12 PNG pages and visually checked; an initial page-template contrast failure was found, fixed and re-rendered.
- **Files affected:** `scripts/`, `results/`, `configs/manual_review.json`, `audit/`, `README.md`, `suspicious_examples.csv`, `adjudication_memo.csv`, `impact_analysis.md`, `report.pdf`, and `output/pdf/report.pdf`.
- **Known limitation:** Sample-level policy judgments were produced through separate AI-assisted evidence and policy passes, not two independent human annotators. The repository explicitly avoids claiming human agreement or ground-truth authority.
