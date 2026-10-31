# Show Your Work

**A tiny checker for the oldest question in agent operations: did the
agent actually do the work?**

Hand it an agent's completion report and the evidence the work
supposedly produced. It extracts the checkable claims from the report —
files, hashes, counts, success assertions, numbers — and grades each
one against the evidence:

- **SUPPORTED** — the evidence carries the claim.
- **CONTRADICTED** — the evidence says otherwise.
- **UNVERIFIABLE** — no basis in the evidence either way. Listed, never
  hidden, never rounded up to a pass.

> **Doctrine.** This tool checks *receipt discipline, not truth.*
> SUPPORTED means the evidence carries the claim — not that the
> evidence is honest. It is a metal detector, not an assay office: it
> beeps at claims with nothing behind them; it does not certify the
> ones that beep clean.

It is the mechanism layer of the verification discipline described in
*Did the Agent Do the Work?* (Misfit Circuit, 2026) — deterministic
checks only. No AI judge, no network, no dependencies: Python 3.10+
standard library, one small package.

## Run it

No install needed. From this folder:

```
python3 -m showyourwork check REPORT.md --evidence ./the-work
```

Or install the launcher anywhere on your PATH (see BUILD-REPORT):

```
showyourwork check REPORT.md --evidence ./the-work
showyourwork check REPORT.md --evidence ./the-work --json
```

Exit codes, so an agent (or a CI step) can gate on the result alone:
**0** = no contradictions · **1** = contradictions found · **2** =
usage/input error.

## Try the example

`examples/` holds a fake agent report with five planted problems — a
packaged file that doesn't exist, a sample export that was never made,
a hash for that missing package, a test count the log disagrees with,
and a file count that doesn't match the folder:

```
$ python3 -m showyourwork check examples/report.md --evidence examples/evidence

Show Your Work - receipt check
report:   examples/report.md
evidence: examples/evidence (4 files)

[ CONTRADICTED ]  exporter.zip = a1b2c3d4a1b2...
                  -> the pair names a file absent from the evidence
[ SUPPORTED ]     exporter.py
                  -> found in the evidence as exporter.py
[ SUPPORTED ]     test_exporter.py
                  -> found in the evidence as test_exporter.py
[ SUPPORTED ]     README.md
                  -> found in the evidence as README.md
[ CONTRADICTED ]  summary.csv
                  -> named in the report, absent from the evidence
[ CONTRADICTED ]  9 tests
                  -> test totals in the evidence are [7]
[ CONTRADICTED ]  5 files
                  -> the evidence contains 4 files
[ SUPPORTED ]     report asserts a clean pass
                  -> pass markers present in the evidence, no failure markers
[ UNVERIFIABLE ]  3
                  -> does not appear in the evidence text

summary: 4 supported / 4 contradicted / 1 unverifiable (of 9 claims)
verdict: the evidence contradicts the report
```

## For agents

Give your agent this contract: run the command with `--json` against
the report it just wrote and the folder it just produced, *before* it
tells the human the work is done. The JSON card has a stable shape —
`summary` counts, a `claims` list (`kind`, `claim`, `verdict`,
`reason`), the evidence file count, the run's limits, and the doctrine
string. A CONTRADICTED row is a bug in the report or in the work; the
agent's job is to fix one of them, not to argue with the checker.

## What it checks

| Claim in the report | Checked against |
|---|---|
| A file was created | The evidence tree (path, suffix, or basename) |
| A SHA-256 hash | Recomputed SHA-256 of every evidence file; also file↔hash pairs stated in the report |
| "N files" | The actual evidence file count |
| "N tests / checks" | Test totals in evidence text (`Ran N tests`, `N passed`, `N/M`) |
| A clean pass | Failure markers in the evidence (unittest FAILED, Traceback, pytest failure summaries) |
| Bare numbers, percentages | Presence in the evidence text (weak support; absence is UNVERIFIABLE, never a contradiction) |

## Limits — read these

- **Scope is yours.** Claims are graded against the evidence exactly
  as handed over. Point `--evidence` at the deliverable itself; a
  report's "12 files" means the deliverable's 12 files, and grading it
  against a whole project folder will contradict it for the wrong
  reason.
- **Prose is not graded.** "The code is elegant" has no receipt; the
  tool will not pretend to grade it. Claims it cannot extract are not
  listed at all.
- **Hashes prove carriage, not honesty.** A SUPPORTED hash means the
  file in evidence is the file the report describes. Whether the file
  is *good* is a different layer's question.
- **Heuristics are labeled as such.** The success-marker check reads
  common test-output shapes; exotic runners may land UNVERIFIABLE.
  UNVERIFIABLE is the tool declining to guess — treat it as an
  invitation to hand over better evidence.

## Provenance

Built by the Misfit Circuit crew under the operator's Law 2: spec →
build → test → install → self-review → independent certification.
Status and findings live in BUILD-REPORT.md; the certification verdict
travels with the release, whatever it says.
