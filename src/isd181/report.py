"""Render the board report from the ledger, in markdown and standalone HTML."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from isd181.ledger import (
    LedgerError,
    headline,
    select,
    sum_amounts,
)


@dataclass(frozen=True)
class Heading:
    level: int
    text: str


@dataclass(frozen=True)
class Paragraph:
    text: str


@dataclass(frozen=True)
class Table:
    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    numeric: tuple[bool, ...]


@dataclass(frozen=True)
class Warning:
    title: str
    paragraphs: tuple[str, ...]


def headline_sentences(lines) -> list[str]:
    """The two lead sentences. Each measure is summed on its own."""
    revenue = headline(lines, 2025, "revenue")
    expenditure = headline(lines, 2025, "expenditure")
    change = headline(lines, 2025, "net_change")
    ending = headline(lines, 2025, "ending_balance")
    general_revenue = _only(
        lines, statement="gov_funds", fiscal_year=2025, fund="general",
        measure="revenue", category="total",
    ).amount
    general_expenditure = _only(
        lines, statement="gov_funds", fiscal_year=2025, fund="general",
        measure="expenditure", category="total",
    ).amount
    general_other = _only(
        lines, statement="gov_funds", fiscal_year=2025, fund="general",
        measure="other_financing", category="total",
    ).amount
    general_change = _only(
        lines, statement="gov_funds", fiscal_year=2025, fund="general",
        measure="net_change", category="total",
    ).amount
    governmental = (
        f"Governmental funds took in {dollars(revenue)} and spent "
        f"{dollars(expenditure)} in FY2025. Fund balances {_movement(change)}, "
        f"to {dollars(ending)}."
    )
    general = (
        f"The general fund took in {dollars(general_revenue)} and spent "
        f"{dollars(general_expenditure)}. Other financing sources of "
        f"{dollars(general_other)} are not revenue. The general fund balance "
        f"{_movement(general_change)}."
    )
    return [governmental, general]


def render_markdown(lines, context, sources) -> str:
    parts = []
    for block in _document(lines, context, sources):
        if isinstance(block, Heading):
            parts.append(f"{'#' * block.level} {block.text}")
        elif isinstance(block, Paragraph):
            parts.append(block.text)
        elif isinstance(block, Warning):
            parts.append(f"## {block.title}")
            parts.extend(block.paragraphs)
        elif isinstance(block, Table):
            parts.append(_markdown_table(block))
        else:
            raise LedgerError(f"unknown block {type(block)!r}")
    return "\n\n".join(parts) + "\n"


def render_html(lines, context, sources) -> str:
    body = []
    for block in _document(lines, context, sources):
        if isinstance(block, Heading):
            tag = f"h{block.level}"
            body.append(f"<{tag}>{_esc(block.text)}</{tag}>")
        elif isinstance(block, Paragraph):
            body.append(f"<p>{_esc(block.text)}</p>")
        elif isinstance(block, Warning):
            inner = "".join(f"<p>{_esc(text)}</p>" for text in block.paragraphs)
            body.append(
                f'<aside class="warning"><h2>{_esc(block.title)}</h2>{inner}</aside>'
            )
        elif isinstance(block, Table):
            body.append(_html_table(block))
        else:
            raise LedgerError(f"unknown block {type(block)!r}")
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>Brainerd Public Schools, ISD 181 — Income and spending</title>\n"
        f"<style>\n{_CSS}</style>\n"
        "</head>\n"
        "<body>\n"
        "<main>\n"
        + "\n".join(body)
        + "\n</main>\n</body>\n</html>\n"
    )


def _document(lines, context, sources):
    _check_pictures(lines)
    governmental, general = headline_sentences(lines)
    blocks = [
        Heading(1, "Brainerd Public Schools, ISD 181"),
        Paragraph(
            "Income and spending from public reports. Fiscal years end June 30. "
            "Independent School District No. 181, Brainerd, Minnesota. "
            "District number 0181-01."
        ),
        Paragraph(governmental),
        Paragraph(general),
        Warning(
            "These totals are different questions",
            (
                "Full-accrual government-wide revenue was "
                f"{dollars(_gw(lines, 2025, 'revenue').amount)} and expenses were "
                f"{dollars(_gw(lines, 2025, 'expense').amount)}. "
                "The statutory form's all-funds inflows were "
                f"{dollars(_stat_published(lines, 2025, 'inflow').amount)} and "
                "outflows were "
                f"{dollars(_stat_published(lines, 2025, 'outflow').amount)}. "
                "The FY2027 adopted budget shows revenue of "
                f"{dollars(_fy2027_published(lines, 'revenue').amount)} and "
                "expenditures of "
                f"{dollars(_fy2027_published(lines, 'expenditure').amount)}. "
                "They are not added to the headline.",
                "Adding these pictures double-counts activity and mixes the "
                "fund basis, the full-accrual basis, and the statutory gross basis.",
            ),
        ),
    ]
    blocks.extend(_governmental_funds(lines))
    blocks.extend(_spending_by_function(lines))
    blocks.extend(_spending_by_fund_and_function(lines))
    blocks.extend(_federal_awards(lines))
    blocks.extend(_revenue_by_source(lines))
    blocks.extend(_general_fund_detail(lines))
    blocks.extend(_general_fund_budget(lines))
    blocks.extend(_restriction_budget(lines))
    blocks.extend(_other_fund_budgets(lines))
    blocks.extend(_statutory(lines))
    blocks.extend(_fy2027(lines))
    blocks.extend(_government_wide(lines))
    blocks.extend(_excluded(lines))
    blocks.extend(_context_section(context))
    blocks.extend(_sources_section(sources))
    return blocks


def _governmental_funds(lines):
    funds = (
        ("general", "General"),
        ("food", "Food service"),
        ("community", "Community service"),
        ("building", "Building construction"),
        ("debt", "Debt service"),
    )
    measures = (
        "revenue",
        "expenditure",
        "other_financing",
        "net_change",
        "ending_balance",
    )
    rows = []
    for fund, label in funds:
        cells = [label]
        for measure in measures:
            cells.append(_money_line(_fund_total(lines, 2025, fund, measure)))
        rows.append(tuple(cells))
    total_2025 = ["FY2025 total"]
    total_2024 = ["FY2024 total"]
    for measure in measures:
        # The FY2025 statement total is headline=no so it is not added to the funds.
        total_2025.append(_money_line(_fund_total(lines, 2025, "all", measure)))
        total_2024.append(_money_line(_fund_total(lines, 2024, "all", measure)))
    rows.append(tuple(total_2025))
    rows.append(tuple(total_2024))
    debt_end = _fund_total(lines, 2025, "debt", "ending_balance").amount
    return [
        Heading(2, "1. Governmental funds by fund"),
        Paragraph(
            "FY2025 audited governmental funds. FY2024 is the statement's "
            "summarized total beside the total row. That column has no fund "
            "split. The FY2025 total is the published statement total. It is "
            "not added on top of the five funds."
        ),
        Table(
            (
                "Fund",
                "Revenue",
                "Expenditures",
                "Other financing",
                "Net change",
                "Ending balance",
            ),
            tuple(rows),
            (False, True, True, True, True, True),
        ),
        Paragraph(
            "Other financing sources are not revenue. For each of the five funds, "
            "beginning balance plus revenue minus expenditures plus other financing "
            "equals the ending balance. Debt service includes OPEB debt service. "
            f"Its ending balance of {dollars(debt_end)} equals statutory debt "
            "service plus statutory OPEB debt service."
        ),
    ]


def _spending_by_function(lines):
    order = (
        ("administration", "Administration"),
        ("district_support", "District support"),
        ("regular_instruction", "Regular instruction"),
        ("vocational", "Vocational"),
        ("special_education", "Special education"),
        ("instructional_support", "Instructional support"),
        ("pupil_support", "Pupil support"),
        ("sites_and_buildings", "Sites and buildings"),
        ("fiscal", "Fiscal and other fixed-cost programs"),
        ("food_service", "Food service"),
        ("community_service", "Community service"),
        ("capital_outlay", "Capital outlay"),
        ("debt_principal", "Debt principal (fund-basis principal)"),
        ("debt_interest", "Debt interest"),
    )
    rows = []
    for category, label in order:
        current = _component(
            lines, statement="gov_funds", fiscal_year=2025, fund="all",
            measure="expenditure", category=category,
        )
        prior = _component(
            lines, statement="gov_funds", fiscal_year=2024, fund="all",
            measure="expenditure", category=category,
        )
        rows.append((label, money(current.amount), money(prior.amount)))
    rows.append((
        "Total",
        money(_fund_total(lines, 2025, "all", "expenditure").amount),
        money(_fund_total(lines, 2024, "all", "expenditure").amount),
    ))
    return [
        Heading(2, "2. Where governmental-fund spending went"),
        Paragraph(
            "Expenditures by function. Debt principal is fund-basis principal. "
            "It is an expenditure of the funds and is not an expense on the "
            "government-wide statement."
        ),
        Table(
            ("Function", "FY2025", "FY2024"),
            tuple(rows),
            (False, True, True),
        ),
    ]


_FUND_FUNCTIONS = (
    ("administration", "Administration"),
    ("district_support", "District support"),
    ("regular_instruction", "Regular instruction"),
    ("vocational", "Vocational"),
    ("special_education", "Special education"),
    ("instructional_support", "Instructional support"),
    ("pupil_support", "Pupil support"),
    ("sites_and_buildings", "Sites and buildings"),
    ("fiscal", "Fiscal and other fixed-cost programs"),
    ("food_service", "Food service"),
    ("community_service", "Community service"),
    ("capital_outlay", "Capital outlay"),
    ("debt_principal", "Debt principal (fund-basis principal)"),
    ("debt_interest", "Debt interest"),
)

_CROSS_FUNDS = (
    ("general", "General"),
    ("food", "Food service"),
    ("community", "Community service"),
    ("building", "Building"),
    ("debt", "Debt service"),
)


def _cross_amount(lines, fund, category):
    found = select(
        lines, statement="spend_cross", fiscal_year=2025, fund=fund,
        measure="expenditure", category=category, stage="actual",
    )
    if not found:
        return None
    if len(found) != 1:
        raise LedgerError(f"duplicate spend cell {fund} {category}")
    return found[0].amount


def _spending_by_fund_and_function(lines):
    """The audit's fund columns. Empty cells were dashes on the statement."""
    rows = []
    for category, label in _FUND_FUNCTIONS:
        cells = [label]
        row_sum = 0
        for fund, _name in _CROSS_FUNDS:
            amount = _cross_amount(lines, fund, category)
            row_sum += 0 if amount is None else amount
            cells.append("—" if amount is None else money(amount))
        published = _component(
            lines, statement="gov_funds", fiscal_year=2025, fund="all",
            measure="expenditure", category=category,
        ).amount
        if row_sum != published:
            raise LedgerError(f"{category} cells do not match the function total")
        cells.append(money(published))
        rows.append(tuple(cells))
    total = ["Total"]
    grand = 0
    for fund, _name in _CROSS_FUNDS:
        fund_sum = sum_amounts(select(
            lines, statement="spend_cross", fiscal_year=2025, fund=fund,
            measure="expenditure", stage="actual",
        ))
        audited = _fund_total(lines, 2025, fund, "expenditure").amount
        if fund_sum != audited:
            raise LedgerError(f"{fund} cells do not match the fund total")
        grand += fund_sum
        total.append(money(fund_sum))
    headline_total = _fund_total(lines, 2025, "all", "expenditure").amount
    if grand != headline_total:
        raise LedgerError("fund-by-function cells do not match the headline")
    total.append(money(grand))
    rows.append(tuple(total))
    return [
        Heading(2, "3. Spending by fund and function"),
        Paragraph(
            "Same FY2025 expenditures, split into the fund that recorded them. "
            "A dash means that fund's column was zero on the statement. "
            "Sites and buildings, capital outlay, debt principal, and debt "
            "interest are the rows that sit in more than one fund. These "
            "cells are the statement itself. They are not added on top of "
            "section 2."
        ),
        Table(
            ("Function",)
            + tuple(name for _fund, name in _CROSS_FUNDS)
            + ("Total",),
            tuple(rows),
            (False, True, True, True, True, True, True),
        ),
        Paragraph(
            "The signed audit does not go finer than this for actual spending. "
            "It does not publish salaries inside a function, spending by "
            "school, or UFARS program codes. The general fund's object totals "
            "in section 6 are salaries, benefits, purchased services, supplies, "
            "capital, and other. They are not crossed with these functions."
        ),
    ]


