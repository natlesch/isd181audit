"""Load the ISD 181 ledger and sum one picture at a time."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path


class LedgerError(Exception):
    """A selection cannot be summed, or the ledger cannot be read."""


@dataclass(frozen=True)
class Line:
    line_id: str
    statement: str
    fiscal_year: int
    basis: str
    fund: str
    measure: str
    category: str
    stage: str
    amount: int | None
    amount_state: str
    role: str
    headline: str
    source_id: str
    locator: str
    note: str


@dataclass(frozen=True)
class Context:
    metric: str
    fiscal_year: int
    amount: Decimal
    unit: str
    source_id: str
    locator: str
    detail: str


@dataclass(frozen=True)
class Source:
    source_id: str
    title: str
    filename: str
    sha256: str
    retrieved: str
    publisher: str
    loaded: str
    url: str


_LINE_FIELDS = (
    "line_id",
    "statement",
    "fiscal_year",
    "basis",
    "fund",
    "measure",
    "category",
    "stage",
    "amount",
    "amount_state",
    "role",
    "headline",
    "source_id",
    "locator",
    "note",
)

_CONTEXT_FIELDS = (
    "metric",
    "fiscal_year",
    "amount",
    "unit",
    "source_id",
    "locator",
    "detail",
)

_SOURCE_FIELDS = (
    "source_id",
    "title",
    "filename",
    "sha256",
    "retrieved",
    "publisher",
    "loaded",
    "url",
)


def find_root(start: Path | None = None) -> Path:
    """Walk upward from this module, or from start, until data/lines.csv exists."""
    if start is None:
        current = Path(__file__).resolve().parent
    else:
        current = Path(start).resolve()
        if current.is_file():
            current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "data" / "lines.csv").is_file():
            return candidate
    raise LedgerError("data/lines.csv not found")


def load_lines(root: Path | None = None) -> list[Line]:
    return [_line_from_row(row) for row in _read_csv(root, "lines.csv")]


def load_context(root: Path | None = None) -> list[Context]:
    rows = []
    for row in _read_csv(root, "context.csv"):
        _require_fields(row, _CONTEXT_FIELDS, "context.csv")
        rows.append(
            Context(
                metric=row["metric"],
                fiscal_year=int(row["fiscal_year"]),
                amount=Decimal(row["amount"]),
                unit=row["unit"],
                source_id=row["source_id"],
                locator=row["locator"],
                detail=row["detail"],
            )
        )
    return rows


def load_sources(root: Path | None = None) -> list[Source]:
    rows = []
    for row in _read_csv(root, "sources.csv"):
        _require_fields(row, _SOURCE_FIELDS, "sources.csv")
        rows.append(
            Source(
                source_id=row["source_id"],
                title=row["title"],
                filename=row["filename"],
                sha256=row["sha256"],
                retrieved=row["retrieved"],
                publisher=row["publisher"],
                loaded=row["loaded"],
                url=row["url"],
            )
        )
    return rows


def select(lines, **equals):
    """Return lines whose fields match every keyword exactly."""
    chosen = []
    for line in lines:
        if all(getattr(line, key) == value for key, value in equals.items()):
            chosen.append(line)
    return chosen


def sum_amounts(lines) -> int:
    """Sum values and dashes.

    Blank amounts cannot be treated as zero. A sum that mixes basis,
    statement, measure, or fiscal year is rejected, including a mix of
    revenue and expense or of inflow and expenditure.
    """
    rows = list(lines)
    if not rows:
        raise LedgerError("cannot sum an empty selection")
    if any(row.amount_state == "blank" or row.amount is None for row in rows):
        raise LedgerError("cannot sum a blank amount")
    for field in ("basis", "statement", "measure", "fiscal_year"):
        values = {getattr(row, field) for row in rows}
        if len(values) > 1:
            shown = ", ".join(str(value) for value in sorted(values, key=str))
            raise LedgerError(f"selection has more than one {field}: {shown}")
    total = 0
    for row in rows:
        if row.amount_state not in ("value", "dash"):
            raise LedgerError(
                f"{row.line_id} has amount_state {row.amount_state!r}"
            )
        total += row.amount
    return total


def headline(lines, fiscal_year, measure) -> int:
    """Sum one governmental-fund headline measure.

    headline=yes also marks beginning balances, ending balances, other
    financing, net change, and excess. Those rows share a statement with
    revenue and expenditure, so this function takes one measure and refuses
    to add them together.
    """
    chosen = select(
        lines,
        statement="gov_funds",
        headline="yes",
        fiscal_year=fiscal_year,
        measure=measure,
    )
    for line in chosen:
        if line.fund == "internal" or line.basis == "memo_excluded":
            raise LedgerError("headline includes an excluded fund")
    return sum_amounts(chosen)


def require_single(lines, line_id) -> Line:
    matches = [line for line in lines if line.line_id == line_id]
    if len(matches) != 1:
        raise LedgerError(
            f"expected one line for {line_id}, found {len(matches)}"
        )
    return matches[0]


def _read_csv(root: Path | None, name: str) -> list[dict]:
    path = find_root(root) / "data" / name
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _require_fields(row: dict, fields: tuple[str, ...], name: str) -> None:
    missing = [field for field in fields if field not in row]
    if missing:
        raise LedgerError(f"{name} missing columns: {', '.join(missing)}")


def _line_from_row(row: dict) -> Line:
    _require_fields(row, _LINE_FIELDS, "lines.csv")
    state = row["amount_state"]
    raw = row["amount"]
    line_id = row["line_id"]
    if state == "blank":
        if raw != "":
            raise LedgerError(f"blank line {line_id} has amount {raw!r}")
        amount: int | None = None
    elif state == "dash":
        if raw not in ("", "0"):
            raise LedgerError(f"dash line {line_id} has amount {raw!r}")
        amount = 0
    elif state == "value":
        try:
            amount = int(raw)
        except (TypeError, ValueError) as exc:
            raise LedgerError(f"bad amount for {line_id}: {raw!r}") from exc
    else:
        raise LedgerError(f"unknown amount_state {state!r} on {line_id}")
    try:
        year = int(row["fiscal_year"])
    except ValueError as exc:
        raise LedgerError(f"bad fiscal_year for {line_id}") from exc
    return Line(
        line_id=line_id,
        statement=row["statement"],
        fiscal_year=year,
        basis=row["basis"],
        fund=row["fund"],
        measure=row["measure"],
        category=row["category"],
        stage=row["stage"],
        amount=amount,
        amount_state=state,
        role=row["role"],
        headline=row["headline"],
        source_id=row["source_id"],
        locator=row["locator"],
        note=row["note"],
    )
