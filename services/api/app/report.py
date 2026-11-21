"""PDF supervisory note for a case: findings, legal basis of failed criteria and
SHA-256 hashes of the preserved evidence."""
import io
from datetime import UTC, datetime
from xml.sax.saxutils import escape

from investwatch_common.models import Case, Finding
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .evidence import build_manifest, load_artifacts

FONT_REGULAR = "DejaVuSans"
FONT_BOLD = "DejaVuSans-Bold"
FONT_DIR = "/usr/share/fonts/truetype/dejavu"

MODULE_NAMES = {"m1": "M1 - finfluencerzy", "m2": "M2 - informacja o ryzyku", "m3": "M3 - shadow advisory"}


def _register_fonts() -> None:
    if FONT_REGULAR not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(FONT_REGULAR, f"{FONT_DIR}/DejaVuSans.ttf"))
        pdfmetrics.registerFont(TTFont(FONT_BOLD, f"{FONT_DIR}/DejaVuSans-Bold.ttf"))


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()["Normal"]
    return {
        "body": ParagraphStyle("body", parent=base, fontName=FONT_REGULAR, fontSize=9, leading=12),
        "small": ParagraphStyle("small", parent=base, fontName=FONT_REGULAR, fontSize=7.5, leading=10, textColor=colors.HexColor("#555555")),
        "h1": ParagraphStyle("h1", parent=base, fontName=FONT_BOLD, fontSize=16, leading=20, spaceAfter=6),
        "h2": ParagraphStyle("h2", parent=base, fontName=FONT_BOLD, fontSize=11, leading=14, spaceBefore=10, spaceAfter=4),
    }


def _p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(text), style)


def _finding_block(finding: Finding, styles: dict[str, ParagraphStyle]) -> list:
    doc = finding.document
    manifest = build_manifest(doc, load_artifacts(doc))
    block = [
        _p(f"Finding #{finding.id} - {MODULE_NAMES.get(finding.module, finding.module)}", styles["h2"]),
        _p(f"Wynik: {finding.score:.2f} | status: {finding.status}", styles["body"]),
        _p(f"URL: {doc.url}", styles["body"]),
        _p(f"Pobrano: {doc.fetched_at:%Y-%m-%d %H:%M} UTC", styles["body"]),
    ]
    if finding.explanation:
        block.append(_p(f"Uzasadnienie: {finding.explanation}", styles["body"]))

    failed = [c for c in (finding.details or {}).get("criteria", []) if c.get("applicable") and c.get("score", 1) < 0.5]
    if failed:
        rows = [[_p("Kryterium", styles["small"]), _p("Podstawa prawna", styles["small"]), _p("Dowód", styles["small"])]]
        for c in failed:
            rows.append(
                [
                    _p(c.get("name") or c["id"], styles["small"]),
                    _p(c.get("legal_basis", ""), styles["small"]),
                    _p(c.get("evidence") or "-", styles["small"]),
                ]
            )
        table = Table(rows, colWidths=[50 * mm, 55 * mm, 65 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        block += [Spacer(1, 3), table]

    hashes = [["content_hash", doc.content_hash]] + [[name, meta["sha256"]] for name, meta in manifest["files"].items()]
    block.append(Spacer(1, 4))
    for name, digest in hashes:
        block.append(_p(f"SHA-256 {name}: {digest}", styles["small"]))
    return block


def build_case_report(case: Case, findings: list[Finding]) -> bytes:
    _register_fonts()
    styles = _styles()
    buffer = io.BytesIO()
    pdf = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm, bottomMargin=18 * mm,
        title=f"InvestWatch - case #{case.id}",
    )
    story = [
        _p(f"Notatka dla nadzoru - case #{case.id}", styles["h1"]),
        _p(f"Podmiot: {case.primary_entity.name} ({'autoryzowany' if case.primary_entity.authorized else 'brak autoryzacji'})", styles["body"]),
        _p(f"Wygenerowano: {datetime.now(UTC):%Y-%m-%d %H:%M} UTC | findingów: {len(findings)}", styles["body"]),
    ]
    for finding in sorted(findings, key=lambda f: f.score, reverse=True):
        story += _finding_block(finding, styles)
    pdf.build(story)
    return buffer.getvalue()