_SEFA = (
    ("usda_commodities_nslp", "National School Lunch, commodities (10.555)"),
    ("usda_breakfast", "School Breakfast (10.553)"),
    ("usda_nslp_cash", "National School Lunch, cash (10.555)"),
    ("usda_snack", "After-school snack (10.555)"),
    ("usda_summer", "Summer Food Service (10.559)"),
    ("usda_ffvp", "Fresh Fruit and Vegetable (10.582)"),
    ("usda_state_admin", "Child-nutrition state admin (10.560)"),
    ("usda_farm_to_school", "Farm to School (10.569)"),
    ("ed_adult_basic", "Adult Basic Education (84.002)"),
    ("ed_nonexclusionary", "Non-exclusionary discipline (84.027)"),
    ("ed_title_ii", "Title II, Part A (84.367)"),
    ("ed_title_vii", "Title VII, Indian Education (84.060)"),
    ("ed_title_i_a", "Title I, Part A (84.010)"),
    ("ed_title_i_d", "Title I, Part D (84.010)"),
    ("ed_esser_iii", "ESSER III, 90 percent (84.425U)"),
    ("ed_esser_learning_loss", "ESSER III, learning loss (84.425U)"),
    ("ed_sped", "Special education, Paul Bunyan (84.027)"),
    ("ed_sped_low_incidence", "Low incidence, Paul Bunyan (84.027)"),
    ("ed_sped_cspd", "CSPD, Paul Bunyan (84.027)"),
    ("ed_perkins_vocational", "Carl Perkins vocational (84.048)"),
    ("ed_perkins_cte", "Carl Perkins career and technical (84.048)"),
)


def _sefa_amount(lines, category) -> int:
    return _component(
        lines, statement="sefa", fiscal_year=2025, fund="all",
        measure="expenditure", category=category,
    ).amount


def _federal_awards(lines):
    rows = []
    program_sum = 0
    usda = 0
    education = 0
    for category, label in _SEFA:
        amount = _sefa_amount(lines, category)
        program_sum += amount
        if category.startswith("usda_"):
            usda += amount
        elif category.startswith("ed_"):
            education += amount
        else:
            raise LedgerError(f"unclassified federal program {category}")
        rows.append((label, money(amount)))
    total = _only(
        lines, statement="sefa", fiscal_year=2025, category="total",
        measure="expenditure",
    ).amount
    if program_sum != total or usda + education != total:
        raise LedgerError("federal award lines do not match the schedule total")
    federal_revenue = _component(
        lines, statement="gov_funds", fiscal_year=2025, fund="all",
        measure="revenue", category="federal",
    ).amount
    food_federal = _only(
        lines, statement="food_rsi", fiscal_year=2025, fund="food",
        measure="revenue", category="federal", stage="actual",
    ).amount
    general_federal = _only(
        lines, statement="gf_sources", fiscal_year=2025, fund="general",
        measure="revenue", category="federal",
    ).amount
    community_federal = _only(
        lines, statement="community_rsi", fiscal_year=2025, fund="community",
        measure="revenue", category="federal", stage="actual",
    ).amount
    gap = total - federal_revenue
    if food_federal != usda:
        raise LedgerError("food-service federal revenue does not match Agriculture")
    if education - community_federal - general_federal != gap:
        raise LedgerError("the federal-award gap is not the education remainder")
    esser = _sefa_amount(lines, "ed_esser_iii") + _sefa_amount(
        lines, "ed_esser_learning_loss"
    )
    rows.append(("Total federal award expenditures", money(total)))
    return [
        Heading(2, "4. Federal award expenditures"),
        Paragraph(
            "Schedule of Expenditures of Federal Awards for the year ended "
            "June 30, 2025. These are modified-accrual expenditures of federal "
            "awards. They are a subset of district spending, already inside "
            "the fund expenditures above. They are not added to the headline, "
            "and they are not federal revenue."
        ),
        Paragraph(
            f"Schedule expenditures are {dollars(total)}. Governmental-fund "
            f"federal revenue is {dollars(federal_revenue)}. The schedule is "
            f"{dollars(gap)} above that revenue. Food-service federal revenue "
            f"equals the Agriculture total of {dollars(usda)}. General-fund "
            f"federal revenue is {dollars(general_federal)} and community-service "
            f"federal revenue is {dollars(community_federal)}. Together those "
            f"two are {dollars(gap)} below the Education total. That "
            f"{dollars(gap)} is not assigned to a program."
        ),
        Table(
            ("Federal program", "FY2025 expenditures"),
            tuple(rows),
            (False, True),
        ),
        Paragraph(
            "The schedule's pass-through total is a dash. The child-nutrition "
            f"cluster, Title I, and the special-education cluster foot to the "
            "lines above. The schedule also prints a total of $3,978,695 for "
            f"Assistance Listing 84.425. The two current-year 84.425 lines sum "
            f"to {dollars(esser)}. The larger figure is not a current-year "
            "expenditure line and is not added."
        ),
    ]


