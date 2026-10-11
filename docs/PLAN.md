# ISD 181 income and spending tracker

Brainerd Public Schools, Independent School District No. 181, Brainerd, Minnesota. Fiscal year ends June 30. District number 0181-01.

This plan is the spec. The ledger files it names are already written and checked against the source PDFs. Implementation follows this document. A bead is finished only when it is closed with evidence.

## Decision

Build a local, source-cited tracker of the district's published income and spending. The headline is the audited governmental-fund statement for FY2025, with FY2024 beside it. Budgets stay in their own sections because they are not the same kind of number.

Do not build a forecast, a monthly board-packet scraper, a UFARS account cube, or a multi-district comparison. UFARS line items are not a public download. The June 2025 preliminary budget is archived and not loaded. It was superseded by the statutory publication and by the later FY2027 budget.

## Three pictures that must not be added together

A reader who adds the district's own published totals will double-count and mix bases. The report leads with one picture and shows the others as different questions.

| Question | Answer for the latest actual year | Source |
| --- | --- | --- |
| What did the governmental funds take in and pay out in FY2025? | Revenue $121,622,792. Expenditures $122,515,320. Fund balance fell $464,821, to $32,634,973. | Audit, statement of revenues, expenditures, and changes in fund balances |
| What did it cost, on a full-accrual basis, to run the district in FY2025? | Revenue $123,211,606. Expenses $119,395,514. Net position rose $3,816,092, after a $3,140,589 reduction of beginning net position for compensated absences. | Audit MD&A Table A-2 |
| What did the statutory budget form publish? | FY2025 inflows $123,774,152 and outflows $125,329,705. FY2026 budget inflows $123,472,372 and outflows $128,854,413. | Form ED-00110-48, dated April 30, 2026 |

The accrual "surplus" is larger because debt principal paid is an expenditure in the funds and is not an expense government-wide, and because depreciation and pension measures move the other way. The statutory inflow is larger because it includes the OPEB irrevocable trust and because the general-fund rows are gross "revenues and transfers in," not audited revenue.

FY2024 governmental funds, from the same statement's summarized column: revenue $122,048,819, expenditures $120,712,127, ending fund balance $33,099,794. That column has no fund split. FY2024 net position of $21,783,798 is not restated for the accounting change, so the two ending net positions are not a clean two-year change.

## General fund, the number people mean by "the budget"

Audited FY2025 general fund:

- Revenue $95,288,614
- Expenditures $95,885,602
- Revenue shortfall $596,988
- Other financing sources $427,707 (lease liability $397,010, insurance proceeds $19,810, sale of assets $10,887). These are not revenue.
- Fund balance fell $169,281, from $22,379,183 to $22,209,902
- Unassigned fund balance $14,159,562. That is part of the $22,209,902, not a second reserve. UFARS unassigned is $14,159,564.

The final FY2025 budget expected expenditures to exceed revenue by $4,203,023. The actual gap was $596,988. Original budget gap was $4,470,249.

Statutory general fund inflows (restricted plus other) are $96,085,225. Statutory outflows are $96,254,503. The net change matches the audit within $3 (statutory ending balance $22,209,905). The form does not name the gross-up. The tracker does not relabel it as transfers. Income and spending for the general fund come from the audit. The statutory slices stay on the statutory page.

Federal general-fund revenue fell from $5,998,877 in FY2024 to $2,937,147 in FY2025. State revenue rose from $77,065,487 to $79,134,309. Salaries and benefits were $75,782,621 of $95,885,602 of FY2025 general-fund spending.

## Funds

Governmental funds in the audit, and the only funds in the headline: General, Food Service, Community Service, Building Construction, and Debt Service. The audit's debt-service column includes OPEB debt service. Ending balance $4,640,413 equals statutory debt service $3,987,751 plus statutory OPEB debt service $652,662. Revenue in that audit column is $2 above the UFARS debt-service revenue plus OPEB debt-service revenue. The compliance table shows that $2.

Food service and community service audited totals match the statutory form within $1. Building construction matches to the dollar. Those $1 gaps are the audit-to-UFARS differences on the compliance table. Store both figures. Do not "fix" either one.

Excluded from district income and spending:

