"""Generate the final project report PDF from audited result files."""

from __future__ import annotations

import html
import shutil
from pathlib import Path

import pandas as pd
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from common import FIGURES_DIR, RESULTS_DIR, ROOT


OUTPUT_DIR = ROOT / "output" / "pdf"
OUTPUT_PATH = OUTPUT_DIR / "report.pdf"
ROOT_REPORT_PATH = ROOT / "report.pdf"

NAVY = colors.HexColor("#172554")
BLUE = colors.HexColor("#2563EB")
PALE_BLUE = colors.HexColor("#EFF6FF")
RED = colors.HexColor("#DC2626")
INK = colors.HexColor("#111827")
MUTED = colors.HexColor("#4B5563")
LIGHT = colors.HexColor("#E5E7EB")
WHITE = colors.white


def pct(value: float, digits: int = 2) -> str:
    return f"{100 * float(value):.{digits}f}%"


def p(text: str, style) -> Paragraph:
    return Paragraph(html.escape(str(text)).replace("\n", "<br/>"), style)


def rich(text: str, style) -> Paragraph:
    return Paragraph(text, style)


def make_table(data, widths=None, header=True, font_size=8.2, alignments=None) -> Table:
    converted = []
    for row_index, row in enumerate(data):
        converted_row = []
        for value in row:
            style = STYLES["table_header"] if header and row_index == 0 else STYLES["table_cell"]
            converted_row.append(p(value, style))
        converted.append(converted_row)
    table = Table(converted, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.35, LIGHT),
        ("ROWBACKGROUNDS", (0, 1 if header else 0), (-1, -1), [WHITE, colors.HexColor("#F9FAFB")]),
    ]
    if header:
        commands.extend(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ]
        )
    if alignments:
        for column, alignment in enumerate(alignments):
            commands.append(("ALIGN", (column, 1 if header else 0), (column, -1), alignment))
    table.setStyle(TableStyle(commands))
    return table


def report_image(filename: str, width: float = 6.6 * inch) -> Image:
    path = FIGURES_DIR / filename
    if not path.exists():
        raise FileNotFoundError(path)
    image = Image(str(path))
    ratio = width / image.imageWidth
    image.drawWidth = width
    image.drawHeight = image.imageHeight * ratio
    image.hAlign = "CENTER"
    return image


