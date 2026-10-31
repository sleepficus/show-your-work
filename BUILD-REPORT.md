# Show Your Work v0.1 — Build Report

**Commission:** Stephen, 2026-10-30 ~19:16 EDT — a simple public tool
to check whether an agent did the work, "just enough," easy for a
person or an agent to run; first GitHub upload candidate. Order per
Stephen: spec → build → test → install. **Builder:** Tally (Muse).
**Status: BUILT + TESTED + INSTALLED + SELF-REVIEWED. NOT CERTIFIED**
— independent audit is the remaining Law 2 step.

## Deliverable

`show-your-work-v0.1.zip` — 17 files, MANIFEST.txt inside (its own
name excluded from itself).
**SHA-256: `d47a68bf766ef8d3c3bc0998b4a49133fc64bc965e2ab541f112d990908d0d7f`**

Contents: SPEC.md · README.md · showyourwork/ (__init__, __main__,
cli, core — stdlib only) · tests/ (19 tests) · examples/ (a report
with five planted problems + its evidence folder).

## What it does

Per SPEC.md: extracts checkable claims from an agent's completion
report (files, SHA-256 hashes and file↔hash pairs, counts of files /
tests / checks, clean-pass assertions, bare numbers and percentages)
and grades each SUPPORTED / CONTRADICTED / UNVERIFIABLE against the
evidence, deterministic only. Human report card or `--json`; exit
0/1/2 so an agent can gate on it. Doctrine printed in every output:
receipt discipline, not truth.

## Builder's lap (evidence)

- **Tests: 19/19 pass** (`python3 -m unittest discover -s tests`).
- **Example run:** the planted report grades exactly as designed —
  4 SUPPORTED / 4 CONTRADICTED / 1 UNVERIFIABLE, exit 1. Every planted
  problem caught (missing package + its hash-pair, missing export,
  9-vs-7 tests, 5-vs-4 files); the "3 formats" claim honestly
  UNVERIFIABLE.
- **Dogfood:** run against the Tracklayer build report with its
  project folder as evidence — the report's claimed zip SHA-256
  recomputed and matched (SUPPORTED), 12-tests matched a recorded
  total, 7,876 tokens found. Its two CONTRADICTED file-counts are a
  scope artifact (report counts the deliverable's files; evidence was
  the whole folder) — the README's limits section now states the scope
  rule explicitly.
- **Install:** launcher at `~/workspace/bin/showyourwork`; verified
  from a clean directory (/tmp): example exit 1, a clean report exit
  path exercised, `--json` parses with correct summary.

## Defects found and fixed in the builder's own lap

1. Pair detection window (6 chars) missed prose-style pairs
   ("— the packaged release, SHA-256: …"). Rebuilt as nearest
   file-token pairing on the hash's line (80-char window).
2. A sentence-final filename ("…plus ghost.py.") was swallowed by its
   own full stop — file claims silently missing. Regex lookahead
   fixed; regression test added.
3. The "256" in the label "SHA-256:" was extracted as a number claim.
   Algorithm labels are now masked alongside hash spans.
4. A bare "3" matched the 3 in "python3" via substring fallback.
   Number search is boundary-aware (letters/dots/digits all block);
   comma-form variants still found; regression tests added.
5. Case mismatch on hashes in evidence text could manufacture a
   contradiction. Hash text search is case-insensitive; regression
   test added.
6. Dead helper removed in self-review.

## Stated limits (also in README)

Scope is the operator's choice (claims grade against the evidence as
handed over). Prose is not graded and unextractable claims are not
listed. Success-marker heuristics cover common test-output shapes;
exotic runners land UNVERIFIABLE. File tokens require a known
extension or a path shape. Bare-number support is weak by design —
presence only; absence is never a contradiction.

## Next

Independent fresh-lane audit → verdict recorded here. On
certification: shelf copy to the Mac (hash-verified) per standing
practice, and the repo/push decision is Stephen's (Tracklayer's live
door opens only after its own v0.1.1 fixes; this tool may also simply
be the first repo created the ordinary way — Stephen's call).


---

## Audit outcome (appended 2026-10-30, after the fact)

Independent fresh-lane audit: **CERTIFY-WITH-FINDINGS** — full report at
`AUDIT-v0.1.md` (11 findings). The auditor re-ran everything: zip hash,
manifest (12 hashes verify, no self-entry), 19/19 tests, the example
card reproduced byte-for-byte against the README, launcher exit codes,
JSON schema, and the Tracklayer dogfood — all corroborated, including
all six builder-lap fixes spot-reproduced.

Corrections this report accepts:
- **"17 files" (above) is wrong as stated:** the zip holds 17 ENTRIES,
  of which 13 are files and 4 are directory entries. The itemized
  contents list in this report describes the 13 correctly. Builder
  overstatement (the zip tool's summary wording, copied uncritically),
  owned.
- **F1 (HIGH) leads the v0.1.1 fix batch:** a report in the ordinary
  form "3 tests failed; remaining tests passed" is not recognized as
  admitting failure (the admission pattern requires the number adjacent
  to "failed"), so the tool invents a clean-pass assertion and can
  contradict a truthful report. A checker must never manufacture a
  contradiction; F1 closes before this tool gates anyone's work.
- Also in the fix round: F2 (pytest short-summary FAILED lines are not
  markers — the README's "pytest failure summaries" needs the
  excerpted-log distinction), F3 (test-total bases accept unrelated
  "N passed" prose), F4 (pairing takes the last file token before a
  hash and can state a pair the report never made). F5–F7 are LOW;
  F8 is the correction above; F9–F11 informational.

Status after audit: v0.1 is certified-with-findings as a demonstration
and dogfood tool. v0.1.1 (F1 first, then F2–F4) is the gate before it
is offered as a gate for anyone else's agent.
