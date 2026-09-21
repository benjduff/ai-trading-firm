from app.ingestion.sec_edgar import extract_excerpt

# Reproduces the structural pattern found in real 10-Q/10-K filings that broke a
# naive text[:N] excerpt: a table-of-contents entry, an earlier cross-reference
# to the section (neither of which is the real content), and the actual MD&A
# section - which itself opens with a long generic legal disclaimer before any
# real figures appear. See app/ingestion/sec_edgar.py's module docstring.
FILING_WITH_MDNA = """
<html><body>
<div style="display:none">hidden xbrl metadata that must never appear in the excerpt $999,999,999</div>
<script>var hiddenScriptContent = "must not appear";</script>
<ix:hidden>more hidden xbrl content that must never appear</ix:hidden>

<p>TABLE OF CONTENTS</p>
<p>Note 9-Earnings Per Share and Equity 24</p>
<p>Item 2. Management's Discussion and Analysis of Financial Condition and
Results of Operations 28 Cautionary Statement Regarding Forward-Looking
Statements 28 Current Business Outlook 29</p>

<p>See the information under Environmental Expenditures in the Management's
Discussion and Analysis of Financial Condition and Results of Operations
section under Part II, Item 7 of this Form 10-K for additional detail.</p>

<p>PART I ITEM 2. Management's Discussion and Analysis of Financial Condition
and Results of Operations The following discussion should be read together
with the Consolidated Condensed Financial Statements. CAUTIONARY STATEMENT
REGARDING FORWARD-LOOKING STATEMENTS Portions of this report contain
forward-looking statements within the meaning of Section 27A of the
Securities Act of 1933. Words such as estimate, project, predict, will,
would, should, could, may, might, anticipate, plan, intend, believe, expect
are generally indicative of forward-looking statements. You should not place
undue reliance on these statements which speak only as of the date hereof
and are subject to numerous risks including changes in general economic
conditions, competitive pressures in the industries in which the company
operates, and other factors beyond the company's control that could cause
actual results to differ materially from any projections set forth herein.
</p>

<p>CURRENT BUSINESS OUTLOOK The Company's financial results are significantly
influenced by crude oil prices. The average WTI price per barrel was $92.79
for the three months ended June 30, 2026, compared with $71.93 for the three
months ended March 31, 2026. Net income attributable to common stockholders
was $2,807 million, versus $3,175 million a year ago, a decrease of 12%.</p>
</body></html>
"""

FILING_WITHOUT_MDNA = """
<html><body>
<p>UNITED STATES SECURITIES AND EXCHANGE COMMISSION WASHINGTON D.C. 20549 FORM
8-K CURRENT REPORT Pursuant to Section 13 or 15(d) of the Securities Exchange
Act of 1934.</p>
<p>Item 2.02 Results of Operations and Financial Condition. On August 5, 2026
the Company issued a press release announcing its financial results for the
quarter ended June 30, 2026.</p>
</body></html>
"""


def test_skips_toc_and_cross_reference_to_find_the_real_mdna_section():
    excerpt = extract_excerpt(FILING_WITH_MDNA.encode())
    assert "CURRENT BUSINESS OUTLOOK" in excerpt
    assert "$92.79" in excerpt


def test_strips_hidden_script_and_xbrl_content():
    excerpt = extract_excerpt(FILING_WITH_MDNA.encode())
    assert "hidden xbrl metadata" not in excerpt
    assert "must not appear" not in excerpt
    assert "999,999,999" not in excerpt


def test_excerpt_does_not_start_with_toc_boilerplate():
    excerpt = extract_excerpt(FILING_WITH_MDNA.encode())
    # the naive old behavior (text[:N]) would have started here
    assert not excerpt.startswith("TABLE OF CONTENTS")
    assert not excerpt.lstrip().startswith("Note 9")


def test_falls_back_to_start_of_document_when_no_mdna_section_exists():
    excerpt = extract_excerpt(FILING_WITHOUT_MDNA.encode())
    assert "SECURITIES AND EXCHANGE COMMISSION" in excerpt
    assert excerpt.startswith("UNITED STATES")


def test_excerpt_is_bounded_by_max_chars():
    from app.ingestion.sec_edgar import EXCERPT_MAX_CHARS

    excerpt = extract_excerpt(FILING_WITH_MDNA.encode())
    assert len(excerpt) <= EXCERPT_MAX_CHARS
