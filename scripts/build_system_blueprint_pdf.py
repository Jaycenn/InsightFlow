"""Render the InsightFlow system blueprint as a shareable PDF."""

from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    LongTable,
    PageTemplate,
    Paragraph,
    Spacer,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "InsightFlow-System-Blueprint.md"
OUTPUT = ROOT / "docs" / "InsightFlow-System-Blueprint.pdf"
ASSETS = ROOT / "docs" / "assets" / "system-blueprint"

INK = colors.HexColor("#152530")
BLUE = colors.HexColor("#173A52")
PALE = colors.HexColor("#F4F8FA")
LINE = colors.HexColor("#D9D9D9")


class BlueprintDoc(BaseDocTemplate):
    def __init__(self, path: Path):
        super().__init__(str(path), pagesize=A4, leftMargin=48, rightMargin=48, topMargin=48, bottomMargin=48)
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="normal", leftPadding=0,
                      rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates(PageTemplate(id="body", frames=[frame], onPage=self.page_decoration))

    def page_decoration(self, canv, doc):
        canv.saveState()
        canv.setFont("Helvetica", 8)
        canv.setFillColor(colors.HexColor("#60747F"))
        canv.drawString(48, 30, "InsightFlow System Blueprint")
        canv.drawRightString(A4[0] - 48, 30, str(doc.page))
        canv.restoreState()


styles = {
    "title": ParagraphStyle("BlueprintTitle", fontName="Helvetica-Bold", fontSize=22, leading=27, textColor=colors.black,
                            spaceAfter=12, keepWithNext=True),
    "h1": ParagraphStyle("BlueprintH1", fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=colors.black,
                         spaceBefore=18, spaceAfter=8, keepWithNext=True),
    "h2": ParagraphStyle("BlueprintH2", fontName="Helvetica-Bold", fontSize=11.5, leading=14, textColor=colors.black,
                         spaceBefore=13, spaceAfter=6, keepWithNext=True),
    "h3": ParagraphStyle("BlueprintH3", fontName="Helvetica-Bold", fontSize=10, leading=13, textColor=colors.black,
                         spaceBefore=11, spaceAfter=4, keepWithNext=True),
    "body": ParagraphStyle("BlueprintBody", fontName="Helvetica", fontSize=9.3, leading=13, textColor=INK,
                           spaceAfter=7),
    "list": ParagraphStyle("BlueprintList", fontName="Helvetica", fontSize=9.2, leading=12.6, textColor=INK,
                           leftIndent=14, firstLineIndent=-11, spaceAfter=4),
    "cell": ParagraphStyle("BlueprintCell", fontName="Helvetica", fontSize=8.0, leading=10.5, textColor=INK),
    "header": ParagraphStyle("BlueprintHeader", fontName="Helvetica-Bold", fontSize=8.1, leading=10.5,
                             textColor=colors.white),
    "diagram": ParagraphStyle("BlueprintDiagram", fontName="Helvetica", fontSize=8, leading=10, alignment=TA_CENTER),
}


def inline(text: str) -> str:
    parts = re.split(r"(\*\*[^*]+\*\*|`[^`]+`|\[[^]]+\]\([^)]+\))", text)
    result = []
    for part in parts:
        if part.startswith("**") and part.endswith("**"):
            result.append(f"<b>{html.escape(part[2:-2])}</b>")
        elif part.startswith("`") and part.endswith("`"):
            result.append(f'<font face="Courier">{html.escape(part[1:-1])}</font>')
        elif part.startswith("[") and "](" in part:
            match = re.match(r"\[([^]]+)\]\(([^)]+)\)", part)
            if match:
                label, url = match.groups()
                result.append(f'<link href="{html.escape(url)}" color="#173A52">{html.escape(label)}</link>')
        else:
            result.append(html.escape(part))
    return "".join(result)


