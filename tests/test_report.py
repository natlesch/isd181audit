"""The report shows each picture and does not add the excluded fund."""

import unittest

from isd181.ledger import load_context, load_lines, load_sources
from isd181.report import render_html, render_markdown


REQUIRED = (
    "121,622,792",
    "122,515,320",
    "464,821",
    "95,288,614",
    "95,885,602",
    "427,707",
    "4,203,023",
    "596,988",
    "123,211,606",
    "119,395,514",
    "3,816,092",
    "3,140,589",
    "15,960,024",
    "124,059,624",
    "132,895,117",
    "14,159,562",
    "not reported",
    "do not chain",
    "not revenue",
    "excluded",
)


class ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        lines = load_lines()
        context = load_context()
        sources = load_sources()
        cls.markdown = render_markdown(lines, context, sources)
        cls.html = render_html(lines, context, sources)

    def test_required_strings_are_in_both_documents(self):
        for document in (self.markdown, self.html):
            for text in REQUIRED:
                with self.subTest(text=text):
                    self.assertIn(text, document)

    def test_excluded_fund_is_not_added_to_the_headline(self):
        # Headline revenue plus internal-service revenue must not appear.
        self.assertNotIn("137582816", self.markdown)
        self.assertNotIn("137582816", self.html)

    def test_vintages_stay_unreconciled(self):
        for document in (self.markdown, self.html):
            self.assertIn("published coincidence", document)
            self.assertIn("not a rollforward", document)
            self.assertIn("unexplained", document)
            self.assertIn("not reconciled", document)
            self.assertIn("1,565,062", document)
            self.assertIn("13,297,649", document)
            self.assertIn("13,270,649", document)
            self.assertIn("These totals are different questions", document)
            self.assertIn("Brainerd Public Schools, ISD 181", document)
            self.assertIn("Income and spending from public reports", document)
            self.assertIn("fund-basis principal", document)
            self.assertIn("not loaded", document)
            self.assertIn("Spending by fund and function", document)
            self.assertIn("Federal award expenditures", document)
            self.assertIn("5,765,316", document)
            self.assertIn("3,978,695", document)
            self.assertIn("not added", document)
            self.assertIn("Restricted, basic skills", document)
            self.assertIn("93,663,493", document)
            self.assertIn("$104,380", document)
            # Federal awards and the restriction budget are not folded in.
            self.assertNotIn("128,280,636", document)
            self.assertNotIn("194,152,035", document)

    def test_html_has_no_external_assets(self):
        self.assertIn("<style>", self.html)
        self.assertNotIn("https://", self.html)
        self.assertNotIn("<script", self.html)
        self.assertNotIn("<link", self.html)
        self.assertIn("text-align: right", self.html)


if __name__ == "__main__":
    unittest.main()
