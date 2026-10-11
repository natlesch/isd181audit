"""Ledger sums stay inside one basis, statement, measure, and year."""

import unittest

from isd181.ledger import (
    LedgerError,
    headline,
    load_lines,
    load_sources,
    require_single,
    select,
    sum_amounts,
)


class LedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lines = load_lines()
        cls.sources = load_sources()

    def test_headline_revenue_and_expenditure(self):
        self.assertEqual(headline(self.lines, 2025, "revenue"), 121622792)
        self.assertEqual(headline(self.lines, 2025, "expenditure"), 122515320)
        self.assertEqual(headline(self.lines, 2024, "revenue"), 122048819)
        self.assertEqual(headline(self.lines, 2024, "expenditure"), 120712127)

    def test_headline_is_one_measure(self):
        # headline=yes also marks balances, other financing, net change, and excess.
        mixed = select(
            self.lines, statement="gov_funds", headline="yes", fiscal_year=2025
        )
        measures = {line.measure for line in mixed}
        self.assertGreater(len(measures), 1)
        with self.assertRaises(LedgerError):
            sum_amounts(mixed)
        self.assertEqual(headline(self.lines, 2025, "beginning_balance"), 33099794)
        self.assertNotEqual(
            headline(self.lines, 2025, "revenue"),
            headline(self.lines, 2025, "revenue")
            + headline(self.lines, 2025, "beginning_balance"),
        )

    def test_internal_service_cannot_join_the_headline(self):
        head = select(
            self.lines, statement="gov_funds", headline="yes",
            fiscal_year=2025, measure="revenue",
        )
        memo = require_single(self.lines, "memo-internal-revenue")
        self.assertEqual(memo.amount, 15960024)
        self.assertEqual(memo.basis, "memo_excluded")
        with self.assertRaises(LedgerError):
            sum_amounts([*head, memo])
        for line in self.lines:
            if line.headline == "yes":
                self.assertNotEqual(line.fund, "internal")
                self.assertNotEqual(line.basis, "memo_excluded")

    def test_mixed_revenue_and_expense_raises(self):
        mixed = [
            require_single(self.lines, "gw-2025-revenue-total"),
            require_single(self.lines, "gw-2025-expense-total"),
        ]
        with self.assertRaises(LedgerError):
            sum_amounts(mixed)

    def test_blank_internal_inflow_raises(self):
        blank = require_single(self.lines, "stat-2025-internal-inflow")
        self.assertEqual(blank.amount_state, "blank")
        self.assertIsNone(blank.amount)
        with self.assertRaises(LedgerError):
            sum_amounts([blank])
        wider = select(
            self.lines, statement="statutory", fiscal_year=2025, measure="inflow"
        )
        self.assertTrue(any(line.amount_state == "blank" for line in wider))
        with self.assertRaises(LedgerError):
            sum_amounts(wider)

    def test_dash_is_zero_and_not_blank(self):
        dash = require_single(self.lines, "stat-2025-trust-inflow")
        self.assertEqual(dash.amount_state, "dash")
        self.assertEqual(dash.amount, 0)

    def test_fy2025_fund_rows_roll(self):
        for fund in ("general", "food", "community", "building", "debt"):
            begin = self._fund(fund, "beginning_balance")
            revenue = self._fund(fund, "revenue")
            expenditure = self._fund(fund, "expenditure")
            other = self._fund(fund, "other_financing")
            ending = self._fund(fund, "ending_balance")
            self.assertEqual(
                begin + revenue - expenditure + other,
                ending,
                fund,
            )

    def test_general_fund_rsi_gaps(self):
        final = require_single(self.lines, "gfrsi-excess-final")
        actual = require_single(self.lines, "gfrsi-excess-actual")
        net = require_single(self.lines, "gfrsi-net-actual")
        self.assertEqual(final.amount, -4203023)
        self.assertEqual(actual.amount, -596988)
        self.assertEqual(net.amount, -169281)

    def test_statutory_general_fund_crosswalk(self):
        beginning = self._statutory_pair(2025, "beginning_balance")
        ending = self._statutory_pair(2025, "ending_balance")
        audited_begin = self._fund("general", "beginning_balance")
        audited_end = self._fund("general", "ending_balance")
        self.assertEqual(beginning, 22379183)
        self.assertEqual(beginning, audited_begin)
        self.assertEqual(ending - audited_end, 3)

    def test_food_and_debt_statutory_endings(self):
        food_audit = self._fund("food", "ending_balance")
        food_stat = self._statutory("food", 2025, "ending_balance")
        self.assertEqual(food_audit - food_stat, 1)
        debt = sum_amounts([
            self._statutory_line("debt", 2025, "ending_balance"),
            self._statutory_line("opeb_debt", 2025, "ending_balance"),
        ])
        self.assertEqual(debt, 4640413)
        self.assertEqual(self._fund("debt", "ending_balance"), 4640413)

    def test_fy2027_beginning_is_not_the_fy2026_ending(self):
        adopted = require_single(self.lines, "fy27-general-beginning_balance")
        projected = self._statutory_pair(2026, "ending_balance")
        self.assertEqual(adopted.amount, 21783758)
        self.assertEqual(projected, 6190784 + 12801445)
        self.assertNotEqual(adopted.amount, projected)
        # Building construction matches. That is not a rollforward, and the
        # two lines cannot be summed into one balance.
        building_adopted = require_single(self.lines, "fy27-building-beginning_balance")
        building_statutory = self._statutory_line("building", 2026, "ending_balance")
        self.assertEqual(building_adopted.amount, 1565062)
        self.assertEqual(building_statutory.amount, 1565062)
        with self.assertRaises(LedgerError):
            sum_amounts([building_adopted, building_statutory])
        opeb_adopted = require_single(self.lines, "fy27-opeb_trust-beginning_balance")
        opeb_statutory = self._statutory_line("opeb_irrevocable", 2026, "ending_balance")
        self.assertEqual(opeb_adopted.amount, 13297649)
        self.assertEqual(opeb_statutory.amount, 13270649)
        self.assertNotEqual(opeb_adopted.amount, opeb_statutory.amount)

    def test_government_wide_change_in_net_position(self):
        revenue = require_single(self.lines, "gw-2025-revenue-total")
        expense = require_single(self.lines, "gw-2025-expense-total")
        increase = require_single(self.lines, "gw-2025-increase")
        restated = require_single(self.lines, "gw-2025-np-restated")
        ending = require_single(self.lines, "gw-2025-np-end")
        self.assertEqual(revenue.amount, 123211606)
        self.assertEqual(expense.amount, 119395514)
        self.assertEqual(revenue.amount - expense.amount, 3816092)
        self.assertEqual(increase.amount, 3816092)
        self.assertEqual(restated.amount, 18643209)
        self.assertEqual(ending.amount, 22459301)
        self.assertEqual(restated.amount + increase.amount, ending.amount)

    def test_unassigned_is_part_of_the_general_fund(self):
        unassigned = require_single(self.lines, "gov-2025-general-unassigned")
        ending = self._fund("general", "ending_balance")
        self.assertEqual(unassigned.amount, 14159562)
        self.assertLess(unassigned.amount, ending)

    def test_sources_and_identities(self):
        seen = set()
        for line in self.lines:
            self.assertNotIn(line.line_id, seen)
            seen.add(line.line_id)
            if line.amount_state in ("value", "dash"):
                self.assertTrue(line.source_id)
        components = [
            line for line in select(
                self.lines, statement="gov_funds", fiscal_year=2025,
                measure="expenditure", fund="all",
            )
            if line.category != "total"
        ]
        self.assertEqual(sum_amounts(components), 122515320)
        by_id = {source.source_id: source for source in self.sources}
        self.assertEqual(by_id["preliminary"].loaded, "yes")
        self.assertTrue(by_id["audit"].sha256.startswith("f595eee772c6"))

    def test_fund_function_cells_match_each_fund_and_the_headline(self):
        cells = select(
            self.lines, statement="spend_cross", fiscal_year=2025,
            measure="expenditure",
        )
        self.assertEqual(sum_amounts(cells), headline(self.lines, 2025, "expenditure"))
        for fund in ("general", "food", "community", "building", "debt"):
            fund_cells = [line for line in cells if line.fund == fund]
            self.assertEqual(sum_amounts(fund_cells), self._fund(fund, "expenditure"))
        self.assertTrue(all(line.headline == "no" for line in cells))
        self.assertNotIn("internal", {line.fund for line in cells})

    def test_federal_awards_are_not_federal_revenue(self):
        programs = [
            line for line in select(
                self.lines, statement="sefa", fiscal_year=2025, measure="expenditure",
            )
            if line.category != "total"
        ]
        total = require_single(self.lines, "sefa-2025-total")
        self.assertEqual(sum_amounts(programs), total.amount)
        self.assertEqual(total.amount, 5765316)
        federal_revenue = require_single(self.lines, "gov-2025-all-revenue-federal")
        self.assertEqual(total.amount - federal_revenue.amount, 300)
        self.assertEqual(total.basis, "federal_award")
        self.assertNotEqual(total.basis, federal_revenue.basis)
        self.assertEqual(total.headline, "no")
        # The printed ALN 84.425 total is not a ledger line.
        self.assertFalse(any(line.amount == 3978695 for line in self.lines))

    def test_restriction_budget_matches_the_audit_final_budgets(self):
        pairs = (
            ("general", "gfrsi-expenditure-total-final", 98266433),
            ("food", "foodrsi-expenditure-total-final", 5089834),
            ("community", "commrsi-expenditure-total-final", 3968176),
        )
        for fund, audit_id, expected in pairs:
            pieces = [
                line for line in select(
                    self.lines, statement="budget_restriction", fiscal_year=2025,
                    fund=fund, measure="expenditure", stage="final",
                )
                if line.category != "total"
            ]
            book = require_single(self.lines, f"bud-2025-{fund}-total")
            audit = require_single(self.lines, audit_id)
            self.assertEqual(sum_amounts(pieces), book.amount)
            self.assertEqual(book.amount, audit.amount)
            self.assertEqual(book.amount, expected)
            self.assertEqual(book.basis, "budget_book")
            self.assertEqual(book.headline, "no")
        # The FY2024 book total that does not foot is not loaded.
        self.assertFalse(any(line.amount == 93663493 for line in self.lines))

    def test_require_single_rejects_a_missing_id(self):
        with self.assertRaises(LedgerError):
            require_single(self.lines, "not-a-line")

    def _fund(self, fund, measure):
        found = select(
            self.lines, statement="gov_funds", fiscal_year=2025, fund=fund,
            measure=measure, category="total", stage="actual",
        )
        self.assertEqual(len(found), 1)
        return found[0].amount

    def _statutory_line(self, fund, fiscal_year, measure):
        found = select(
            self.lines, statement="statutory", fiscal_year=fiscal_year,
            fund=fund, measure=measure, category="total",
        )
        self.assertEqual(len(found), 1)
        return found[0]

    def _statutory(self, fund, fiscal_year, measure):
        return self._statutory_line(fund, fiscal_year, measure).amount

    def _statutory_pair(self, fiscal_year, measure):
        return sum_amounts([
            self._statutory_line("general_restricted", fiscal_year, measure),
            self._statutory_line("general_other", fiscal_year, measure),
        ])


if __name__ == "__main__":
    unittest.main()
