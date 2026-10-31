# Show Your Work — spec v0.1

**Stephen's ask, in his words (2026-10-30):** "a simple tool to check
whether or not their agents did the work they wanted… we don't need to
give them everything we have but just enough — it's simple and easy to
use or get one of their agents to run." Order of work, also his: spec,
then build, test, install — and make it easy for us to use too.

## What it is

A tiny, deterministic checker. You hand it an agent's completion report
and the evidence the work supposedly produced. It extracts the checkable
claims from the report and grades each one against the evidence:

- **SUPPORTED** — the evidence carries the claim.
- **CONTRADICTED** — the evidence says otherwise.
- **UNVERIFIABLE** — no basis in the evidence either way (listed, never
  hidden, never rounded up to a pass).

Doctrine, printed in the README and in every output footer:

> This tool checks receipt discipline, not truth. SUPPORTED means the
> evidence carries the claim — not that the evidence is honest.

## Checks (v0.1, all deterministic, no model, no network)

1. **File claims** — files named in the report are looked for in the
   evidence. Present → SUPPORTED; named but absent → CONTRADICTED.
2. **Hash claims** — SHA-256 strings in the report are compared against
   the recomputed SHA-256 of every evidence file, and against
   file↔hash pairs stated in the report itself. Match → SUPPORTED;
   a full hash that matches nothing → CONTRADICTED.
3. **Count claims** — "N files" against the actual evidence file count;
   "N tests/checks" against test-summary lines in the evidence text.
   No basis → UNVERIFIABLE.
4. **Success claims** — a report asserting a clean pass while the
   evidence text carries failure markers (FAILED, Traceback, nonzero
   failure counts) → CONTRADICTED.
5. **Numbers and percentages** — searched in the evidence text. Found →
   SUPPORTED (weak); absent → UNVERIFIABLE. Absence of a number is
   never a contradiction.

## Contract

- `showyourwork check REPORT --evidence PATH [--json]`
- Evidence is a directory (walked) or a single file. Text is read as
  UTF-8, lossy; per-file and total caps are recorded in the output.
- Human output: a report card (per-claim verdicts + summary counts).
- `--json`: a stable machine schema for agents.
- Exit codes: 0 = no contradictions · 1 = contradictions found ·
  2 = usage/input error. An agent can gate on the exit code alone.

## Non-goals (v0.1)

No AI judge. No prose/entailment grading. No source-trust judgment.
No GitHub integration. No installation beyond a folder and `python3`
(3.10+, standard library only). This is the mechanism layer of the
verification discipline in *Did the Agent Do the Work?* — the layer
that has never been wrong in our records — packaged to stand alone.

## Definition of done (Law 2)

Spec → build → test → install (verified from a clean directory) →
self-review → independent fresh-lane audit certifies. The builder
never certifies. First public repo candidate; nothing pushes anywhere
without Stephen's separate word.