def _revenue_by_source(lines):
    order = (
        ("property_taxes", "Property taxes"),
        ("investment_earnings", "Investment earnings"),
        ("other", "Other local revenue"),
        ("state", "State"),
        ("federal", "Federal"),
    )
    rows = []
    amounts = {}
    for category, label in order:
        current = _component(
            lines, statement="gov_funds", fiscal_year=2025, fund="all",
            measure="revenue", category=category,
        )
        prior = _component(
            lines, statement="gov_funds", fiscal_year=2024, fund="all",
            measure="revenue", category=category,
        )
        amounts[(2025, category)] = current.amount
        amounts[(2024, category)] = prior.amount
        rows.append((label, money(current.amount), money(prior.amount)))
    rows.append((
        "Total",
        money(_fund_total(lines, 2025, "all", "revenue").amount),
        money(_fund_total(lines, 2024, "all", "revenue").amount),
    ))
    federal_drop = amounts[(2024, "federal")] - amounts[(2025, "federal")]
    state_rise = amounts[(2025, "state")] - amounts[(2024, "state")]
    return [
        Heading(2, "5. Where governmental-fund revenue came from"),
        Paragraph(
            f"Federal revenue fell by {dollars(federal_drop)}, from "
            f"{dollars(amounts[(2024, 'federal')])} in FY2024 to "
            f"{dollars(amounts[(2025, 'federal')])} in FY2025. State revenue "
            f"rose by {dollars(state_rise)}, from "
            f"{dollars(amounts[(2024, 'state')])} to "
            f"{dollars(amounts[(2025, 'state')])}."
        ),
        Table(
            ("Source", "FY2025", "FY2024"),
            tuple(rows),
            (False, True, True),
        ),
    ]


def _general_fund_detail(lines):
    source_order = (
        ("property_taxes", "Property taxes"),
        ("investment_earnings", "Investment earnings"),
        ("other", "Other"),
        ("state", "State"),
        ("federal", "Federal"),
    )
    object_order = (
        ("salaries", "Salaries"),
        ("benefits", "Benefits"),
        ("purchased_services", "Purchased services"),
        ("supplies", "Supplies"),
        ("capital", "Capital"),
        ("other", "Other"),
    )
    financing_order = (
        ("lease_liability", "Lease liability"),
        ("insurance_proceeds", "Insurance proceeds"),
        ("sale_of_capital_assets", "Sale of capital assets"),
    )
    source_rows = []
    general_sources = {}
    for category, label in source_order:
        current = _only(
            lines, statement="gf_sources", fiscal_year=2025, fund="general",
            measure="revenue", category=category,
        )
        prior = _only(
            lines, statement="gf_sources", fiscal_year=2024, fund="general",
            measure="revenue", category=category,
        )
        general_sources[(2025, category)] = current.amount
        general_sources[(2024, category)] = prior.amount
        source_rows.append((label, money(current.amount), money(prior.amount)))
    source_rows.append((
        "Total revenue",
        money(_only(
            lines, statement="gf_sources", fiscal_year=2025, category="total",
            measure="revenue",
        ).amount),
        money(_only(
            lines, statement="gf_sources", fiscal_year=2024, category="total",
            measure="revenue",
        ).amount),
    ))
    object_rows = []
    for category, label in object_order:
        current = _only(
            lines, statement="gf_objects", fiscal_year=2025, fund="general",
            measure="expenditure", category=category,
        )
        prior = _only(
            lines, statement="gf_objects", fiscal_year=2024, fund="general",
            measure="expenditure", category=category,
        )
        object_rows.append((label, money(current.amount), money(prior.amount)))
    object_rows.append((
        "Total expenditures",
        money(_only(
            lines, statement="gf_objects", fiscal_year=2025, category="total",
            measure="expenditure",
        ).amount),
        money(_only(
            lines, statement="gf_objects", fiscal_year=2024, category="total",
            measure="expenditure",
        ).amount),
    ))
    pay = sum_amounts([
        _only(
            lines, statement="gf_objects", fiscal_year=2025,
            measure="expenditure", category="salaries",
        ),
        _only(
            lines, statement="gf_objects", fiscal_year=2025,
            measure="expenditure", category="benefits",
        ),
    ])
    spending = _fund_total(lines, 2025, "general", "expenditure").amount
    financing_rows = []
    for category, label in financing_order:
        line = _only(
            lines, statement="gov_funds", fiscal_year=2025, fund="general",
            measure="other_financing", category=category,
        )
        financing_rows.append((label, money(line.amount)))
    financing_rows.append((
        "Total other financing sources",
        money(_fund_total(lines, 2025, "general", "other_financing").amount),
    ))
    begin = _fund_total(lines, 2025, "general", "beginning_balance").amount
    end = _fund_total(lines, 2025, "general", "ending_balance").amount
    change = _fund_total(lines, 2025, "general", "net_change").amount
    excess = _fund_total(lines, 2025, "general", "excess").amount
    unassigned = _only(
        lines, statement="gov_funds", fiscal_year=2025, fund="general",
        measure="ending_balance", category="unassigned",
    )
    return [
        Heading(2, "6. General fund sources and objects"),
        Paragraph(
            f"The general fund balance {_movement(change)}, from {dollars(begin)} "
            f"to {dollars(end)}. {_shortfall(excess)} That shortfall is not the "
            "same thing as the change in fund balance, because other financing "
            "sources are not revenue."
        ),
        Paragraph(
            f"Federal general-fund revenue fell from "
            f"{dollars(general_sources[(2024, 'federal')])} in FY2024 to "
            f"{dollars(general_sources[(2025, 'federal')])} in FY2025. State "
            f"revenue rose from {dollars(general_sources[(2024, 'state')])} to "
            f"{dollars(general_sources[(2025, 'state')])}. Salaries and benefits "
            f"were {dollars(pay)} of {dollars(spending)} of FY2025 general-fund "
            "spending."
        ),
        Table(
            ("Source", "FY2025", "FY2024"),
            tuple(source_rows),
            (False, True, True),
        ),
        Table(
            ("Object", "FY2025", "FY2024"),
            tuple(object_rows),
            (False, True, True),
        ),
        Paragraph(
            "Other financing sources are not revenue. They are not relabeled "
            "as transfers."
        ),
        Table(
            ("Other financing sources (not revenue)", "FY2025"),
            tuple(financing_rows),
            (False, True),
        ),
        Paragraph(
            f"Unassigned fund balance is {dollars(unassigned.amount)}. That is "
            f"part of the {dollars(end)} general-fund ending balance, not a "
            "second reserve. UFARS unassigned is "
            f"{dollars(_cited_amount(unassigned.note, 'UFARS unassigned is'))}."
        ),
    ]