def first_page(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    canvas.setFillColor(BLUE)
    canvas.rect(0, A4[1] - 12 * mm, A4[0], 12 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#93C5FD"))
    canvas.circle(A4[0] - 25 * mm, 24 * mm, 15 * mm, fill=1, stroke=0)
    canvas.restoreState()


def later_pages(canvas, doc) -> None:
    canvas.saveState()
    canvas.setStrokeColor(LIGHT)
    canvas.setLineWidth(0.5)
    canvas.line(20 * mm, A4[1] - 16 * mm, A4[0] - 20 * mm, A4[1] - 16 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(20 * mm, A4[1] - 12 * mm, "AIAA3102 - Dataset Forensics and Label Audit")
    canvas.drawRightString(A4[0] - 20 * mm, 11 * mm, f"Page {doc.page}")
    canvas.restoreState()


BASE = getSampleStyleSheet()
STYLES = {
    "cover_kicker": ParagraphStyle(
        "cover_kicker",
        parent=BASE["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#BFDBFE"),
        alignment=TA_LEFT,
        spaceAfter=9,
    ),
    "cover_title": ParagraphStyle(
        "cover_title",
        parent=BASE["Title"],
        fontName="Helvetica-Bold",
        fontSize=29,
        leading=34,
        textColor=WHITE,
        alignment=TA_LEFT,
        spaceAfter=14,
    ),
    "cover_subtitle": ParagraphStyle(
        "cover_subtitle",
        parent=BASE["Normal"],
        fontName="Helvetica",
        fontSize=13,
        leading=19,
        textColor=colors.HexColor("#DBEAFE"),
        alignment=TA_LEFT,
    ),
    "h1": ParagraphStyle(
        "h1",
        parent=BASE["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=NAVY,
        spaceBefore=3,
        spaceAfter=10,
    ),
    "h2": ParagraphStyle(
        "h2",
        parent=BASE["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12.5,
        leading=16,
        textColor=BLUE,
        spaceBefore=9,
        spaceAfter=5,
    ),
    "body": ParagraphStyle(
        "body",
        parent=BASE["BodyText"],
        fontName="Helvetica",
        fontSize=9.4,
        leading=14.2,
        textColor=INK,
        spaceAfter=7,
    ),
    "small": ParagraphStyle(
        "small",
        parent=BASE["BodyText"],
        fontName="Helvetica",
        fontSize=8.1,
        leading=11.2,
        textColor=MUTED,
        spaceAfter=4,
    ),
    "callout": ParagraphStyle(
        "callout",
        parent=BASE["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=10.2,
        leading=15,
        textColor=NAVY,
        backColor=PALE_BLUE,
        borderColor=colors.HexColor("#BFDBFE"),
        borderWidth=0.7,
        borderPadding=9,
        spaceBefore=5,
        spaceAfter=10,
    ),
    "table_header": ParagraphStyle(
        "table_header",
        parent=BASE["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.7,
        leading=9.5,
        textColor=WHITE,
    ),
    "table_cell": ParagraphStyle(
        "table_cell",
        parent=BASE["Normal"],
        fontName="Helvetica",
        fontSize=7.7,
        leading=9.7,
        textColor=INK,
    ),
    "caption": ParagraphStyle(
        "caption",
        parent=BASE["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7.7,
        leading=10,
        textColor=MUTED,
        alignment=TA_CENTER,
        spaceBefore=3,
        spaceAfter=8,
    ),
}


class ReportDocTemplate(BaseDocTemplate):
    def __init__(self, filename: str):
        super().__init__(
            filename,
            pagesize=A4,
            rightMargin=19 * mm,
            leftMargin=19 * mm,
            topMargin=22 * mm,
            bottomMargin=18 * mm,
            title="Dataset Forensics and Label Audit",
            author="AIAA3102 Project Team",
            subject="Final Project Topic B",
        )
        cover_frame = Frame(23 * mm, 25 * mm, A4[0] - 46 * mm, A4[1] - 54 * mm, id="cover")
        body_frame = Frame(19 * mm, 18 * mm, A4[0] - 38 * mm, A4[1] - 40 * mm, id="body")
        self.addPageTemplates(
            [
                PageTemplate(
                    id="Cover",
                    frames=[cover_frame],
                    onPage=first_page,
                    autoNextPageTemplate="Body",
                ),
                PageTemplate(id="Body", frames=[body_frame], onPage=later_pages, autoNextPageTemplate="Body"),
            ]
        )


def build_story() -> list:
    profile = pd.read_csv(RESULTS_DIR / "profile_summary.csv")
    baseline = pd.read_csv(RESULTS_DIR / "baseline_metrics.csv")
    thresholds = pd.read_csv(RESULTS_DIR / "near_duplicate_threshold_sensitivity.csv")
    shortcut = pd.read_csv(RESULTS_DIR / "shortcut_metrics.csv")
    interventions = pd.read_csv(RESULTS_DIR / "intervention_metrics.csv")
    suspicious = pd.read_csv(ROOT / "suspicious_examples.csv")

    b = baseline.set_index("condition")
    s = shortcut.set_index("condition")
    i = interventions.set_index("condition")

    story = []
    story.extend(
        [
            Spacer(1, 35 * mm),
            rich("AIAA3102 FINAL PROJECT / TOPIC B", STYLES["cover_kicker"]),
            rich("Dataset Forensics<br/>and Label Audit", STYLES["cover_title"]),
            rich(
                "An evidence-calibrated audit of duplication, cross-split leakage, likely label errors, shortcut features, and annotation ambiguity in the UCI SMS Spam Collection.",
                STYLES["cover_subtitle"],
            ),
            Spacer(1, 42 * mm),
            rich("Fixed course split: 4,460 train / 1,114 held-out", STYLES["cover_kicker"]),
            rich("Reproducible CPU pipeline | July 2026", STYLES["cover_subtitle"]),
            PageBreak(),
        ]
    )

    story.extend(
        [
            rich("Executive Summary", STYLES["h1"]),
            p(
                "A simple word TF-IDF classifier reaches 99.10% accuracy and 96.55% spam F1 on the fixed held-out split. This project tests whether that score supports a trustworthy generalization claim. The answer is qualified: the model is strong, but the dataset contains repeated templates, cross-split leakage, likely label-policy errors, and highly predictive shallow cues.",
                STYLES["body"],
            ),
            rich(
                "The main validity result: removing 62 held-out rows linked to accepted exact or near training matches changes overall accuracy by only 0.05 points, but lowers spam recall from 93.96% to 90.91%. Accuracy alone hides the audit's largest effect.",
                STYLES["callout"],
            ),
            p(
                "The audit finds 290 exact-duplicate clusters involving 705 rows, including five clusters crossing the fixed split. At the public 0.92 TF-IDF cosine threshold, 361 non-exact candidate pairs remain; 90 cross the split. Evidence-and-policy review accepts 84 cross-split template matches and rejects six false-positive traps. Eleven likely label errors are reported with independent model and policy evidence, while eight ambiguity claims distinguish genuine policy boundaries from model uncertainty.",
                STYLES["body"],
            ),
            p(
                "Shallow contact and promotional features alone reach 98.20% accuracy and 93.15% spam F1. They are useful task cues but fragile: legitimate price discussions become false positives, and spam without numeric markers can become false negatives. Exact training deduplication and a nine-row label overlay do not improve the official score; this reinforces that audit actions should be justified by validity, not benchmark optimization.",
                STYLES["body"],
            ),
            rich("Key outputs", STYLES["h2"]),
            make_table(
                [
                    ["Output", "Result"],
                    ["Ranked audit", f"{len(suspicious)} claims; six issue types; {pct((suspicious.confidence == 'high').mean(), 1)} high confidence"],
                    ["Duplicate audit", "290 exact clusters; 5 cross-split exact clusters"],
                    ["Leakage sensitivity", "62 held-out rows excluded; spam recall -3.05 percentage points"],
                    ["Label review", "11 likely errors; 9 training overlays; held-out labels untouched"],
                    ["Interventions", "Exact deduplication, filtering, overlay, combined, and leakage-aware evaluation"],
                ],
                widths=[1.55 * inch, 4.95 * inch],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            rich("1. Dataset and Research Questions", STYLES["h1"]),
            p(
                "The UCI SMS Spam Collection is a public corpus of 5,574 labelled SMS messages assembled from several sources for mobile-spam research [1]. The course manifest maps every 1-based UCI row to a stable ID and a fixed train or held-out split [2]. The raw archive and extracted corpus were SHA-256 checked, then joined one-to-one with the manifest. All row-count, ID, split-prefix, label-domain and empty-text assertions passed.",
                STYLES["body"],
            ),
            make_table(
                [
                    ["Split", "Ham", "Spam", "Total", "Spam share"],
                    ["Train", "3,862", "598", "4,460", "13.41%"],
                    ["Held-out", "965", "149", "1,114", "13.38%"],
                    ["All", "4,827", "747", "5,574", "13.40%"],
                ],
                widths=[1.4 * inch, 1.05 * inch, 1.05 * inch, 1.15 * inch, 1.4 * inch],
                alignments=["LEFT", "RIGHT", "RIGHT", "RIGHT", "RIGHT"],
            ),
            Spacer(1, 7),
            report_image("class_distribution.png", 6.25 * inch),
            rich("Figure 1. Class counts are closely matched in proportion across the fixed split.", STYLES["caption"]),
            rich("Research questions", STYLES["h2"]),
            p(
                "(1) Are held-out examples independent of training? (2) Which labels have enough independent evidence to merit review? (3) How much performance can shallow features explain? (4) Which examples remain policy-ambiguous? (5) How do controlled data interventions change the meaning of evaluation?",
                STYLES["body"],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            rich("2. Methodology", STYLES["h1"]),
            rich("2.1 Profiling and baselines", STYLES["h2"]),
            p(
                "The canonical table contains stable ID, split, 1-based UCI row number, raw text and public label. Derived features include message length, token count, digits, capitalization, URL, phone, currency, promotional tokens and normalized row position. The primary model is word TF-IDF over unigrams and bigrams with Logistic Regression. A character 3-5-gram model supplies a representation-diverse diagnostic. Training evidence uses five-fold out-of-fold probabilities; held-out models are fitted only on training [3].",
                STYLES["body"],
            ),
            rich("2.2 Duplicates and leakage", STYLES["h2"]),
            p(
                "Exact duplicates use the public lowercase-plus-whitespace-collapse rule. Near candidates are retrieved with word and character TF-IDF cosine search. A pair is eligible at a primary cosine of at least 0.92 and must not be exact. Cross-split candidates then receive a separate text-comparison decision. The audit retains rejected threshold crossings so precision control is visible.",
                STYLES["body"],
            ),
            rich("2.3 Label errors and ambiguity", STYLES["h2"]),
            p(
                "Label-error retrieval combines OOF or held-out model disagreement, representation-diverse model agreement, nearest-neighbour label evidence and cluster evidence. Final claims require at least two evidence sources, including a policy reading of the original text. Ambiguity is used only when missing consent or sender context leaves two plausible labels; low model confidence alone is rejected as proof.",
                STYLES["body"],
            ),
            rich("2.4 Shortcut and intervention tests", STYLES["h2"]),
            p(
                "Shallow Logistic Regression conditions isolate shape, contact/promotion and row-position features. A masked-text model replaces a predeclared promotional lexicon. Controlled interventions keep model settings fixed while changing exact training duplication, high-confidence filtering, a nine-row training-label overlay, or the leakage-aware evaluation subset. No held-out label is edited.",
                STYLES["body"],
            ),
            rich("Confidence calibration", STYLES["h2"]),
            p(
                "High confidence requires direct definitional evidence and no unresolved counterexample. Medium confidence marks threshold- or policy-sensitive cases. Low confidence records rejected or weak candidates. The final 51-row audit contains 26 high-confidence claims (51.0%), below the public 55% cap.",
                STYLES["body"],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            rich("3. Dataset Profile and Baseline", STYLES["h1"]),
            p(
                "Spam is longer and much more numeric than ham: median length is 149 versus 52 characters, median digit count is 16 versus 0, phone-like numbers occur in 60.78% versus 0.10%, and currency cues in 38.15% versus 0.62%. These gaps make strong shallow performance plausible before any lexical model is trained.",
                STYLES["body"],
            ),
            report_image("length_distribution.png", 6.25 * inch),
            rich("Figure 2. Spam messages are substantially longer than ham messages.", STYLES["caption"]),
            make_table(
                [
                    ["Condition", "Accuracy", "Spam P", "Spam R", "Spam F1", "Macro F1"],
                    ["Word, train OOF", pct(b.loc["word_oof", "accuracy"]), pct(b.loc["word_oof", "spam_precision"]), pct(b.loc["word_oof", "spam_recall"]), pct(b.loc["word_oof", "spam_f1"]), pct(b.loc["word_oof", "macro_f1"])],
                    ["Character, train OOF", pct(b.loc["char_oof", "accuracy"]), pct(b.loc["char_oof", "spam_precision"]), pct(b.loc["char_oof", "spam_recall"]), pct(b.loc["char_oof", "spam_f1"]), pct(b.loc["char_oof", "macro_f1"])],
                    ["Word, held-out", pct(b.loc["word_heldout", "accuracy"]), pct(b.loc["word_heldout", "spam_precision"]), pct(b.loc["word_heldout", "spam_recall"]), pct(b.loc["word_heldout", "spam_f1"]), pct(b.loc["word_heldout", "macro_f1"])],
                    ["Character, held-out", pct(b.loc["char_heldout", "accuracy"]), pct(b.loc["char_heldout", "spam_precision"]), pct(b.loc["char_heldout", "spam_recall"]), pct(b.loc["char_heldout", "spam_f1"]), pct(b.loc["char_heldout", "macro_f1"])],
                ],
                widths=[1.7 * inch, 0.9 * inch, 0.9 * inch, 0.9 * inch, 0.95 * inch, 0.95 * inch],
                alignments=["LEFT", "RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT"],
            ),
            Spacer(1, 8),
            rich(
                "Raw held-out accuracy is high, but nine of ten errors are public spam rows predicted ham. Accuracy is therefore less informative than spam recall and audit-aware error analysis.",
                STYLES["callout"],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            rich("4. Duplicate and Leakage Findings", STYLES["h1"]),
            p(
                "Lowercase and whitespace normalization yields 5,159 unique texts. The audit finds 290 exact clusters containing 705 rows; the largest is a 30-row training cluster. Five exact clusters cross the fixed split, all with consistent labels. Their problem is independence, not label conflict.",
                STYLES["body"],
            ),
            report_image("exact_cluster_sizes.png", 6.15 * inch),
            rich("Figure 3. Most exact clusters are small, but a few repeated templates are large.", STYLES["caption"]),
            make_table(
                [["Threshold", "All pairs", "Cross-split", "Label conflicts"]]
                + [
                    [f"{row.threshold:.2f}", str(int(row.candidate_pairs)), str(int(row.cross_split_pairs)), str(int(row.label_conflict_pairs))]
                    for row in thresholds.itertuples()
                ],
                widths=[1.45 * inch, 1.45 * inch, 1.55 * inch, 1.55 * inch],
                alignments=["RIGHT", "RIGHT", "RIGHT", "RIGHT"],
            ),
            Spacer(1, 7),
            p(
                "At 0.92, 361 non-exact pairs remain and 90 cross the split. Eighty-four cross-split pairs are accepted as shared templates and six are rejected. The clearest false-positive trap has word cosine 1.0: one text ends in 'affectionate' and the other in 'hostile'. Common words dominate the representation while the meaning reverses.",
                STYLES["body"],
            ),
            PageBreak(),
        ]
    )

    leak = i
    story.extend(
        [
            rich("5. Leakage-Aware Evaluation", STYLES["h1"]),
            p(
                "The accepted relationships affect five exact held-out rows and 59 near-matched held-out IDs. Their union contains 62 rows because two held-out messages participate in both exact and near relationships. The fitted model is kept fixed while these rows are excluded from sensitivity subsets.",
                STYLES["body"],
            ),
            make_table(
                [
                    ["Evaluation set", "N", "Accuracy", "Spam recall", "Spam F1", "Macro F1"],
                    ["Original", "1,114", pct(i.loc["original_baseline", "accuracy"]), pct(i.loc["original_baseline", "spam_recall"]), pct(i.loc["original_baseline", "spam_f1"]), pct(i.loc["original_baseline", "macro_f1"])],
                    ["Exclude exact", "1,109", pct(i.loc["exclude_exact_leakage", "accuracy"]), pct(i.loc["exclude_exact_leakage", "spam_recall"]), pct(i.loc["exclude_exact_leakage", "spam_f1"]), pct(i.loc["exclude_exact_leakage", "macro_f1"])],
                    ["Exclude exact + near", "1,052", pct(i.loc["exclude_exact_and_near_leakage", "accuracy"]), pct(i.loc["exclude_exact_and_near_leakage", "spam_recall"]), pct(i.loc["exclude_exact_and_near_leakage", "spam_f1"]), pct(i.loc["exclude_exact_and_near_leakage", "macro_f1"])],
                ],
                widths=[1.85 * inch, 0.65 * inch, 1.0 * inch, 1.05 * inch, 1.0 * inch, 1.0 * inch],
                alignments=["LEFT", "RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT"],
            ),
            Spacer(1, 10),
            rich(
                "Overall accuracy falls by only 0.05 points, while spam recall falls by 3.05 points and spam F1 by 1.81 points. The minority-class metrics reveal a meaningful novelty penalty that the headline accuracy conceals.",
                STYLES["callout"],
            ),
            p(
                "The result does not prove that every repeated template is invalid in deployment. Recurring spam campaigns can be realistic. It does prove that the fixed held-out set mixes novel examples with messages recoverable from training, so a single score cannot support both file-level and novel-template generalization claims.",
                STYLES["body"],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            rich("6. Likely Label Errors and Ambiguity", STYLES["h1"]),
            p(
                "Automated retrieval produced 73 label-error candidates. Evidence-and-policy adjudication retains 11: seven high-confidence and four medium-confidence. Nine training proposals are stored in an overlay; two held-out cases remain flags only. The clearest suspected spam-to-ham corrections are standalone jokes with no solicitation, charge or response mechanism.",
                STYLES["body"],
            ),
            make_table(
                [
                    ["ID", "Public", "Proposed", "Confidence", "Reason"],
                    ["T2378", "spam", "ham", "High", "Driving joke; both OOF models strongly ham"],
                    ["T0059", "spam", "ham", "High", "Divorce Barbie joke; no action or charge"],
                    ["T2232", "spam", "ham", "High", "Child/teenager joke"],
                    ["T4358", "spam", "ham", "High", "Stolen-toilet joke"],
                    ["T3791", "ham", "spam", "High", "Unsolicited free-SMS platform invitation"],
                    ["H0143", "spam", "ham-like", "High", "Tattoo joke; held-out label unchanged"],
                ],
                widths=[0.65 * inch, 0.7 * inch, 0.75 * inch, 0.8 * inch, 3.5 * inch],
            ),
            Spacer(1, 8),
            p(
                "Eight ambiguity claims are reported separately. Seven are policy cases involving adult-chat style, premium-number follow-up, research recruitment, charity, club advertising, job follow-up or social-platform invitations. H0935 is retained as a rejected ambiguity candidate: model probabilities straddle 0.5, but 'I liked the new mobile' is ordinary ham. Uncertainty alone is not ambiguity.",
                STYLES["body"],
            ),
            rich(
                "Two of the baseline's ten held-out errors are likely label-policy errors. Treating them as unresolved changes an audit sensitivity accuracy from 99.10% to 99.28%; this is not presented as a corrected official score.",
                STYLES["callout"],
            ),
            p(
                "The policy review was AI-assisted and is not represented as two independent human annotators. No fabricated kappa or agreement statistic is reported. This disclosure limits the strength of subjective sample-level conclusions while preserving reproducibility of the automated evidence.",
                STYLES["small"],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            rich("7. Shortcut Features", STYLES["h1"]),
            p(
                "Contact and promotion features have substantial predictive power. Digit count has the largest standardized shallow-model coefficient (2.434), followed by promotional-token count (1.671), average token length (0.740), URL presence (0.666) and currency count (0.636). Row position adds no measurable value.",
                STYLES["body"],
            ),
            make_table(
                [
                    ["Condition", "Accuracy", "Spam recall", "Spam F1", "Macro F1"],
                    ["Majority ham", pct(s.loc["majority_ham", "accuracy"]), pct(s.loc["majority_ham", "spam_recall"]), pct(s.loc["majority_ham", "spam_f1"]), pct(s.loc["majority_ham", "macro_f1"])],
                    ["Shape only", pct(s.loc["shape_only", "accuracy"]), pct(s.loc["shape_only", "spam_recall"]), pct(s.loc["shape_only", "spam_f1"]), pct(s.loc["shape_only", "macro_f1"])],
                    ["Contact/promotion", pct(s.loc["contact_promo_only", "accuracy"]), pct(s.loc["contact_promo_only", "spam_recall"]), pct(s.loc["contact_promo_only", "spam_f1"]), pct(s.loc["contact_promo_only", "macro_f1"])],
                    ["All shallow", pct(s.loc["all_shallow", "accuracy"]), pct(s.loc["all_shallow", "spam_recall"]), pct(s.loc["all_shallow", "spam_f1"]), pct(s.loc["all_shallow", "macro_f1"])],
                    ["Masked text", pct(s.loc["masked_text", "accuracy"]), pct(s.loc["masked_text", "spam_recall"]), pct(s.loc["masked_text", "spam_f1"]), pct(s.loc["masked_text", "macro_f1"])],
                    ["Full text", pct(s.loc["full_text", "accuracy"]), pct(s.loc["full_text", "spam_recall"]), pct(s.loc["full_text", "spam_f1"]), pct(s.loc["full_text", "macro_f1"])],
                ],
                widths=[1.9 * inch, 1.1 * inch, 1.1 * inch, 1.05 * inch, 1.1 * inch],
                alignments=["LEFT", "RIGHT", "RIGHT", "RIGHT", "RIGHT"],
            ),
            Spacer(1, 8),
            report_image("shortcut_metrics.png", 6.45 * inch),
            rich("Figure 4. Shallow features are strong, but their example-level failures are systematic.", STYLES["caption"]),
            p(
                "The cues are relevant but fragile. H0946 is a legitimate price discussion assigned shallow spam probability 0.991; H0044 is a ringtone solicitation assigned shallow probability 0.088. Premium-rate adult-chat messages can be caught almost entirely by price and phone markers even when the full text classifier misses them.",
                STYLES["body"],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            rich("8. Data-Intervention Results", STYLES["h1"]),
            report_image("intervention_metrics.png", 6.55 * inch),
            rich("Figure 5. Data interventions change minority-class metrics more than headline accuracy.", STYLES["caption"]),
            make_table(
                [
                    ["Condition", "Train N", "Test N", "Accuracy", "Spam recall", "Spam F1"],
                    ["Original", "4,460", "1,114", pct(i.loc["original_baseline", "accuracy"]), pct(i.loc["original_baseline", "spam_recall"]), pct(i.loc["original_baseline", "spam_f1"])],
                    ["Exact dedup train", "4,128", "1,114", pct(i.loc["deduplicate_exact_training", "accuracy"]), pct(i.loc["deduplicate_exact_training", "spam_recall"]), pct(i.loc["deduplicate_exact_training", "spam_f1"])],
                    ["High-conf filter", "4,454", "1,114", pct(i.loc["filter_high_confidence_label_errors", "accuracy"]), pct(i.loc["filter_high_confidence_label_errors", "spam_recall"]), pct(i.loc["filter_high_confidence_label_errors", "spam_f1"])],
                    ["Label overlay", "4,460", "1,114", pct(i.loc["training_label_overlay", "accuracy"]), pct(i.loc["training_label_overlay", "spam_recall"]), pct(i.loc["training_label_overlay", "spam_f1"])],
                    ["Dedup + overlay", "4,128", "1,114", pct(i.loc["deduplicate_plus_overlay", "accuracy"]), pct(i.loc["deduplicate_plus_overlay", "spam_recall"]), pct(i.loc["deduplicate_plus_overlay", "spam_f1"])],
                    ["Leakage-aware", "4,460", "1,052", pct(i.loc["exclude_exact_and_near_leakage", "accuracy"]), pct(i.loc["exclude_exact_and_near_leakage", "spam_recall"]), pct(i.loc["exclude_exact_and_near_leakage", "spam_f1"])],
                ],
                widths=[1.75 * inch, 0.8 * inch, 0.8 * inch, 1.0 * inch, 1.05 * inch, 1.0 * inch],
                alignments=["LEFT", "RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT"],
            ),
            Spacer(1, 8),
            p(
                "Exact deduplication removes 332 training rows and lowers spam recall by 1.34 points. The high-confidence filter and nine-row label overlay each change only two predictions and do not improve the official score. These results discourage performance-driven cleaning: corrections should follow evidence even when the benchmark metric declines.",
                STYLES["body"],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            rich("9. Difficulties and Solutions", STYLES["h1"]),
            rich("Difficulty 1 - Stable raw-row alignment", STYLES["h2"]),
            p(
                "A single parse offset would invalidate every stable ID and hidden-key comparison. The solution was to split each raw line only on its first tab, use a 1-based row number, perform a one-to-one merge, and stop on any count, ID, split-prefix, label-domain or empty-text failure. Verification is stored in data_validation.json.",
                STYLES["body"],
            ),
            rich("Difficulty 2 - TF-IDF false-positive traps", STYLES["h2"]),
            p(
                "Word cosine can be 1.0 when only a decisive adjective changes. We kept the public threshold for reproducibility, added character similarity and a separate text-comparison decision, and retained six rejected cross-split pairs. The affectionate/hostile reversal provides a directly verifiable counterexample.",
                STYLES["body"],
            ),
            rich("Difficulty 3 - Label error versus model error", STYLES["h2"]),
            p(
                "The conservative classifier produces many spam false negatives, most of which remain valid spam. We required two evidence sources and a policy reading, then stored training proposals as an overlay rather than editing public labels. Seventy-three automated candidates were reduced to eleven submitted findings.",
                STYLES["body"],
            ),
            rich("Difficulty 4 - Accuracy conceals minority-class impact", STYLES["h2"]),
            p(
                "Leakage-aware accuracy changes by only 0.05 points, which initially appears negligible. Reporting spam recall and F1 reveals a 3.05-point recall decline. The solution was to predefine class-specific metrics and interpret score decreases as potentially stricter evaluation rather than model failure.",
                STYLES["body"],
            ),
            rich("Difficulty 5 - Honest AI-assisted adjudication", STYLES["h2"]),
            p(
                "The project requires manual judgment, but this implementation was independently executed with AI assistance. We separated automated evidence from a policy pass, logged every selected judgment, and explicitly avoided claiming two human reviewers or fabricated agreement statistics. Independent team sign-off remains advisable before academic submission.",
                STYLES["body"],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            rich("10. Conclusions and Recommendations", STYLES["h1"]),
            p(
                "The fixed SMS corpus supports a strong classifier, but the 99.10% headline accuracy is not a complete generalization statement. Five exact clusters cross the split, 59 held-out IDs participate in accepted near matches, shallow cues nearly match the text model, and a small number of policy-sensitive labels account for a material share of observed errors.",
                STYLES["body"],
            ),
            rich(
                "Recommended benchmark redesign: group exact and accepted near templates before splitting; publish a consent-aware annotation guide; preserve an uncertain/policy-boundary category; and report spam recall, spam F1, and leakage-aware sensitivity beside overall accuracy.",
                STYLES["callout"],
            ),
            p(
                "The most defensible quantitative conclusion is narrow: overall accuracy is stable, but novel-template spam recall is lower than the raw split suggests. The audit does not claim definitive ground truth for every subjective message, and it does not treat performance changes as proof that a cleaning decision is correct.",
                STYLES["body"],
            ),
            rich("AI usage declaration", STYLES["h2"]),
            p(
                "OpenAI Codex was used to interpret the supplied specification, implement and test the analysis pipeline, generate candidate evidence, perform an explicitly AI-assisted policy pass, draft documentation, and generate this report. AI outputs were treated as untrusted drafts: row mappings were checked by assertions, numerical claims were regenerated from saved CSV files, threshold traps were compared against original text, and submission constraints were checked programmatically. No claim of independent human double-review is made, and AI is not presented as a source of ground-truth labels. The complete usage record is in logs/chat.md.",
                STYLES["body"],
            ),
            rich("References", STYLES["h2"]),
            p(
                "[1] T. Almeida and J. Hidalgo, SMS Spam Collection, UCI Machine Learning Repository, 2011. DOI: 10.24432/C5CC84. License: CC BY 4.0.",
                STYLES["small"],
            ),
            p(
                "[2] AIAA3102 Final Project Topic B: Dataset Forensics and Label Audit, course handout and starter protocol supplied with this repository, 2026.",
                STYLES["small"],
            ),
            p(
                "[3] F. Pedregosa et al., Scikit-learn: Machine Learning in Python, Journal of Machine Learning Research 12, 2825-2830, 2011.",
                STYLES["small"],
            ),
            Spacer(1, 8),
            p(
                "Reproducibility: run python scripts/run_all.py from the repository root. The final report is generated from tracked result tables and figures; the public raw archive is downloaded on demand and checksum-recorded.",
                STYLES["small"],
            ),
        ]
    )
    return story


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    doc = ReportDocTemplate(str(OUTPUT_PATH))
    doc.build(build_story())
    shutil.copyfile(OUTPUT_PATH, ROOT_REPORT_PATH)
    reader = PdfReader(str(ROOT_REPORT_PATH))
    if len(reader.pages) < 8:
        raise AssertionError(f"Unexpectedly short report: {len(reader.pages)} pages")
    print(f"Generated {ROOT_REPORT_PATH} ({len(reader.pages)} pages)")


if __name__ == "__main__":
    main()