def make_table(source_lines: list[str]) -> LongTable:
    raw = [[c.strip() for c in line.strip().strip("|").split("|")] for line in source_lines]
    raw.pop(1)
    col_count = len(raw[0])
    available = A4[0] - 96
    if col_count == 4 and raw[0][0] == "Canonical field":
        proportions = [0.19, 0.12, 0.27, 0.42]
    elif col_count == 4 and raw[0][0] == "Method":
        proportions = [0.11, 0.39, 0.38, 0.12]
    elif col_count == 4:
        proportions = [0.17, 0.31, 0.38, 0.14]
    elif col_count == 3:
        proportions = [0.23, 0.32, 0.45]
    elif col_count == 2:
        proportions = [0.30, 0.70]
    else:
        proportions = [1 / col_count] * col_count
    data = []
    for row_index, row in enumerate(raw):
        style = styles["header"] if row_index == 0 else styles["cell"]
        data.append([Paragraph(inline(item), style) for item in row])
    table = LongTable(data, colWidths=[available * p for p in proportions], repeatRows=1, hAlign="CENTER")
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]
    for row in range(2, len(data), 2):
        commands.append(("BACKGROUND", (0, row), (-1, row), PALE))
    table.setStyle(TableStyle(commands))
    return table


def figure(path: Path) -> Image:
    reader = ImageReader(str(path))
    width, height = reader.getSize()
    display_width = A4[0] - 100
    display_height = display_width * height / width
    return Image(str(path), width=display_width, height=display_height)


def build() -> None:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    diagrams = [
        "customer-journey.png", "implemented-architecture.png", "data-flow.png", "local-topology.png",
        "entity-relationships.png", "dataset-lifecycle.png", "production-topology.png", "billing-lifecycle.png",
    ]
    story = []
    i = 0
    diagram_index = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line == "```mermaid":
            i += 1
            while i < len(lines) and lines[i].strip() != "```":
                i += 1
            i += 1
            story.append(KeepTogether([Spacer(1, 6), figure(ASSETS / diagrams[diagram_index]), Spacer(1, 9)]))
            diagram_index += 1
            continue
        if line.startswith("```"):
            i += 1
            code = []
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            story.append(Paragraph('<font face="Courier">' + html.escape("\n".join(code)).replace("\n", "<br/>") + "</font>", styles["body"]))
            continue
        if line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s|:-]+\|$", lines[i + 1]):
            table_lines = []
            while i < len(lines) and lines[i].startswith("|"):
                table_lines.append(lines[i])
                i += 1
            story.append(make_table(table_lines))
            story.append(Spacer(1, 8))
            continue
        heading = re.match(r"^(#{1,4})\s+(.+)$", line)
        if heading:
            level = len(heading.group(1))
            key = "title" if level == 1 else f"h{min(level - 1, 3)}"
            heading_flowable = Paragraph(html.escape(heading.group(2)), styles[key])
            next_index = i + 1
            while next_index < len(lines) and not lines[next_index].strip():
                next_index += 1
            if next_index < len(lines) and lines[next_index].strip() == "```mermaid":
                closing = next_index + 1
                while closing < len(lines) and lines[closing].strip() != "```":
                    closing += 1
                story.append(KeepTogether([heading_flowable, Spacer(1, 6),
                                           figure(ASSETS / diagrams[diagram_index]), Spacer(1, 9)]))
                diagram_index += 1
                i = closing + 1
                continue
            story.append(heading_flowable)
            i += 1
            continue
        ordered = re.match(r"^(\d+)\.\s+(.+)$", line)
        bullet = re.match(r"^-\s+(.+)$", line)
        if ordered:
            story.append(Paragraph(f"{ordered.group(1)}. {inline(ordered.group(2))}", styles["list"]))
        elif bullet:
            story.append(Paragraph(f"&#8226; {inline(bullet.group(1))}", styles["list"]))
        else:
            story.append(Paragraph(inline(line.replace("  ", " ")), styles["body"]))
        i += 1
    if diagram_index != len(diagrams):
        raise RuntimeError(f"Used {diagram_index} diagrams, expected {len(diagrams)}")
    BlueprintDoc(OUTPUT).build(story)
    print(OUTPUT)


if __name__ == "__main__":
    build()