def _general_fund_budget(lines):
    revenue_order = (
        ("property_taxes", "Property taxes"),
        ("investment_earnings", "Investment earnings"),
        ("other", "Other"),
        ("state", "State"),
        ("federal", "Federal"),
        ("total", "Total revenue"),
    )
    expenditure_order = (
        ("administration", "Administration"),
        ("district_support", "District support"),
        ("regular_instruction", "Regular instruction"),
        ("vocational", "Vocational"),
        ("special_education", "Special education"),
        ("instructional_support", "Instructional support"),
        ("pupil_support", "Pupil support"),
        ("sites_and_buildings", "Sites and buildings"),
        ("fiscal", "Fiscal and other fixed-cost programs"),
        ("capital_outlay", "Capital outlay"),
        ("debt_principal", "Debt principal (fund-basis principal)"),
        ("debt_interest", "Debt interest"),
        ("total", "Total expenditures"),
    )
    rows = []
    for category, label in revenue_order:
        rows.append(_budget_row(lines, "gf_rsi", "general", "revenue", category, label))
    for category, label in expenditure_order:
        rows.append(_budget_row(
            lines, "gf_rsi", "general", "expenditure", category, label
        ))
    rows.append(_budget_row(
        lines, "gf_rsi", "general", "excess", "total",
        "Excess of revenue over expenditures",
    ))
    rows.append(_budget_row(
        lines, "gf_rsi", "general", "other_financing", "total",
        "Other financing sources (not revenue)",
    ))
    rows.append(_budget_row(
        lines, "gf_rsi", "general", "net_change", "total", "Net change",
    ))
    final_gap = _only(
        lines, statement="gf_rsi", fiscal_year=2025, measure="excess",
        category="total", stage="final",
    ).amount
    actual_gap = _only(
        lines, statement="gf_rsi", fiscal_year=2025, measure="excess",
        category="total", stage="actual",
    ).amount
    original_gap = _only(
        lines, statement="gf_rsi", fiscal_year=2025, measure="excess",
        category="total", stage="original",
    ).amount
    return [
        Heading(2, "7. General fund budget versus actual, FY2025"),
        Paragraph(
            f"The final budget expected expenditures to exceed revenue by "
            f"{dollars(final_gap)}. The actual gap was {dollars(actual_gap)}. "
            f"The original budget gap was {dollars(original_gap)}. Other "
            "financing sources were budgeted at zero and are not revenue."
        ),
        Table(
            ("", "Original budget", "Final budget", "Actual"),
            tuple(rows),
            (False, True, True, True),
        ),
    ]


_RESTRICTIONS = {
    "general": (
        ("unassigned", "Unassigned"),
        ("assigned_other", "Assigned, all other"),
        ("assigned_qcomp", "Assigned, Q Comp"),
        ("nonspendable", "Nonspendable"),
        ("restricted", "Restricted"),
        ("alternative_learning", "Restricted, alternative learning"),
        ("basic_skills", "Restricted, basic skills"),
        ("english_learner", "Restricted, English learner"),
        ("gifted", "Restricted, gifted and talented"),
        ("learning_development", "Restricted, learning and development"),
        ("literacy_aid", "Restricted, literacy aid"),
        ("literacy_incentive", "Restricted, literacy incentive aid"),
        ("ltfm", "Restricted, long-term facilities maintenance"),
        ("medical_assistance", "Restricted, medical assistance"),
        ("operating_capital", "Restricted, operating capital"),
        ("safe_schools", "Restricted, safe schools"),
        ("school_library", "Restricted, school library aid"),
        ("staff_development", "Restricted, staff development"),
        ("student_activities", "Restricted, student activities"),
        ("student_support", "Restricted, student support personnel"),
        ("read_act", "Restricted, READ Act teacher compensation"),
    ),
    "food": (
        ("nonspendable", "Nonspendable"),
        ("restricted", "Restricted"),
    ),
    "community": (
        ("nonspendable", "Nonspendable"),
        ("restricted", "Restricted, other"),
        ("adult_basic", "Restricted, adult basic education"),
        ("community_service", "Restricted, community service"),
        ("ecfe", "Restricted, early childhood family education"),
        ("school_readiness", "Restricted, school readiness"),
    ),
    "building": (
        ("nonspendable", "Nonspendable"),
        ("restricted", "Restricted"),
    ),
}


def _budget_piece(lines, fund, category):
    return _only(
        lines, statement="budget_restriction", fiscal_year=2025, fund=fund,
        measure="expenditure", category=category, stage="final",
    ).amount


def _restriction_rows(lines, fund):
    rows = []
    piece_sum = 0
    for category, label in _RESTRICTIONS[fund]:
        amount = _budget_piece(lines, fund, category)
        piece_sum += amount
        rows.append((label, money(amount)))
    printed = _budget_piece(lines, fund, "total")
    if piece_sum != printed:
        raise LedgerError(f"{fund} restriction rows do not match the book total")
    rows.append(("Total", money(printed)))
    return tuple(rows), printed


def _restriction_budget(lines):
    general_rows, general_total = _restriction_rows(lines, "general")
    food_rows, food_total = _restriction_rows(lines, "food")
    community_rows, community_total = _restriction_rows(lines, "community")
    building_rows, building_total = _restriction_rows(lines, "building")
    debt_total = _budget_piece(lines, "debt", "total")
    audit_general = _only(
        lines, statement="gf_rsi", fiscal_year=2025, fund="general",
        measure="expenditure", category="total", stage="final",
    ).amount
    audit_food = _only(
        lines, statement="food_rsi", fiscal_year=2025, fund="food",
        measure="expenditure", category="total", stage="final",
    ).amount
    audit_community = _only(
        lines, statement="community_rsi", fiscal_year=2025, fund="community",
        measure="expenditure", category="total", stage="final",
    ).amount
    if (general_total, food_total, community_total) != (
        audit_general, audit_food, audit_community
    ):
        raise LedgerError("restriction totals do not match the audit final budgets")
    signed_2024 = _only(
        lines, statement="gf_objects", fiscal_year=2024, fund="general",
        measure="expenditure", category="total",
    ).amount
    opeb_budget = _budget_piece(lines, "opeb_trust", "total")
    opeb_actual = _only(
        lines, statement="memo", fund="opeb_trust", measure="expenditure",
    ).amount
    return [
        Heading(2, "8. FY2025 revised budget by restriction"),
        Paragraph(
            "June 2025 budget book, first revised budget for FY2025. These "
            "are budgeted expenditures, not actual spending. The general fund, "
            "food service, and community service totals match the audit's "
            f"final budgets of {dollars(audit_general)}, {dollars(audit_food)}, "
            f"and {dollars(audit_community)}. The signed audit does not publish "
            "actual spending inside these restrictions."
        ),
        Paragraph(
            "The same book prints a FY2024 table it labels audited. That "
            f"table's general-fund expenditures are $93,663,493. The signed "
            f"audit's general-fund expenditures are {dollars(signed_2024)}. "
            "The $104,380 difference is not repaired, and those FY2024 rows "
            "are not loaded."
        ),
        Heading(3, "General fund"),
        Table(
            ("Restriction", "Revised budget expenditures"),
            general_rows,
            (False, True),
        ),
        Heading(3, "Food service, community service, and building construction"),
        Table(
            ("Food service", "Revised budget expenditures"),
            food_rows,
            (False, True),
        ),
        Table(
            ("Community service", "Revised budget expenditures"),
            community_rows,
            (False, True),
        ),
        Table(
            ("Building construction", "Revised budget expenditures"),
            building_rows,
            (False, True),
        ),
        Paragraph(
            f"Debt-service revised-budget expenditures are {dollars(debt_total)}. "
            "The audit does not publish a debt-service budget-to-actual "
            "schedule. This figure is the budget book, not actual debt-service "
            f"spending of {dollars(_fund_total(lines, 2025, 'debt', 'expenditure').amount)}."
        ),
        Paragraph(
            f"The OPEB irrevocable trust's revised-budget expenditures are "
            f"{dollars(opeb_budget)}. Audited UFARS expenditures for that trust "
            f"are {dollars(opeb_actual)}. The trust is outside the "
            "governmental-fund headline. Neither figure is added to district "
            "spending."
        ),
    ]


def _other_fund_budgets(lines):
    blocks = [
        Heading(2, "9. Food service and community service budget versus actual"),
        Paragraph(
            "Shorter view of the FY2025 audit's budget-to-actual schedules. "
            "These are audited revenue and expenditures, not statutory inflows."
        ),
    ]
    for statement, fund, title in (
        ("food_rsi", "food", "Food service"),
        ("community_rsi", "community", "Community service"),
    ):
        revenue_categories = _categories(
            lines, statement=statement, fund=fund, measure="revenue"
        )
        rows = [
            _budget_row(lines, statement, fund, "revenue", category, label)
            for category, label in revenue_categories
        ]
        rows.append(_budget_row(
            lines, statement, fund, "expenditure", "total", "Total expenditures"
        ))
        blocks.append(Heading(3, title))
        blocks.append(Table(
            ("", "Original budget", "Final budget", "Actual"),
            tuple(rows),
            (False, True, True, True),
        ))
    return blocks