- Internal service. Audit revenue $15,960,024, expenditures $17,074,153, net position $9,558,253. Those charges are already inside other funds' spending. The statutory form prints a beginning balance of $10,672,383, leaves activity blank, and prints a dash for the ending balance. The printed all-funds total therefore does not roll forward, by exactly that $10,672,383 beginning balance. The dash is not the audited net position.
- Custodial fund. Revenue $4,487,467 and expenditures $4,517,751. Money held for others.
- OPEB irrevocable trust. Shown on the statutory page and in the FY2027 table, and marked as outside the governmental-fund total. Contributions can already be an expenditure of another fund.

The statutory printed totals are stored as published totals. FY2025 beginning is $1 above the sum of the printed fund rows. FY2025 outflows are $1 below the sum of the printed fund rows. FY2026 columns foot exactly. The report shows the printed total and says it is not the headline.

## FY2026 and FY2027 do not chain

The FY2026 statutory budget is the April 30, 2026 publication for the year that was then in progress. It is a budget, on the statutory gross basis.

The FY2027 original budget is the table on the district's operating-referendum page, snapshotted October 11, 2026. Revenue $124,059,624. Expenditures $132,895,117. Projected fund balance decline $8,835,493, to $41,784,824. General fund beginning balance on that table is $21,783,758. The FY2026 statutory projected general-fund ending balance is $18,992,229. Debt service beginning balance is $10,678,294 against a statutory projected ending balance of $4,528,744. Building construction happens to match at $1,565,062. The tracker displays both vintages and does not draw a rollforward from one to the other. It does not invent a bond sale or any other cause for the gap.

The operating levy described on that page would first be available in FY2028 if voters approve it on November 3, 2026. It is not a line in the FY2027 budget. The "$15 million over three years" sentence on that page is campaign narrative, not a ledger line.

## Context that is not spending

Average daily membership for aid fell from 6,446 in FY2016 to 5,676 in FY2025 (MD&A Table A-4).

The statutory form reports FY2025 operating expenditures of $101,199,586.45 and an operating cost of $17,477.71 per ADM, on 5,790.21 ADM (served, plus tuitioned out, plus adjusted extended). That ADM is not the 5,676 aid ADM. The rate times the ADM is $24.77 above the printed expenditure total because the rate is rounded. Long-term debt outstanding June 30, 2025 is $206,927,369. Beginning debt plus new issues minus redeemed issues is $1 above that printed ending balance. The form spells the row "Redemeed." None of these are added to income or spending. Principal paid during the year is already in debt-service expenditures.

There is no statutory operating debt. The form's general-fund deficit in excess of 2.5 percent of expenditures is a dash.

## Ledger

`data/lines.csv` is the ledger. 416 lines. Whole dollars, as published. `amount_state` is `value`, `dash` (printed dash, stored as 0), or `blank` (not printed, must not be treated as zero).

Columns: `line_id`, `statement`, `fiscal_year`, `basis`, `fund`, `measure`, `category`, `stage`, `amount`, `amount_state`, `role`, `headline`, `source_id`, `locator`, `note`.

`basis` is one of `governmental_fund`, `government_wide`, `statutory_form`, `adopted_budget`, `memo_excluded`.

`measure` separates the bases on purpose. Statutory rows use `inflow` and `outflow`, not `revenue` and `expenditure`. Government-wide costs use `expense`, not `expenditure`. A sum that requires one measure cannot mix them.

`role` is `fund`, `component`, `total`, `published_total`, or `memo`. Components are parts of a total. Published totals are what the form printed, which can differ by $1 from the rows. Memos are excluded.

`headline=yes` marks the lines that answer "what did the governmental funds take in and pay out." For FY2025 those are the five fund rows. For FY2024 the statement has only the total, so the total is the headline. The FY2025 total row is `headline=no` so it cannot be added on top of the funds.

`data/context.csv` holds ADM, the operating-cost statistic, and long-term debt. `data/sources.csv` holds the file name, SHA-256, retrieval date, and whether the source was loaded.

Source files live in `sources/`. Text extracts of the two loaded PDFs live in `sources/text/` for review. The PDF is the source if a text extract disagrees with it.

## Report

One command from the repo root:

```bash
PYTHONPATH=src python3 -m isd181
```

writes `output/income-spending.md` and `output/income-spending.html`. Standard library only. No network call at runtime.

The page is a document a board member can read. Title: Brainerd Public Schools, ISD 181. Subtitle: Income and spending from public reports. Fiscal years end June 30.

Lead, before any other table:

- Governmental funds took in $121,622,792 and spent $122,515,320 in FY2025. Fund balances fell by $464,821, to $32,634,973.
- The general fund took in $95,288,614 and spent $95,885,602. Other financing sources of $427,707 are not revenue. The general fund balance fell by $169,281.
- A short warning titled "These totals are different questions" names the government-wide pair ($123,211,606 and $119,395,514), the statutory all-funds pair ($123,774,152 and $125,329,705), and the FY2027 budget pair ($124,059,624 and $132,895,117), and says they are not added to the headline.

Then, in order:

1. FY2025 governmental funds by fund, with FY2024 totals beside the total row. Revenue, expenditures, other financing, net change, ending balance.
2. Where FY2025 and FY2024 governmental-fund spending went, by function. Debt principal is labeled fund-basis principal.
3. Where governmental-fund revenue came from, by source, both years. Call out the drop in federal revenue and the rise in state revenue.
4. General fund sources and objects, FY2024 and FY2025.
5. General fund budget versus actual for FY2025. State the final-budget gap of $4,203,023 and the actual gap of $596,988.
6. Food service and community service budget versus actual, shorter.
7. Statutory form, FY2025 actual and FY2026 budget, every fund. General fund labeled as inflows and outflows, not as audited revenue. Internal service shows "not reported" for blank activity and a dash for the ending balance, plus a sentence that the audit net position is $9,558,253 and is excluded. The printed total is shown and labeled as not the headline. Say the FY2025 total does not roll forward because of the internal-service beginning balance.
8. FY2027 adopted budget. Say the beginning balances do not chain from the FY2026 statutory projection. Say the operating levy is not in this budget.
9. Government-wide FY2024 and FY2025. Name the $3,140,589 accounting-principle change and the negative unrestricted net position of $32,942,414. Say unrestricted net position is not spendable cash, and point at the unassigned general-fund balance of $14,159,562.
10. Excluded: internal service and custodial, with their amounts, and why.
11. Context: aid ADM for FY2016 and FY2025, operating cost per ADM with both ADM figures, long-term debt outstanding. A sentence that the per-ADM rate does not multiply back to the expenditure total.
12. Sources: title, file name, SHA-256 prefix (first 12 hex characters), retrieval date, and whether it was loaded.

The June 2025 budget book is loaded only for the FY2025 revised-budget expenditures by restriction. Its FY2024 restriction table is not loaded, because that table's general-fund expenditures are $104,380 below the signed audit.

Money is whole dollars with thousands separators. Negatives are parentheses. Missing statutory amounts render as "not reported." Dashes render as a dash. No chart library and no external assets. The HTML stands alone, uses a readable serif or system font, right-aligns numbers, and stacks tables on a narrow screen.

The markdown file carries the same words and the same numbers. It does not need matching CSS.

## Build contract

Create these files and no others except `output/` and `__pycache__`:

- `src/isd181/__init__.py`
- `src/isd181/__main__.py`
- `src/isd181/ledger.py`
- `src/isd181/report.py`
- `tests/test_ledger.py`
- `tests/test_report.py`
- `README.md`
- `.gitignore` ignoring `__pycache__/`, `*.pyc`, and `.venv/`

Do not modify `data/`, `sources/`, or `docs/PLAN.md`. Do not add dependencies. Do not call the network. Do not run `bd`. Do not commit or push.

`ledger.py` loads the CSVs from the repo root (found by walking up from the module until `data/lines.csv` exists).

- `Line` holds every column. `amount` is `int` or `None`. `dash` becomes amount 0 and `amount_state == "dash"`. `blank` becomes amount `None`.
- `select(lines, **equals)` filters on exact field matches.
- `sum_amounts(lines)` sums values and dashes. It raises `LedgerError` if any line is blank, if the selection is empty, or if the selection contains more than one `basis`, more than one `statement`, more than one `measure`, or more than one `fiscal_year`.
- `headline(lines, fiscal_year, measure)` sums `statement == "gov_funds"`, `headline == "yes"`, that year and measure. It uses `sum_amounts`, so a caller cannot point it at another statement.
- `require_single(lines, line_id)` returns one line or raises.

`report.py` exposes `render_markdown(lines, context, sources) -> str` and `render_html(...) -> str`. `__main__.py` writes both files under `output/` and prints the two headline sentences to stdout.

### Tests that must pass

`tests/test_ledger.py`:

