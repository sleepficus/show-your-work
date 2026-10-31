# Show Your Work v0.1.1 — Fix Report

**Trigger:** independent audit of v0.1 (AUDIT-v0.1.md,
CERTIFY-WITH-FINDINGS, 11 findings). **Commissioned by:** Stephen,
2026-10-30 ~19:31 EDT ("let's dooo it"). **Builder:** Tally (Muse).
**Status: FIXED + TESTED + INSTALLED + SELF-REVIEWED. NOT CERTIFIED**
— a fresh-lane delta audit is the remaining step.

## Deliverable

`show-your-work-v0.1.1.zip` (hash recorded below after packaging;
the zip contains this report, the spec, the v0.1 audit, and the
corrected build report).

## Fixes, by audit finding

- **F1 (HIGH) — false CONTRADICTED against honest reports.** The
  failure-admission test required the number adjacent to "failed."
  Admissions are now recognized in ordinary forms: "3 tests failed,"
  "tests failed," "failures: 3," "2 of 9 failed," "not all tests
  passed," "did not pass," "failing tests." A report admitting failure
  is never graded as asserting a clean pass. Regression test added.
- **F2 (MEDIUM) — pytest short summaries missed.** `FAILED
  tests/x.py::test_b` and `ERROR …::…` summary lines, and unittest
  `ERROR:` headers, are now strong failure markers.
- **F3 (MEDIUM) — prose "N passed" polluted test totals.** Bases are
  anchored to test-shaped text only (`Ran N tests`, `N tests passed`,
  `N/M`, pytest trailer forms). "500 passed the entrance exam" no
  longer supports a 500-tests claim. Regression test added.
- **F4 (MEDIUM) — invented hash pairs.** Pairing now requires exactly
  ONE distinct file token in the window before a hash; two or more
  means ambiguous — no pair is stated, and the hash grades on its own.
  Regression test added.
- **F5 (LOW) — undisclosed unsearched files.** Files too large or
  binary for text search are now listed by name (first 20) and counted
  in the JSON `limits` block.
- **F6 (LOW) — self-grading.** When the report sits inside the
  evidence tree it is excluded from the evidence, and the exclusion is
  disclosed in `limits.report_excluded_from_evidence`. (Visible in the
  dogfood: the Tracklayer build report's supported count dropped from
  21 to 19 when it stopped grading its own text.)
- **F7 (LOW) — count comma retry.** Non-file/test count claims now
  retry the comma form ("56474 verdicts" finds "56,474 verdicts").
- **F10/F11 (INFORMATIONAL) — cosmetic rows.** The success-claim
  trigger now requires test-shaped language (a passing "pass rate" or
  a deadline that "passed" no longer invents a claim), and a
  zero-claim card reads "no checkable claims found" instead of a rosy
  verdict.
- **F8** was a build-report wording error ("17 files" for 17 entries /
  13 files), corrected by addendum in BUILD-REPORT.md; this report
  counts entries and files separately. **F9** (basename satisfaction)
  was disclosed behavior; unchanged.

## Builder's lap

- **Tests: 27/27 pass** (19 original + 8 audit regressions).
- **Example:** unchanged verdicts — 4 SUPPORTED / 4 CONTRADICTED /
  1 UNVERIFIABLE, exit 1. The fixes did not disturb designed behavior.
- **Install:** the `~/workspace/bin/showyourwork` launcher picks up
  the fixed package in place; re-verified against the Tracklayer
  build report from a clean directory.

## Remaining known limits

Unchanged from v0.1 except as fixed above: scope is the operator's
choice; prose ungraded; success markers cover common runner shapes;
pair detection needs the filename shortly before the hash on the same
line (hash-first forms grade as bare hashes, by design).