def _statutory(lines):
    fund_order = (
        ("general_restricted", "General, restricted"),
        ("general_other", "General, other"),
        ("food", "Food service"),
        ("community", "Community service"),
        ("building", "Building construction"),
        ("debt", "Debt service"),
        ("trust", "Trust"),
        ("opeb_revocable", "OPEB revocable trust"),
        ("opeb_irrevocable", "OPEB irrevocable trust"),
        ("opeb_debt", "OPEB debt service"),
        ("internal", "Internal service"),
        ("published_total", "Printed total (not the headline)"),
    )
    present = {
        line.fund for line in select(lines, statement="statutory")
    }
    if present != {fund for fund, _label in fund_order}:
        raise LedgerError("statutory fund list does not match the ledger")
    measures = (
        (2025, "beginning_balance"),
        (2025, "inflow"),
        (2025, "outflow"),
        (2025, "ending_balance"),
        (2026, "inflow"),
        (2026, "outflow"),
        (2026, "ending_balance"),
    )
    rows = []
    for fund, label in fund_order:
        cells = [label]
        for year, measure in measures:
            cells.append(_money_line(_statutory_line(lines, year, fund, measure)))
        rows.append(tuple(cells))
    restricted_begin = _statutory_line(lines, 2025, "general_restricted", "beginning_balance")
    other_begin = _statutory_line(lines, 2025, "general_other", "beginning_balance")
    combined_begin = sum_amounts([restricted_begin, other_begin])
    combined_in = sum_amounts([
        _statutory_line(lines, 2025, "general_restricted", "inflow"),
        _statutory_line(lines, 2025, "general_other", "inflow"),
    ])
    combined_out = sum_amounts([
        _statutory_line(lines, 2025, "general_restricted", "outflow"),
        _statutory_line(lines, 2025, "general_other", "outflow"),
    ])
    combined_end = sum_amounts([
        _statutory_line(lines, 2025, "general_restricted", "ending_balance"),
        _statutory_line(lines, 2025, "general_other", "ending_balance"),
    ])
    audited_end = _fund_total(lines, 2025, "general", "ending_balance").amount
    internal_position = _only(
        lines, statement="memo", fund="internal", measure="ending_balance",
        category="net_position",
    ).amount
    published_begin = _stat_published(lines, 2025, "beginning_balance").amount
    published_in = _stat_published(lines, 2025, "inflow").amount
    published_out = _stat_published(lines, 2025, "outflow").amount
    published_end = _stat_published(lines, 2025, "ending_balance").amount
    internal_begin = _statutory_line(
        lines, 2025, "internal", "beginning_balance"
    ).amount
    roll_gap = published_begin + published_in - published_out - published_end
    if roll_gap != internal_begin:
        raise LedgerError("statutory rollforward gap is not the internal beginning")
    begin_gap = published_begin - _sum_printed(lines, 2025, "beginning_balance")
    out_gap = published_out - _sum_printed(lines, 2025, "outflow")
    if begin_gap != 1 or out_gap != -1:
        raise LedgerError("FY2025 statutory footing is not the published $1 gap")
    for measure in ("inflow", "outflow", "ending_balance"):
        if _stat_published(lines, 2026, measure).amount != _sum_printed(lines, 2026, measure):
            raise LedgerError(f"FY2026 statutory {measure} does not foot")
    crosswalk = _audit_statutory_crosswalk(lines)
    return [
        Heading(2, "10. Statutory form, FY2025 actual and FY2026 budget"),
        Paragraph(
            "Form ED-00110-48, dated April 30, 2026. Amounts here are inflows "
            "and outflows, not audited revenue and expenditures. General fund "
            "rows are the restricted slice and the other slice. Their gross-up "
            "is not relabeled as transfers. Income and spending for the general "
            "fund come from the audit. These statutory slices stay on this page."
        ),
        Paragraph(
            f"Statutory general-fund inflows, restricted plus other, are "
            f"{dollars(combined_in)}. Statutory outflows are {dollars(combined_out)}. "
            f"The statutory ending balance is {dollars(combined_end)}, which is "
            f"{dollars(combined_end - audited_end)} above the audited ending "
            f"balance of {dollars(audited_end)}. The net change matches the audit "
            f"within {dollars(combined_end - audited_end)}. The statutory beginning "
            f"balance of those two slices is {dollars(combined_begin)}, the same "
            "figure as the audited general-fund beginning balance."
        ),
        Table(
            (
                "Fund",
                "FY2025 beginning",
                "FY2025 inflows",
                "FY2025 outflows",
                "FY2025 ending",
                "FY2026 inflows",
                "FY2026 outflows",
                "FY2026 ending",
            ),
            tuple(rows),
            (False, True, True, True, True, True, True, True),
        ),
        Paragraph(
            "Internal service activity is not reported. The ending balance is "
            f"a dash. The audit net position is {dollars(internal_position)} and "
            "is excluded. The dash is not that net position. The printed total "
            "is not the headline. The FY2025 printed total does not roll forward "
            "because the internal-service beginning balance of "
            f"{dollars(internal_begin)} is in the beginning total while activity "
            "is not reported and the ending balance is a dash. FY2025 beginning "
            "is $1 above the sum of the printed fund rows. FY2025 outflows are "
            "$1 below the sum of the printed fund rows. FY2026 columns foot exactly."
        ),
        Paragraph(
            "The OPEB irrevocable trust is inside this statutory total and "
            "outside the governmental-fund headline. Contributions can already "
            "be an expenditure of another fund. Food service and community "
            "service match the statutory form within $1. Building construction "
            "matches to the dollar. Those $1 gaps are the audit-to-UFARS "
            "differences. Both figures are shown. Neither is adjusted. Revenue "
            "in the audit debt-service column, which includes OPEB debt service, "
            "is $2 above statutory debt-service inflow plus statutory OPEB "
            "debt-service inflow."
        ),
        Table(
            (
                "Crosswalk (not a combined total)",
                "Audited",
                "Statutory",
                "Audited minus statutory",
            ),
            tuple(crosswalk),
            (False, True, True, True),
        ),
    ]


def _fy2027(lines):
    """Show both budget vintages. Do not set any FY2027 beginning from FY2026."""
    fund_order = (
        ("general", "General"),
        ("food", "Food service"),
        ("community", "Community service"),
        ("building", "Building construction"),
        ("debt", "Debt service"),
        ("opeb_trust", "OPEB trust (outside governmental funds)"),
        ("opeb_debt", "OPEB debt service"),
        ("published_total", "Printed total (includes the OPEB trust; not the headline)"),
    )
    present = {line.fund for line in select(lines, statement="fy2027")}
    if present != {fund for fund, _label in fund_order}:
        raise LedgerError("FY2027 fund list does not match the ledger")
    measures = (
        "beginning_balance",
        "revenue",
        "expenditure",
        "excess",
        "ending_balance",
    )
    rows = []
    for fund, label in fund_order:
        cells = [label]
        for measure in measures:
            # Beginning balances are the FY2027 adopted lines only.
            cells.append(_money_line(_fy2027_line(lines, fund, measure)))
        rows.append(tuple(cells))
    published_revenue = _fy2027_published(lines, "revenue").amount
    published_expenditure = _fy2027_published(lines, "expenditure").amount
    published_excess = _fy2027_published(lines, "excess").amount
    published_end = _fy2027_published(lines, "ending_balance").amount
    comparison = _vintage_comparison(lines)
    return [
        Heading(2, "11. FY2027 adopted budget"),
        Paragraph(
            f"The FY2027 original budget, from the district's operating-referendum "
            f"page snapshotted October 11, 2026, shows revenue of "
            f"{dollars(published_revenue)} and expenditures of "
            f"{dollars(published_expenditure)}. The projected fund-balance decline "
            f"is {dollars(published_excess)}, to {dollars(published_end)}. That "
            "printed total includes the OPEB trust. It is not the governmental-fund "
            "headline, and it is not added to FY2025."
        ),
        Paragraph(
            "FY2027 beginning balances do not chain from the FY2026 statutory "
            "projection. No FY2027 beginning balance is set from a FY2026 "
            "statutory ending balance. Where the two published figures are the "
            "same number, the match is a published coincidence, not a rollforward. "
            "The report does not invent a bond sale or any other cause for a gap."
        ),
        Table(
            (
                "Fund",
                "Beginning balance",
                "Revenue",
                "Expenditures",
                "Excess",
                "Ending balance",
            ),
            tuple(rows),
            (False, True, True, True, True, True),
        ),
        Table(
            (
                "Fund",
                "FY2026 statutory ending",
                "FY2027 adopted beginning",
                "How to read the two figures",
            ),
            tuple(comparison),
            (False, True, True, False),
        ),
        Paragraph(
            "Building construction's FY2027 beginning balance equals the FY2026 "
            "statutory ending balance at "
            f"{dollars(_fy2027_line(lines, 'building', 'beginning_balance').amount)}. "
            "That is a published coincidence, not a rollforward."
        ),
        Paragraph(_opeb_vintage_sentence(lines)),
        Paragraph(_debt_vintage_sentence(lines)),
        Paragraph(
            "The operating levy described on that page is not in this budget. "
            "It would first be available in FY2028 if voters approve it on "
            "November 3, 2026. The \"$15 million over three years\" sentence on "
            "that page is campaign narrative, not a ledger line."
        ),
    ]


