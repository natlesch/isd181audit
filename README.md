# Brainerd ISD 181 income and spending

Local tracker of published income and spending for Brainerd Public Schools, Independent School District No. 181. Fiscal years end June 30.

The headline is the audited governmental-fund statement for FY2025, with FY2024 beside it. The government-wide statement, the statutory budget form, and the FY2027 adopted budget answer different questions. They are shown separately and are not added to the headline.

FY2027 beginning balances are the adopted-budget figures. They are not set from FY2026 statutory ending balances. Building construction happens to match; that match is a published coincidence, not a rollforward.

## Run

From the repo root, with the Python 3 standard library only:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m isd181
```

The second command writes `output/income-spending.md` and `output/income-spending.html`. It does not use the network.

The three-page overview is separate. It reads the same ledger and needs reportlab, which the tracker does not import:

```bash
PYTHONPATH=src uv run --with reportlab python scripts/build_overview_pdf.py
```

That writes `output/isd181-overview.pdf`.

`scripts/hooks/pre-push` runs gitleaks before a push. Install it once per clone:

```bash
mkdir -p .git/hooks
cp scripts/hooks/pre-push .git/hooks/pre-push
chmod +x .git/hooks/pre-push
```

Numbers come from `data/lines.csv`, `data/context.csv`, and `data/sources.csv`. Those files are the ledger. Do not add internal service, the custodial fund, government-wide expenses, or statutory inflows into the governmental-fund headline.

The finest actual split in the report is fund by function, then the federal-award schedule. The FY2025 revised budget adds a restriction split. That split is budget, not actual. Federal-award expenditures and the restriction budget are not added to the headline.