- Headline FY2025 revenue is 121622792 and expenditure is 122515320.
- Headline FY2024 revenue is 122048819 and expenditure is 120712127.
- Adding the internal-service memo revenue of 15960024 to the FY2025 headline raises, because the memo is a different basis and statement. A direct check also asserts that no `headline=yes` line has fund `internal` or basis `memo_excluded`.
- `sum_amounts` on a mix of `revenue` and `expense` raises.
- `sum_amounts` on a selection that includes a blank internal-service inflow raises.
- Each FY2025 fund row rolls: beginning + revenue - expenditure + other financing = ending.
- General fund RSI final excess is -4203023 and actual excess is -596988. Actual net change is -169281.
- Statutory general restricted plus other beginning balance equals 22379183, the audited general-fund beginning balance.
- Statutory general restricted plus other ending balance minus the audited ending balance equals 3.
- Food service audited ending balance minus statutory ending balance equals 1.
- Statutory debt-service ending balance plus OPEB debt-service ending balance equals the audited debt-fund ending balance 4640413.
- FY2027 general beginning balance 21783758 does not equal the FY2026 statutory projected general-fund ending balance (restricted 6190784 plus other 12801445).
- Government-wide FY2025 revenue 123211606 minus expense 119395514 equals 3816092.
- Restated beginning net position 18643209 plus the increase equals ending net position 22459301.
- Unassigned general-fund balance 14159562 is less than the general-fund ending balance.
- Every `value` and `dash` line has a non-empty `source_id`. Every line id is unique.
- Component rows for `gov_funds` FY2025 `expenditure` category other than `total`, fund `all`, sum to 122515320.
- The preliminary source is `loaded=no`. The audit SHA-256 in `sources.csv` starts with `f595eee772c6`.

`tests/test_report.py` renders both formats and asserts the markdown and the HTML each contain all of these strings:

- `121,622,792`
- `122,515,320`
- `464,821`
- `95,288,614`
- `95,885,602`
- `427,707`
- `4,203,023`
- `596,988`
- `123,211,606`
- `119,395,514`
- `3,816,092`
- `3,140,589`
- `15,960,024`
- `124,059,624`
- `132,895,117`
- `14,159,562`
- `not reported`
- `do not chain`
- `not revenue`
- `excluded`

And that neither document contains the digit string `137582816` (headline revenue plus internal-service revenue), which would mean the excluded fund was added in.

Run:

```bash
cd /home/mint/projects/isd181 && PYTHONPATH=src python3 -m unittest discover -s tests -v && PYTHONPATH=src python3 -m isd181
```

## What a blocker is

A blocker is one of these, shown against a file:

- A locked dollar amount in this plan or in `data/lines.csv` contradicts `sources/text/` or the PDF.
- A rule that puts internal service, the custodial fund, government-wide expenses, or statutory inflows into the governmental-fund headline.
- A rule that treats FY2026 statutory general-fund inflows as the same quantity as FY2025 audited general-fund revenue.
- A rule that sets the FY2027 beginning balance equal to the FY2026 statutory ending balance.

A tighter label, a missing footnote, or another category table is a required change, not a blocker. An unexplained debt-service gap between the two budget vintages is not a blocker. Inventing its cause would be.

## Agents

| Step | Agent | Why |
| --- | --- | --- |
| This plan and the ledger extract | Orchestrator | The numbers had to be checked before anyone wrote code. |
| Two skeptics, in parallel | `explore`, read-only | They only read. A general-purpose agent would be wasted, and it could edit. |
| Implementation | `general-purpose`, execute | The only step that writes code. |
| Review | `general-purpose`, execute | Must run the tests. Read-only cannot. |

The skeptics run before the builder. If either one returns a blocker, nothing is built. The parent closes beads only after the tests pass and the review does not show a mixed total.

## Beads

Epic: track ISD 181 income and spending. Children, in order: plan lock, implementation, adversarial review, closeout. Each child depends on the one before it. The epic does not block its children. Close a bead only with the evidence named in its acceptance. Closing the epic is the last act, and only when no child is open.

## Acceptance of the whole job

- `docs/PLAN.md`, `data/lines.csv`, `data/context.csv`, and `data/sources.csv` exist.
- The unit tests pass.
- `output/income-spending.html` and `output/income-spending.md` exist and contain the lead sentences.
- The review records no mixed-basis total.
- Every bead under the epic is closed.