def _government_wide(lines):
    rows = [
        (
            "Revenue",
            money(_gw(lines, 2025, "revenue").amount),
            money(_gw(lines, 2024, "revenue").amount),
        ),
        (
            "Expenses",
            money(_gw(lines, 2025, "expense").amount),
            money(_gw(lines, 2024, "expense").amount),
        ),
        (
            "Increase in net position",
            money(_gw(lines, 2025, "increase_in_net_position").amount),
            money(_gw(lines, 2024, "increase_in_net_position").amount),
        ),
        (
            "Beginning net position, as reported",
            money(_gw(lines, 2025, "net_position_beginning", "as_reported").amount),
            money(_gw(lines, 2024, "net_position_beginning", "as_reported").amount),
        ),
        (
            "Accounting-principle change, compensated absences",
            money(_gw(lines, 2025, "accounting_principle_change", "compensated_absences").amount),
            "not restated",
        ),
        (
            "Beginning net position, as restated",
            money(_gw(lines, 2025, "net_position_beginning", "as_restated").amount),
            "not restated",
        ),
        (
            "Ending net position",
            money(_gw(lines, 2025, "net_position_ending").amount),
            money(_gw(lines, 2024, "net_position_ending").amount),
        ),
    ]
    components = (
        ("net_investment_in_capital", "Net investment in capital assets"),
        ("restricted", "Restricted"),
        ("unrestricted", "Unrestricted"),
    )
    component_rows = []
    for category, label in components:
        line = _gw(lines, 2025, "net_position_ending", category)
        component_rows.append((label, money(line.amount)))
    change = _gw(lines, 2025, "accounting_principle_change", "compensated_absences")
    increase = _gw(lines, 2025, "increase_in_net_position").amount
    restated = _gw(lines, 2025, "net_position_beginning", "as_restated").amount
    ending = _gw(lines, 2025, "net_position_ending").amount
    prior_end = _gw(lines, 2024, "net_position_ending").amount
    unrestricted = _gw(lines, 2025, "net_position_ending", "unrestricted").amount
    unassigned = _only(
        lines, statement="gov_funds", fiscal_year=2025, fund="general",
        measure="ending_balance", category="unassigned",
    ).amount
    return [
        Heading(2, "12. Government-wide results"),
        Paragraph(
            "These are full-accrual revenues and expenses from MD&A Table A-2. "
            "They are not fund expenditures. Debt principal paid is an expenditure "
            "in the funds and is not an expense government-wide. Depreciation and "
            "pension measures move the other way, so the accrual result is not "
            "the fund-balance change."
        ),
        Table(
            ("", "FY2025", "FY2024"),
            tuple(rows),
            (False, True, True),
        ),
        Paragraph(
            f"Beginning net position was reduced by {dollars(change.amount)} for "
            "a change in accounting principle for compensated absences. Restated "
            f"beginning net position of {dollars(restated)} plus the increase of "
            f"{dollars(increase)} equals ending net position of {dollars(ending)}. "
            f"FY2024 ending net position of {dollars(prior_end)} is not restated "
            "for that accounting change, so the two ending net positions are not "
            "a clean two-year change."
        ),
        Table(
            ("FY2025 ending net position", "Amount"),
            tuple(component_rows),
            (False, True),
        ),
        Paragraph(
            f"Unrestricted net position is negative {dollars(unrestricted)}. "
            "Unrestricted net position is not spendable cash. The unassigned "
            f"general-fund balance is {dollars(unassigned)}."
        ),
    ]


def _excluded(lines):
    internal_revenue = _only(
        lines, statement="memo", fund="internal", measure="revenue"
    )
    internal_expenditure = _only(
        lines, statement="memo", fund="internal", measure="expenditure"
    )
    internal_position = _only(
        lines, statement="memo", fund="internal", measure="ending_balance"
    )
    custodial_revenue = _only(
        lines, statement="memo", fund="custodial", measure="revenue"
    )
    custodial_expenditure = _only(
        lines, statement="memo", fund="custodial", measure="expenditure"
    )
    ufars_spending = _cited_amount(
        internal_expenditure.note, "UFARS expenditures are"
    )
    ufars_gap = ufars_spending - internal_expenditure.amount
    direction = "higher" if ufars_gap > 0 else "lower"
    return [
        Heading(2, "13. Excluded from district income and spending"),
        Paragraph(
            "Internal service and the custodial fund are excluded. Their charges "
            "or holdings are not a second copy of district income and spending."
        ),
        Paragraph(
            f"Internal service revenue was {dollars(internal_revenue.amount)} and "
            f"expenditures were {dollars(internal_expenditure.amount)}. Net position "
            f"was {dollars(internal_position.amount)}. Those charges are already "
            "inside other funds' spending. The statutory form prints a dash, not "
            f"this net position. UFARS expenditures are {dollars(ufars_spending)}, "
            f"which is {dollars(ufars_gap)} {direction} than the audited figure. "
            "The audited figure is not adjusted. Internal service is excluded "
            "from district spending."
        ),
        Paragraph(
            f"The custodial fund took in {dollars(custodial_revenue.amount)} and "
            f"paid out {dollars(custodial_expenditure.amount)}. That is money held "
            "for others. It is excluded from district income and spending."
        ),
        Paragraph(
            "The OPEB irrevocable trust is shown on the statutory page and in "
            "the FY2027 table, and it is marked as outside the governmental-fund "
            "total. It is not part of the headline."
        ),
    ]


def _context_section(context):
    adm = sorted(
        (row for row in context if row.metric == "adm_for_aid"),
        key=lambda row: row.fiscal_year,
    )
    if [row.fiscal_year for row in adm] != list(range(2016, 2026)):
        raise LedgerError("aid ADM years are not FY2016 through FY2025")
    adm_rows = tuple(
        (f"FY{row.fiscal_year}", published_number(row.amount)) for row in adm
    )
    aid_2016 = _context_amount(context, "adm_for_aid", 2016)
    aid_2025 = _context_amount(context, "adm_for_aid", 2025)
    operating_spend = _context_amount(context, "operating_expenditures", 2025)
    operating_adm = _context_amount(context, "operating_adm", 2025)
    rate = _context_amount(context, "operating_cost_per_adm", 2025)
    gap = (rate * operating_adm - operating_spend).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    debt_begin = _context_amount(context, "long_term_debt_outstanding", 2024)
    debt_issued = _context_amount(context, "long_term_debt_issued", 2025)
    debt_redeemed = _context_amount(context, "long_term_debt_redeemed", 2025)
    debt_end = _context_amount(context, "long_term_debt_outstanding", 2025)
    debt_gap = debt_begin + debt_issued - debt_redeemed - debt_end
    operating_debt = _context_one(context, "statutory_operating_debt", 2025)
    return [
        Heading(2, "14. Context that is not spending"),
        Paragraph(
            "Average daily membership for aid fell from "
            f"{published_number(aid_2016)} in FY2016 to "
            f"{published_number(aid_2025)} in FY2025. None of the figures in "
            "this section are added to income or spending."
        ),
        Table(("Aid ADM", "Students"), adm_rows, (False, True)),
        Paragraph(
            f"The statutory form reports FY2025 operating expenditures of "
            f"${published_number(operating_spend)} and an operating cost of "
            f"${published_number(rate)} per ADM, on {published_number(operating_adm)} "
            "ADM (served, plus tuitioned out, plus adjusted extended). That ADM "
            f"is not the {published_number(aid_2025)} aid ADM. The per-ADM rate "
            "does not multiply back to the expenditure total. The rate times the "
            f"ADM is ${published_number(gap)} above the printed expenditure total "
            "because the rate is rounded."
        ),
        Paragraph(
            f"Long-term debt outstanding on June 30, 2025 is "
            f"${published_number(debt_end)}. Debt outstanding on July 1, 2024 was "
            f"${published_number(debt_begin)}. New issues were "
            f"${published_number(debt_issued)}. Redeemed issues were "
            f"${published_number(debt_redeemed)}. Beginning debt plus new issues "
            f"minus redeemed issues is ${published_number(debt_gap)} above that "
            "printed ending balance. The form spells the row \"Redemeed.\" "
            "Principal paid during the year is already in debt-service expenditures."
        ),
        Paragraph(
            "There is no statutory operating debt. "
            f"{_finish_sentence(operating_debt.detail)}"
        ),
    ]


