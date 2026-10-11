"""Build a short overview PDF from the ISD 181 ledger.

The tracker itself stays on the Python standard library. This script needs
reportlab, which is not imported by python3 -m isd181.

    PYTHONPATH=src uv run --with reportlab python scripts/build_overview_pdf.py
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    KeepTogether,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from isd181.ledger import find_root, headline, load_lines, load_sources, select
from isd181.report import dollars, money


NAVY = colors.HexColor("#1f3a5f")
RULE = colors.HexColor("#d5dbe3")
ZEBRA = colors.HexColor("#f4f7fb")
MUTED = colors.HexColor("#243140")


def _one(lines, **equals) -> int:
    found = select(lines, **equals)
    if len(found) != 1:
        raise SystemExit(f"expected one line for {equals}, found {len(found)}")
    return found[0].amount


def _cell(text: str, style) -> Paragraph:
    return Paragraph(text, style)


def _table(rows, widths, numeric_from: int = 1, total_row: bool = True):
    style_commands = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ALIGN", (numeric_from, 1), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LINEBELOW", (0, 1), (-1, -2), 0.25, RULE),
    ]
    if total_row:
        style_commands.extend([
            ("LINEABOVE", (0, -1), (-1, -1), 0.6, NAVY),
            ("BACKGROUND", (0, -1), (-1, -1), ZEBRA),
        ])
    table = Table(rows, colWidths=widths, repeatRows=1)
    table.setStyle(TableStyle(style_commands))
    return table


def _heading(text: str, style) -> KeepTogether:
    return KeepTogether([Paragraph(text, style), Spacer(1, 4)])


def build(root: Path) -> Path:
    lines = load_lines(root)
    sources = load_sources(root)
    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=10,
        leading=13,
        textColor=MUTED,
        spaceAfter=8,
    )
    head = ParagraphStyle(
        "Head",
        parent=styles["Heading2"],
        fontName="Times-Bold",
        fontSize=12,
        leading=15,
        textColor=NAVY,
        spaceBefore=8,
        spaceAfter=2,
    )
    title = ParagraphStyle(
        "DocTitle",
        parent=styles["Title"],
        fontName="Times-Bold",
        fontSize=18,
        leading=22,
        textColor=NAVY,
        spaceAfter=2,
    )
    subtitle = ParagraphStyle(
        "Subtitle",
        parent=body,
        fontName="Times-Italic",
        fontSize=11,
        leading=14,
        textColor=NAVY,
        spaceAfter=8,
    )
    th = ParagraphStyle(
        "Th",
        parent=body,
        fontName="Times-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        spaceAfter=0,
    )
    td = ParagraphStyle(
        "Td",
        parent=body,
        fontName="Times-Roman",
        fontSize=8.5,
        leading=11,
        textColor=MUTED,
        spaceAfter=0,
    )
    td_right = ParagraphStyle("TdRight", parent=td, alignment=TA_RIGHT)
    small = ParagraphStyle(
        "Small",
        parent=body,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#3d4c5c"),
    )
    bullet = ParagraphStyle(
        "BulletBody",
        parent=body,
        spaceAfter=2,
    )

    revenue = headline(lines, 2025, "revenue")
    expenditure = headline(lines, 2025, "expenditure")
    change = headline(lines, 2025, "net_change")
    ending = headline(lines, 2025, "ending_balance")
    prior_expenditure = headline(lines, 2024, "expenditure")
    general_revenue = _one(
        lines, statement="gov_funds", fiscal_year=2025, fund="general",
        measure="revenue", category="total",
    )
    general_expenditure = _one(
        lines, statement="gov_funds", fiscal_year=2025, fund="general",
        measure="expenditure", category="total",
    )
    general_other = _one(
        lines, statement="gov_funds", fiscal_year=2025, fund="general",
        measure="other_financing", category="total",
    )
    general_change = _one(
        lines, statement="gov_funds", fiscal_year=2025, fund="general",
        measure="net_change", category="total",
    )
    general_end = _one(
        lines, statement="gov_funds", fiscal_year=2025, fund="general",
        measure="ending_balance", category="total",
    )

    story = [
        Paragraph("Brainerd Public Schools, ISD 181", title),
        Paragraph(
            "Income and spending overview. Fiscal year ended June 30, 2025.",
            subtitle,
        ),
        Paragraph(
            "Independent School District No. 181, Brainerd, Minnesota. "
            "District number 0181-01. This overview reads the local ledger. "
            "The signed audit remains the record for the audited figures. "
            "Amounts are whole dollars.",
            body,
        ),
        Paragraph("The audited governmental funds", head),
        Paragraph(
            f"Governmental funds took in {dollars(revenue)} and spent "
            f"{dollars(expenditure)}. Fund balances fell by {dollars(abs(change))}, "
            f"to {dollars(ending)}. FY2024 spending on the same statement was "
            f"{dollars(prior_expenditure)}. That year is a single total, with no "
            "fund split.",
            body,
        ),
        Paragraph(
            f"The general fund took in {dollars(general_revenue)} and spent "
            f"{dollars(general_expenditure)}. Other financing sources of "
            f"{dollars(general_other)} are not revenue. The general fund balance "
            f"fell by {dollars(abs(general_change))}, to {dollars(general_end)}.",
            body,
        ),
        Paragraph("These totals are different questions", head),
        Paragraph(
            "The figures below answer different questions. They are not added "
            "to the governmental-fund spending of "
            f"{dollars(expenditure)}.",
            body,
        ),
    ]

    pictures = [
        [
            _cell("<b>Picture</b>", th),
            _cell("<b>In</b>", th),
            _cell("<b>Out</b>", th),
        ],
        [
            _cell("Audited governmental funds, FY2025", td),
            _cell(money(revenue), td_right),
            _cell(money(expenditure), td_right),
        ],
        [
            _cell("Full-accrual government-wide, FY2025", td),
            _cell(money(_one(
                lines, statement="gw", fiscal_year=2025,
                measure="revenue", category="total",
            )), td_right),
            _cell(money(_one(
                lines, statement="gw", fiscal_year=2025,
                measure="expense", category="total",
            )), td_right),
        ],
        [
            _cell("Statutory form, FY2025 inflows and outflows", td),
            _cell(money(_one(
                lines, statement="statutory", fiscal_year=2025,
                fund="published_total", measure="inflow",
            )), td_right),
            _cell(money(_one(
                lines, statement="statutory", fiscal_year=2025,
                fund="published_total", measure="outflow",
            )), td_right),
        ],
        [
            _cell("FY2027 adopted budget, referendum page", td),
            _cell(money(_one(
                lines, statement="fy2027", fiscal_year=2027,
                fund="published_total", measure="revenue",
            )), td_right),
            _cell(money(_one(
                lines, statement="fy2027", fiscal_year=2027,
                fund="published_total", measure="expenditure",
            )), td_right),
        ],
    ]
    story.append(_table(
        pictures, [3.5 * inch, 1.7 * inch, 1.7 * inch], total_row=False
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Government-wide outflows are expenses, not expenditures. Debt "
        "principal paid is an expenditure in the funds and is not an expense "
        "government-wide. Statutory inflows are revenues and transfers in. "
        "The FY2027 budget includes the OPEB trust. Unrestricted government-wide "
        "net position is negative $32,942,414. That figure is not spendable cash.",
        small,
    ))

    functions = (
        ("regular_instruction", "Regular instruction"),
        ("special_education", "Special education"),
        ("sites_and_buildings", "Sites and buildings"),
        ("debt_principal", "Debt principal"),
        ("debt_interest", "Debt interest"),
        ("pupil_support", "Pupil support"),
        ("food_service", "Food service"),
        ("instructional_support", "Instructional support"),
        ("community_service", "Community service"),
        ("administration", "Administration"),
        ("district_support", "District support"),
        ("vocational", "Vocational"),
        ("capital_outlay", "Capital outlay"),
        ("fiscal", "Fiscal and other fixed-cost programs"),
    )
    function_rows = [[
        _cell("<b>Function</b>", th),
        _cell("<b>FY2025 expenditures</b>", th),
    ]]
    for category, label in functions:
        amount = _one(
            lines, statement="gov_funds", fiscal_year=2025, fund="all",
            measure="expenditure", category=category,
        )
        function_rows.append([
            _cell(label, td),
            _cell(money(amount), td_right),
        ])
    function_rows.append([
        _cell("<b>Total</b>", td),
        _cell(f"<b>{money(expenditure)}</b>", td_right),
    ])
    story.append(Paragraph("Where the governmental funds spent the year", head))
    story.append(Paragraph(
        "Every row is audited governmental-fund spending. Regular instruction "
        "and special education are entirely in the general fund. The split "
        "rows are sites and buildings ($9,716,466 general and $810,873 "
        "building construction), capital outlay ($891,609 general, $516,995 "
        "building, and $16,771 community service), debt principal ($1,491,536 "
        "general and $8,260,000 debt service), and debt interest ($352,447 "
        "general and $8,119,226 debt service).",
        body,
    ))
    story.append(_table(function_rows, [4.6 * inch, 2.3 * inch]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "The signed audit does not publish salaries inside a function, "
        "spending by school, or UFARS program codes. The line-item UFARS "
        "file is not a public download.",
        small,
    ))

    objects = (
        ("salaries", "Salaries"),
        ("benefits", "Employee benefits"),
        ("purchased_services", "Purchased services"),
        ("supplies", "Supplies and materials"),
        ("capital", "Capital expenditures"),
        ("other", "Other expenditures"),
    )
    object_rows = [[
        _cell("<b>General fund object</b>", th),
        _cell("<b>FY2025</b>", th),
        _cell("<b>FY2024</b>", th),
    ]]
    for category, label in objects:
        object_rows.append([
            _cell(label, td),
            _cell(money(_one(
                lines, statement="gf_objects", fiscal_year=2025, fund="general",
                measure="expenditure", category=category,
            )), td_right),
            _cell(money(_one(
                lines, statement="gf_objects", fiscal_year=2024, fund="general",
                measure="expenditure", category=category,
            )), td_right),
        ])
    object_rows.append([
        _cell("<b>Total</b>", td),
        _cell(f"<b>{money(general_expenditure)}</b>", td_right),
        _cell(f"<b>{money(_one(lines, statement='gf_objects', fiscal_year=2024, fund='general', measure='expenditure', category='total'))}</b>", td_right),
    ])
    story.append(Paragraph("General fund, by object", head))
    story.append(Paragraph(
        "These objects are not crossed with the functions above. Salaries and "
        "benefits are the largest share of general-fund spending.",
        body,
    ))
    story.append(_table(object_rows, [3.2 * inch, 1.85 * inch, 1.85 * inch]))

    programs = [
        line for line in select(
            lines, statement="sefa", fiscal_year=2025, measure="expenditure",
            role="component",
        )
    ]
    programs.sort(key=lambda line: line.amount or 0, reverse=True)
    sefa_total = _one(
        lines, statement="sefa", fiscal_year=2025, category="total",
        measure="expenditure",
    )
    federal_revenue = _one(
        lines, statement="gov_funds", fiscal_year=2025, fund="all",
        measure="revenue", category="federal",
    )
    labels = {
        "usda_nslp_cash": "National School Lunch, cash",
        "ed_title_i_a": "Title I, Part A",
        "ed_esser_iii": "ESSER III, 90 percent",
        "usda_breakfast": "School Breakfast",
        "ed_sped": "Special education, through Paul Bunyan",
        "usda_commodities_nslp": "National School Lunch, commodities",
        "ed_title_ii": "Title II, Part A",
        "ed_title_i_d": "Title I, Part D",
    }
    award_rows = [[
        _cell("<b>Largest federal award lines</b>", th),
        _cell("<b>FY2025</b>", th),
    ]]
    for line in programs:
        if line.category not in labels:
            continue
        award_rows.append([
            _cell(labels[line.category], td),
            _cell(money(line.amount), td_right),
        ])
    award_rows.append([
        _cell("<b>All federal award expenditures</b>", td),
        _cell(f"<b>{money(sefa_total)}</b>", td_right),
    ])
    story.append(Paragraph("Federal awards already inside that spending", head))
    story.append(Paragraph(
        f"The schedule of federal awards sums to {dollars(sefa_total)}. "
        f"Governmental-fund federal revenue is {dollars(federal_revenue)}. "
        f"The schedule is {dollars(sefa_total - federal_revenue)} above that "
        "revenue. That difference is not assigned to a program. These lines "
        "are already inside the governmental-fund total. They are not added "
        "again. The eight lines below are the largest awards. They do not "
        "add to the schedule total. Smaller awards are in the full report. "
        "The schedule prints $3,978,695 for Assistance Listing 84.425. "
        "The two current-year lines, ESSER III and learning loss, sum to "
        "$805,172. The larger figure is not added.",
        body,
    ))
    story.append(_table(award_rows, [4.6 * inch, 2.3 * inch]))

    restrictions = [
        line for line in select(
            lines, statement="budget_restriction", fiscal_year=2025,
            fund="general", measure="expenditure", stage="final",
            role="component",
        )
        if (line.amount or 0) >= 1_000_000
    ]
    restrictions.sort(key=lambda line: line.amount or 0, reverse=True)
    restriction_labels = {
        "unassigned": "Unassigned",
        "basic_skills": "Basic skills",
        "ltfm": "Long-term facilities maintenance",
        "alternative_learning": "Alternative learning",
        "operating_capital": "Operating capital",
        "assigned_qcomp": "Q Comp",
        "staff_development": "Staff development",
        "learning_development": "Learning and development",
    }
    budget_total = _one(
        lines, statement="budget_restriction", fiscal_year=2025, fund="general",
        measure="expenditure", category="total",
    )
    budget_rows = [[
        _cell("<b>General fund restriction, revised budget</b>", th),
        _cell("<b>FY2025 budget</b>", th),
    ]]
    for line in restrictions:
        budget_rows.append([
            _cell(restriction_labels[line.category], td),
            _cell(money(line.amount), td_right),
        ])
    budget_rows.append([
        _cell("<b>Total general fund budget</b>", td),
        _cell(f"<b>{money(budget_total)}</b>", td_right),
    ])
    story.append(Paragraph("FY2025 revised budget, not actual spending", head))
    story.append(Paragraph(
        "The June 2025 budget book splits the revised general-fund budget by "
        f"restriction. Rows of $1 million or more are shown. They add, with "
        f"the smaller rows, to {dollars(budget_total)}, which matches the "
        "audit's final general-fund expenditure budget. Actual general-fund "
        f"spending was {dollars(general_expenditure)}. The signed audit does "
        "not publish actual spending inside these restrictions.",
        body,
    ))
    story.append(_table(budget_rows, [4.6 * inch, 2.3 * inch]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "The same book prints a FY2024 table it labels audited. That table's "
        "general-fund expenditures are $93,663,493. The signed audit's "
        "general-fund expenditures are $93,767,873. The $104,380 difference "
        "is not repaired, and those FY2024 rows are not in the ledger.",
        small,
    ))

    story.append(Paragraph("What this overview leaves in the full report", head))
    bullets = [
        "Food service, community service, building construction, and debt service are each shown with their own revenue, spending, and ending balance.",
        "The statutory form separates general-fund restricted and other accounts. Those inflows are not audited revenue.",
        "Internal service spending of $17,074,153 is excluded. Those charges are already inside the other funds. The custodial fund is money held for others.",
        "The OPEB irrevocable trust is outside the headline. Its audited expenditures are $2,445,486.",
        "FY2027 beginning balances are not set from FY2026 statutory ending balances. Building construction's matching $1,565,062 is a published coincidence.",
        "The long markdown and HTML reports list every loaded line, the federal award schedule, and the full restriction budget.",
    ]
    story.append(ListFlowable(
        [ListItem(Paragraph(item, bullet), leftIndent=12) for item in bullets],
        bulletType="bullet",
        start="•",
        leftIndent=16,
        bulletFontName="Times-Roman",
        bulletFontSize=10,
        spaceBefore=0,
        spaceAfter=4,
    ))

    source_rows = [[
        _cell("<b>Source</b>", th),
        _cell("<b>SHA-256 prefix</b>", th),
        _cell("<b>Loaded</b>", th),
    ]]
    for source in sources:
        source_rows.append([
            _cell(source.title, td),
            _cell(source.sha256[:12], td),
            _cell("yes" if source.loaded == "yes" else "no", td),
        ])
    story.append(Paragraph("Sources", head))
    story.append(Paragraph(
        "Retrieved October 11, 2026. The prefix is the first 12 characters "
        "of the SHA-256 of the file in this repository. The PDF wins if a "
        "text extract disagrees with it.",
        body,
    ))
    story.append(_table(
        source_rows, [4.3 * inch, 1.5 * inch, 1.1 * inch],
        numeric_from=2, total_row=False,
    ))

    out = root / "output" / "isd181-overview.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)

    def _page(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.rect(0, letter[1] - 28, letter[0], 28, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Times-Roman", 8)
        canvas.drawString(0.7 * inch, letter[1] - 18, "Brainerd Public Schools  ·  ISD 181")
        canvas.drawRightString(letter[0] - 0.7 * inch, letter[1] - 18, "Public-records overview")
        canvas.setFillColor(MUTED)
        canvas.setFont("Times-Roman", 8)
        canvas.drawString(0.7 * inch, 0.42 * inch, "Not a substitute for the signed audit.")
        canvas.drawRightString(
            letter[0] - 0.7 * inch, 0.42 * inch, f"Page {doc.page}"
        )
        canvas.restoreState()

    SimpleDocTemplate(
        str(out),
        pagesize=letter,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.62 * inch,
        bottomMargin=0.62 * inch,
        title="Brainerd ISD 181 income and spending overview",
        author="ISD 181 public-records ledger",
    ).build(story, onFirstPage=_page, onLaterPages=_page)
    return out


if __name__ == "__main__":
    destination = build(find_root())
    print(destination)
