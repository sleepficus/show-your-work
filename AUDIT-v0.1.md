# Show Your Work v0.1 — Independent Audit

**Auditor:** fresh Muse lane (audit-only; nothing in the deliverable
was modified — all runs were against an unzipped copy in /tmp and
fresh auditor fixtures).
**Date:** 2026-10-30. **Subject:** `show-your-work-v0.1.zip`, checked
against SPEC.md and BUILD-REPORT.md.

## Verdict: CERTIFY-WITH-FINDINGS

The contract holds end to end: zip integrity, manifest, test suite,
example card, exit codes, JSON schema, and the builder's dogfood
account all reproduce exactly. The deterministic core (files, hashes,
counts) survived every probe aimed at it. The findings cluster where
findings usually live — in the two prose-adjacent heuristics (success
claims, test-total bases) and in pairing. **F1 is the headline:** the
tool can manufacture a CONTRADICTED row against a report that honestly
admits its failures. It should be fixed before this tool is used to
gate anyone's work, and F2–F4 with it. None of the findings contradict
the build report's evidence section; one wording overstatement is
named in F8.

## What I verified (ran, not just read)

- **Zip integrity:** SHA-256 of `show-your-work-v0.1.zip` =
  `d47a68bf766ef8d3c3bc0998b4a49133fc64bc965e2ab541f112d990908d0d7f` ✓
  matches the report. Contents: **17 zip entries — 13 files + 4
  directory entries** (see F8). `diff -r` of the unzipped tree against
  the source tree (excluding `__pycache__` and the zip): identical ✓.
- **MANIFEST.txt:** 12 entries; `sha256sum -c` — all OK; the manifest
  does **not** list itself ✓ (the 13th file in the zip is the manifest,
  correctly excluded).
- **Test suite, run by me:** `Ran 19 tests — OK` ✓ (builder's 19/19
  is accurate).
- **Bundled example, run by me:** 4 SUPPORTED / 4 CONTRADICTED /
  1 UNVERIFIABLE, exit 1 — the card is byte-for-byte the one printed
  in the README and described in the build report ✓.
- **Installed launcher from a clean directory** (`~/workspace/bin/
  showyourwork`, cwd=/tmp): example exit 1 ✓; a clean fixture of mine
  (true report, matching hash/counts) → 4/0/0, exit 0 ✓; missing
  report → 2 ✓; missing evidence → 2 ✓; no arguments → 2 ✓.
- **JSON contract:** parses; top level carries `summary`, `claims`
  (each with `kind`/`claim`/`verdict`/`reason`), `evidence_files`,
  `limits` (files_skipped_unreadable, walk_capped,
  text_search_cap_bytes_per_file), and the `doctrine` string ✓ —
  exactly the shape the README promises agents.
- **Dogfood re-run** (BUILD-REPORT-v0.1.md vs the github-autopilot
  folder): the claimed zip SHA-256 grades **SUPPORTED by
  recomputation** ("matches evidence file tracklayer-v0.1.zip") ✓;
  "12 tests" SUPPORTED ✓; "7,876" SUPPORTED ✓. The only two
  CONTRADICTED rows are "12 files" and "4 files" vs a 31-file folder —
  precisely the scope artifact the builder disclosed ✓.
- **Builder's six self-reported defect fixes, spot-reproduced:**
  sentence-final filename now extracted (my `ghost.py.` probe →
  CONTRADICTED as designed) ✓; hash case-insensitivity (uppercase
  pair → SUPPORTED) ✓; a hash present only in evidence *text* →
  SUPPORTED ✓; boundary-aware bare numbers (13 ≁ 130, 3.5 ≁ 13.55,
  1300 ↔ "1,300" both directions) ✓; version tokens behave
  (`tracklayer-v0.1.zip` is a file claim and resolves; `muse-spark-1.3`
  is not extracted as one) ✓.
- **Non-goals absent:** grep over the package finds no network, model,
  or subprocess usage — stdlib only ✓. Version strings consistent
  (0.1.0 in `__init__` and in the JSON card) ✓.
- **Robustness:** empty report → 0 claims, exit 0; empty evidence dir
  → file claims CONTRADICTED, exit 1; evidence as a single file works
  (and a file merely *mentioned* in that log correctly stays
  CONTRADICTED — mention is not existence); binary evidence is hashed
  and counted with text skipped; a broken symlink lands in
  `files_skipped_unreadable` (=1) ✓; CRLF reports parse; backticked,
  table-cell, parenthesised, comma-separated, and deep-path filenames
  all resolve ✓; "12 of 12 tests" and "12/12 checks" both extract and
  grade ✓; a report claiming "0 failures" against FAILED evidence is
  CONTRADICTED ✓.

## Findings

### F1 — HIGH: an honestly-admitting report earns a false CONTRADICTED

The failure-admission pattern requires the number to touch the word
(`2 failed`). The ordinary English form puts a noun between them, and
then the admission is invisible — while any later pass-language
("the rest passed") is read as a clean-pass assertion and contradicted
by the failure markers the report itself was honest about.