def _sources_section(sources):
    wanted = ("audit", "statutory", "fy2027", "preliminary")
    by_id = {source.source_id: source for source in sources}
    if set(by_id) != set(wanted):
        raise LedgerError("source list does not match the ledger")
    rows = []
    for source_id in wanted:
        source = by_id[source_id]
        loaded = "loaded" if source.loaded == "yes" else "not loaded"
        rows.append((
            source.title,
            source.filename,
            source.sha256[:12],
            source.retrieved,
            loaded,
        ))
    return [
        Heading(2, "15. Sources"),
        Paragraph(
            "SHA-256 prefixes are the first 12 hexadecimal characters. The "
            "June 2025 preliminary budget is loaded only for its FY2025 "
            "revised-budget expenditures by restriction. The FY2024 restriction "
            "table in that book is not loaded. Its general-fund expenditure "
            "total is $104,380 below the signed audit. The PDF is the source "
            "if a text extract disagrees with it."
        ),
        Table(
            ("Title", "File", "SHA-256 prefix", "Retrieved", "Loaded"),
            tuple(rows),
            (False, False, False, False, False),
        ),
    ]


def _vintage_comparison(lines):
    """Pair published endings with published beginnings. Do not copy one into the other."""
    general_2026 = sum_amounts([
        _statutory_line(lines, 2026, "general_restricted", "ending_balance"),
        _statutory_line(lines, 2026, "general_other", "ending_balance"),
    ])
    general_2027 = _fy2027_line(lines, "general", "beginning_balance").amount
    if general_2027 == general_2026:
        raise LedgerError("FY2027 general beginning unexpectedly equals FY2026")
    rows = [(
        "General fund",
        money(general_2026),
        money(general_2027),
        "do not chain",
    )]
    same_name = (
        ("food", "Food service", "do not chain"),
        ("community", "Community service", "do not chain"),
        ("building", "Building construction", "published coincidence, not a rollforward"),
        ("debt", "Debt service", "unexplained; no cause invented"),
        ("opeb_debt", "OPEB debt service", "do not chain"),
    )
    for fund, label, reading in same_name:
        statutory_ending = _statutory_line(lines, 2026, fund, "ending_balance").amount
        adopted_beginning = _fy2027_line(lines, fund, "beginning_balance").amount
        if fund == "building" and adopted_beginning != statutory_ending:
            raise LedgerError("building figures are not the published coincidence")
        if fund != "building" and adopted_beginning == statutory_ending:
            raise LedgerError(f"{fund} vintages match and would look like a rollforward")
        rows.append((
            label,
            money(statutory_ending),
            money(adopted_beginning),
            reading,
        ))
    opeb_ending = _statutory_line(
        lines, 2026, "opeb_irrevocable", "ending_balance"
    ).amount
    opeb_beginning = _fy2027_line(lines, "opeb_trust", "beginning_balance").amount
    if opeb_beginning == opeb_ending:
        raise LedgerError("refusing to treat the OPEB vintage gap as closed")
    rows.append((
        "OPEB irrevocable trust / OPEB trust",
        money(opeb_ending),
        money(opeb_beginning),
        "unexplained; not reconciled",
    ))
    return rows


def _opeb_vintage_sentence(lines) -> str:
    ending = _statutory_line(lines, 2026, "opeb_irrevocable", "ending_balance").amount
    beginning = _fy2027_line(lines, "opeb_trust", "beginning_balance").amount
    gap = beginning - ending
    return (
        f"The FY2027 OPEB-trust beginning balance is {dollars(beginning)}. "
        f"The FY2026 statutory irrevocable ending balance is {dollars(ending)}. "
        f"The {dollars(gap)} vintage gap is unexplained and is not reconciled."
    )


def _debt_vintage_sentence(lines) -> str:
    ending = _statutory_line(lines, 2026, "debt", "ending_balance").amount
    beginning = _fy2027_line(lines, "debt", "beginning_balance").amount
    return (
        f"Debt service beginning balance on the FY2027 table is {dollars(beginning)}, "
        f"against a FY2026 statutory projected ending balance of {dollars(ending)}. "
        "That gap is unexplained. No bond sale or other cause is invented."
    )


def _audit_statutory_crosswalk(lines):
    rows = []
    pairs = (
        ("Food service revenue / inflow", "food", "revenue", "inflow"),
        ("Food service expenditures / outflow", "food", "expenditure", "outflow"),
        ("Food service ending balance", "food", "ending_balance", "ending_balance"),
        ("Community service revenue / inflow", "community", "revenue", "inflow"),
        ("Community service expenditures / outflow", "community", "expenditure", "outflow"),
        ("Community service ending balance", "community", "ending_balance", "ending_balance"),
        ("Building construction revenue / inflow", "building", "revenue", "inflow"),
        ("Building construction expenditures / outflow", "building", "expenditure", "outflow"),
        ("Building construction ending balance", "building", "ending_balance", "ending_balance"),
    )
    for label, fund, audited_measure, statutory_measure in pairs:
        audited = _fund_total(lines, 2025, fund, audited_measure).amount
        statutory = _statutory_line(lines, 2025, fund, statutory_measure).amount
        rows.append((
            label,
            money(audited),
            money(statutory),
            money(audited - statutory),
        ))
    debt_audited = _fund_total(lines, 2025, "debt", "revenue").amount
    debt_statutory = sum_amounts([
        _statutory_line(lines, 2025, "debt", "inflow"),
        _statutory_line(lines, 2025, "opeb_debt", "inflow"),
    ])
    rows.append((
        "Debt service revenue, audit column vs statutory debt plus OPEB debt",
        money(debt_audited),
        money(debt_statutory),
        money(debt_audited - debt_statutory),
    ))
    debt_end_audited = _fund_total(lines, 2025, "debt", "ending_balance").amount
    debt_end_statutory = sum_amounts([
        _statutory_line(lines, 2025, "debt", "ending_balance"),
        _statutory_line(lines, 2025, "opeb_debt", "ending_balance"),
    ])
    rows.append((
        "Debt service ending balance, audit column vs statutory debt plus OPEB debt",
        money(debt_end_audited),
        money(debt_end_statutory),
        money(debt_end_audited - debt_end_statutory),
    ))
    return rows


def _check_pictures(lines) -> None:
    """Refuse a report that would mix the headline with another picture."""
    for measure in (
        "revenue",
        "expenditure",
        "other_financing",
        "net_change",
        "ending_balance",
        "excess",
        "beginning_balance",
    ):
        published = _fund_total(lines, 2025, "all", measure).amount
        if headline(lines, 2025, measure) != published:
            raise LedgerError(f"FY2025 headline {measure} does not match the statement total")
        if headline(lines, 2024, measure) != _fund_total(lines, 2024, "all", measure).amount:
            raise LedgerError(f"FY2024 headline {measure} does not match the statement total")
    for fund in ("general", "food", "community", "building", "debt"):
        begin = _fund_total(lines, 2025, fund, "beginning_balance").amount
        revenue = _fund_total(lines, 2025, fund, "revenue").amount
        expenditure = _fund_total(lines, 2025, fund, "expenditure").amount
        other = _fund_total(lines, 2025, fund, "other_financing").amount
        ending = _fund_total(lines, 2025, fund, "ending_balance").amount
        if begin + revenue - expenditure + other != ending:
            raise LedgerError(f"{fund} does not roll forward")
    components = select(
        lines, statement="gov_funds", fiscal_year=2025, fund="all",
        measure="expenditure", role="component",
    )
    if sum_amounts(components) != _fund_total(lines, 2025, "all", "expenditure").amount:
        raise LedgerError("FY2025 expenditure components do not match the total")
    revenue = _gw(lines, 2025, "revenue").amount
    expense = _gw(lines, 2025, "expense").amount
    increase = _gw(lines, 2025, "increase_in_net_position").amount
    if revenue - expense != increase:
        raise LedgerError("government-wide revenue minus expense does not match")
    restated = _gw(lines, 2025, "net_position_beginning", "as_restated").amount
    ending = _gw(lines, 2025, "net_position_ending").amount
    if restated + increase != ending:
        raise LedgerError("restated net position does not roll to the ending balance")


