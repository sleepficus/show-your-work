# Show Your Work v0.1.2 — targeted closure

**BOUNDED_TARGETED_CLOSURE_PASS.** Ready for assisted public trials within the published deterministic-checker limits. This closes the concrete delta findings on the frozen bytes below; it is not universal certification, proof of evidence honesty, or a claim that exit0 approves the underlying work.

Independent reviewer: Command (Codex). The original v0.1.1 audit, source freeze and failing receipts remain unchanged. No implementation/public edits were made by the auditor. Main/builder owns the repair.

## Candidate identity

This was a v0.1.2 **working-tree candidate based on926962ce521bbada29a31ddea8fb6b98bcbef50d**, not that commit alone. The exact repaired files were checked against the builder manifest before and after replay:

| File | SHA-256 |
|---|---|
| showyourwork/core.py | 026f209369b1d64ef79a2035bb6c03afd6e513f60d7fb92f491d6fffd0c5785e |
| showyourwork/cli.py | 863a1b31d6aa7635602da6a7ad93ecc3dd9f38606a741abf5165a7cb96c4ac81 |
| showyourwork/__init__.py | d0e4f9ab88943664acdce1eacba1952fdeaa82b77b4630c79785436a1599fcc9 |
| tests/test_delta_repairs.py | 77950107ae4b95a83a3b8bd285cb3ad287bb6034aebcee2f844fe32139cbce7c |

Complete21-file snapshot manifest SHA-256: `aa6fb99e9d1acf9a051f93202a190389865a1db12ea578c4a41b785c4ca562c1`. Snapshot tar SHA-256: `11902c5164ee715231187ebf2d734225652c5465b0f1a8f26916ec1992acda01`.

## Independent results

| Scope | Observed result |
|---|---|
| Candidate's complete unittest suite |42 tests, OK|
| Exact original core replay|31/31 expectations held|
| CLI/F6 replay in repaired-candidate mode|10/10 cases held|
| Proportional changed-semantics boundaries|7/7 held|
| Source preservation|21 candidate snapshot files and original20-file freeze unchanged; all four live pinned repair files still matched after replay|

These counts are separate finite checks, not a model-generated grade, statistical coverage claim or universal correctness rate. Replays used actual subprocess CLI calls, JSON cards, file identities and fresh external fixture folders; no mocked checker outputs.

## Catches, misses and false positives

- **Qualified counts:** `3 tests failed` is compared with failure counts rather than total9; the original honest-report false contradiction is gone.
- **Mixed pytest totals:**3 failed plus5 passed supports total8 and contradicts total5; unrelated packet fractions no longer supply test totals.
- **Clean-pass meaning:** negated failure assertions remain checkable; remaining/subset/suite wording no longer invents an all-pass claim.
- **Pytest errors:** the previously missed error trailer and collection header now contradict an all-pass claim.
- **Pair integrity:** long filenames are matched whole; correct full pairs support and a new wrong-hash long-name boundary still contradicts the actual name. No clipped filename is invented.
- **Self-exclusion:** direct paths, file symlinks, hardlinks and root aliases exclude the same report file. Independent same-byte evidence remains usable, including the additional independent-symlink control.
- **CLI/type behavior:** FIFO roots are rejected as input errors; valid cards and missing-path controls retain their contracts. Missing-input errors remain ordinary stderr, which was never falsely flagged as breaking a JSON error-envelope promise.
- **Safe/cosmetic limits also improved:** reverse comma formatting and model-version noise now pass the original scenarios. An ordinary measured decimal still remains a weak numeric claim.

No unresolved material miss or false contradiction was found within this declared replay/boundary set and focused diff. This does not say none exists outside it.

## Main's adjacent case and additional boundaries

`5 tests passed.` against a mixed3-failed/5-passed log yields a supported passed subtotal, no global success assertion, exit0. `All 5 tests passed.` retains its explicit global assertion and is contradicted, exit1. The first exit0 validates the report's receipt, not the failing suite.

The other five boundaries held: reversed pytest status order; explicit zero-failure claim against failure evidence; wrong digest on a long filename; independent evidence reached by symlink; and ordinary decimal1.3 retained as a numeric claim.

## Evidence and reproducibility

Private full receipts remain under this closure directory: `core-replay/`, `cli-replay/`, `boundary-checks/`, `BOUNDARY-RESULTS.json`, `FOCUSED-DIFF.patch`, `SOURCE-FREEZE.json`, and `SOURCE-MANIFEST.sha256`. Full unit stdout/stderr are under `core-replay/`.

The portable source/out-parameterized scripts are retained separately alongside the original v0.1.1 findings. Use a new results path for each candidate. The scripts recreate filesystem aliases and FIFO fixtures; byte archives do not preserve hardlink identity and must not read a FIFO as a regular file. Public packaging should use the sanitized summaries and scripts rather than machine-specific raw CLI receipts.

Limits remain: receipt carriage is not truth or test quality; not every prose claim is extracted; custom/ambiguous/multiple-run logs can remain unverifiable; a clean exit only means no contradiction was found. No external customer/participant trial or cross-platform certification was performed in this audit. Main owns the demo, invitation, hiring story and publication decisions.

Questions for Stephen: none for this bounded closure.