Reproduction (auditor fixture): report = *"Status: 3 tests failed;
remaining tests passed."*, evidence log = `FAILED (failures=3)`.
Output row: `[ CONTRADICTED ] report asserts a clean pass`. The
evidence **agrees** with the report; the row manufactures both the
assertion and the contradiction, and flips the run to exit 1 — the
exit code an agent would gate on. Control: *"2 failed, 9 passed"*
(adjacent form) behaves correctly — no success row.
Fix direction: let the admission pattern span an optional noun
(`N (tests|checks) failed|errors`), and treat qualified pass-language
("the rest passed", "remaining … passed") as no clean-pass assertion.

### F2 — MEDIUM: pytest's short-summary FAILED lines escape the success check

All four strong failure markers require a count string or the
unittest banner. Pytest's canonical short-summary lines —
`FAILED tests/test_x.py::test_b - AssertionError` — match none of
them. With any "N passed" text also present, a clean-pass claim over
such a log grades **SUPPORTED** (auditor fixture, reproduced). The
full pytest trailer (`===== 2 failed, 3 passed in 0.42s =====`) IS
caught (verified), so the gap is excerpted logs — a common evidence
shape, and the README's check table claims "pytest failure summaries"
without the distinction.

### F3 — MEDIUM: test-total bases accept any "N passed" prose in the evidence

The basis harvest for "N tests/checks" includes a bare
`(\d+)\s+passed` pattern with no test context. Auditor fixture: report
claims *"500 tests"*; the only evidence is an essay containing *"500
passed the entrance exam"* → `500 tests` grades **SUPPORTED**. A false
SUPPORTED in a headline check. Fix direction: require test-context
words near a basis, or drop the bare pattern and keep `Ran N tests`,
`N/M`, and `N tests passed` shapes.

### F4 — MEDIUM: hash-pairing picks the nearest file token — and can pick the wrong one

A pair is graded against the **last** file token within 80 chars
before the hash. Auditor fixture: *"Built app.py and lib.py —
SHA-256: ⟨app.py's real hash⟩"* → row `lib.py = 17e682f0… CONTRADICTED`
— a pair the report never stated, graded as a contradiction (the true
file's own row is separately SUPPORTED). The build report discloses
the nearest-token mechanism (its defect #1) but not this failure mode.
Degraded forms behave acceptably (hash-first and hash-on-next-line
fall back to the bare-hash path with correct verdicts), so the defect
is specifically multi-token lines. Fix direction: if the window holds
more than one distinct file token, grade the hash as a bare hash
instead of inventing a pair.

### F5 — LOW: files over the 1 MB text cap are silently unsearchable

For an evidence file larger than MAX_TEXT_BYTES the text is dropped
wholesale (not truncated), so claims whose support lives in that file
grade UNVERIFIABLE with the reason *"does not appear in the evidence
text"* — a misdescription: the text was never searched (auditor
fixture: 1.39 MB log, number present past the cap). The limits block
reports the cap value but no count or names of unsearched files.
Honesty fix: count text-skipped files in `limits` and say so.

### F6 — LOW: a report inside the evidence tree grades itself

If the report file sits under the evidence root (an easy operator
slip — agents often write `report.md` into the work folder), its own
numbers are found in "the evidence text": auditor fixture graded a
fabricated *"999999 lines"* **SUPPORTED** against the report itself.
Not disclosed in the README's scope note. Fix direction: exclude the
report's own path from the evidence walk, or flag it in `limits`.

### F7 — LOW: count claims don't get the comma-form courtesy bare numbers get

The bare-number pass retries with comma grouping (1300 ↔ "1,300",
verified both directions), but the count pass for other nouns compares
the literal phrase: report *"56474 verdicts"* vs evidence *"56,474
verdicts"* → UNVERIFIABLE. Errs safe; inconsistent.

### F8 — INFORMATIONAL: the build report's "17 files" counts zip entries

The zip holds 17 **entries**, of which 13 are files and 4 are
directory entries; the report's own itemised contents describe the 13
files. (`unzip -l`'s summary line also says "17 files," so the number
is traceable — but stated precisely, it is 17 entries / 13 files.)
Everything else in the report's evidence section reproduced exactly.

### F9 — INFORMATIONAL (disclosed limit): basename satisfaction

A file claim is satisfied by a same-basename file anywhere in the tree
(probe: `docs/report.md` satisfied by `other/report.md`). The README's
check table discloses basename matching, and the verdict reason names
the actual path found, so a reader can catch it. Recorded, not held
against the build.

### F10 — INFORMATIONAL: cosmetic noise rows

"Pass rate" prose triggers a success-claim row (UNVERIFIABLE when no
markers exist — harmless, but the row mislabels analysis as a test
assertion); digits from version strings surface as weak UNVERIFIABLE
numbers (`1.3`, `1` out of `muse-spark-1.3`). Clutter, not error.

### F11 — INFORMATIONAL: the zero-claim verdict line

An empty report produces *"verdict: every checkable claim is supported
by the evidence"* over 0 claims. Literally true, cosmetically rosy;
exit 0 is correct. A "no claims found" line would be more in the
tool's own spirit.

## Auditor's note on scope

Certification covers the deterministic contract as specced: extraction
and grading of file, hash, count, success, and bare-number claims
against handed-over evidence. It does not cover — and the tool does
not claim — prose truth, source honesty, or entailment; the doctrine
footer says so on every card, and every probe I ran is consistent with
that boundary. Fix F1–F4 in a v0.1.1 (F1 first — it is the only finding
that wrongs an honest reporter), F5–F7 as the same batch's polish, and
this is a clean little tool.

*End of audit.*