def _budget_row(lines, statement, fund, measure, category, label):
    cells = [label]
    for stage in ("original", "final", "actual"):
        line = _only(
            lines, statement=statement, fiscal_year=2025, fund=fund,
            measure=measure, category=category, stage=stage,
        )
        cells.append(_money_line(line))
    return tuple(cells)


def _categories(lines, statement, fund, measure):
    labels = {
        "property_taxes": "Property taxes",
        "investment_earnings": "Investment earnings",
        "other": "Other",
        "state": "State",
        "federal": "Federal",
        "total": "Total revenue",
    }
    found = select(
        lines, statement=statement, fiscal_year=2025, fund=fund,
        measure=measure, stage="actual",
    )
    order = (
        "property_taxes",
        "investment_earnings",
        "other",
        "state",
        "federal",
        "total",
    )
    present = [line.category for line in found]
    if len(present) != len(set(present)):
        raise LedgerError(f"duplicate categories for {statement} {fund} {measure}")
    unknown = [category for category in present if category not in labels]
    if unknown or "total" not in present:
        raise LedgerError(f"unexpected categories for {statement} {fund} {measure}")
    ordered = [category for category in order if category in present]
    return tuple((category, labels[category]) for category in ordered)


def _sum_printed(lines, fiscal_year, measure) -> int:
    """Sum printed statutory fund rows. Blank activity is not printed and is left out."""
    rows = [
        line for line in select(
            lines, statement="statutory", fiscal_year=fiscal_year, measure=measure,
            role="fund",
        )
        if line.amount_state != "blank"
    ]
    return sum_amounts(rows)



def _shortfall(excess: int) -> str:
    if excess < 0:
        return f"Revenue fell short of expenditures by {dollars(excess)}."
    if excess > 0:
        return f"Revenue exceeded expenditures by {dollars(excess)}."
    return "Revenue equaled expenditures."


def _cited_amount(note: str, label: str) -> int:
    match = re.search(rf"{re.escape(label)} (\d+)", note)
    if not match:
        raise LedgerError(f"note does not cite {label}")
    return int(match.group(1))


def _finish_sentence(detail: str) -> str:
    text = detail.strip()
    if text and text[-1] not in ".!?":
        text += "."
    return text


def _movement(amount: int) -> str:
    if amount < 0:
        return f"fell by {dollars(amount)}"
    if amount > 0:
        return f"rose by {dollars(amount)}"
    return f"was unchanged at {dollars(amount)}"


def money(amount: int) -> str:
    if amount < 0:
        return f"({abs(amount):,})"
    return f"{amount:,}"


def dollars(amount: int) -> str:
    return f"${abs(amount):,}"


def _money_line(line) -> str:
    if line.amount_state == "blank":
        return "not reported"
    if line.amount_state == "dash":
        return "—"
    if line.amount is None:
        raise LedgerError(f"{line.line_id} has no amount")
    return money(line.amount)


def published_number(amount: Decimal) -> str:
    negative = amount < 0
    amount = abs(amount)
    text = format(amount, "f")
    if "." in text:
        whole, frac = text.split(".")
        rendered = f"{int(whole):,}.{frac}"
    else:
        rendered = f"{int(text):,}"
    if negative:
        return f"({rendered})"
    return rendered


def _only(lines, **equals):
    found = select(lines, **equals)
    if len(found) != 1:
        raise LedgerError(
            f"expected one line for {equals}, found {len(found)}"
        )
    return found[0]


def _fund_total(lines, fiscal_year, fund, measure):
    return _only(
        lines, statement="gov_funds", fiscal_year=fiscal_year, fund=fund,
        measure=measure, category="total", stage="actual",
    )


def _component(lines, **equals):
    return _only(lines, role="component", stage="actual", **equals)


def _statutory_line(lines, fiscal_year, fund, measure):
    return _only(
        lines, statement="statutory", fiscal_year=fiscal_year, fund=fund,
        measure=measure, category="total",
    )


def _stat_published(lines, fiscal_year, measure):
    return _statutory_line(lines, fiscal_year, "published_total", measure)


def _fy2027_line(lines, fund, measure):
    return _only(
        lines, statement="fy2027", fiscal_year=2027, fund=fund,
        measure=measure, category="total", stage="adopted",
    )


def _fy2027_published(lines, measure):
    return _fy2027_line(lines, "published_total", measure)


def _gw(lines, fiscal_year, measure, category="total"):
    return _only(
        lines, statement="gw", fiscal_year=fiscal_year, fund="governmental_activities",
        measure=measure, category=category, stage="actual",
    )


def _context_one(context, metric, fiscal_year):
    found = [
        row for row in context
        if row.metric == metric and row.fiscal_year == fiscal_year
    ]
    if len(found) != 1:
        raise LedgerError(
            f"expected one context row for {metric} {fiscal_year}, found {len(found)}"
        )
    return found[0]


def _context_amount(context, metric, fiscal_year) -> Decimal:
    return _context_one(context, metric, fiscal_year).amount


def _markdown_table(table: Table) -> str:
    if len(table.numeric) != len(table.headers):
        raise LedgerError("table numeric flags do not match headers")

    def cell(value: str) -> str:
        return value.replace("|", "\\|").replace("\n", " ")

    header = "| " + " | ".join(cell(value) for value in table.headers) + " |"
    separator = "| " + " | ".join("---:" if flag else "---" for flag in table.numeric) + " |"
    body = []
    for row in table.rows:
        if len(row) != len(table.headers):
            raise LedgerError("table row does not match headers")
        body.append("| " + " | ".join(cell(value) for value in row) + " |")
    return "\n".join((header, separator, *body))


def _html_table(table: Table) -> str:
    head = "".join(
        f'<th class="{"num" if flag else "label"}">{_esc(value)}</th>'
        for value, flag in zip(table.headers, table.numeric)
    )
    body = []
    for row in table.rows:
        cells = []
        for value, header, flag in zip(row, table.headers, table.numeric):
            kind = "num" if flag else "label"
            cells.append(
                f'<td class="{kind}" data-label="{_esc(header)}">{_esc(value)}</td>'
            )
        body.append("<tr>" + "".join(cells) + "</tr>")
    return (
        "<table><thead><tr>"
        + head
        + "</tr></thead><tbody>"
        + "".join(body)
        + "</tbody></table>"
    )


def _esc(value: str) -> str:
    return html.escape(value, quote=True)


_CSS = """
body {
  margin: 0;
  background: #fbf8f3;
  color: #1c1a17;
  font-family: "Iowan Old Style", Palatino, "Palatino Linotype", Georgia, "Times New Roman", serif;
  line-height: 1.45;
}
main {
  max-width: 52rem;
  margin: 0 auto;
  padding: 2rem 1.25rem 3rem;
}
h1 { font-size: 1.8rem; line-height: 1.2; margin-bottom: 0.3rem; }
h2 { font-size: 1.25rem; margin-top: 2rem; }
h3 { font-size: 1.05rem; margin: 1.2rem 0 0.2rem; }
p { margin: 0.7rem 0; }
table { border-collapse: collapse; width: 100%; margin: 0.8rem 0 1.2rem; }
th, td { border-bottom: 1px solid #ddd6cc; padding: 0.35rem 0.55rem; vertical-align: top; }
th { font-weight: 600; text-align: left; }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.warning {
  border-left: 4px solid #6b3a2a;
  background: #f3ebe3;
  padding: 0.4rem 1rem;
  margin: 1.2rem 0;
}
@media (max-width: 720px) {
  table, thead, tbody, tr, th, td { display: block; width: auto; }
  thead { position: absolute; left: -9999px; width: 1px; height: 1px; overflow: hidden; }
  tr { margin: 0 0 0.9rem; border: 1px solid #ddd6cc; }
  td { display: flex; justify-content: space-between; gap: 1rem; border: none; text-align: left; }
  td.num { text-align: right; white-space: normal; }
  td::before { content: attr(data-label); font-weight: 600; margin-right: 1rem; }
}
"""
