import hashlib
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from showyourwork.core import check_report, load_evidence, run_check
from showyourwork.cli import main


def make_evidence(root, files):
    """files: {relpath: bytes-or-str}"""
    for rel, content in files.items():
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        mode = "wb" if isinstance(content, bytes) else "w"
        with open(path, mode) as fh:
            fh.write(content)
    return load_evidence(root)


def verdicts(claims, kind=None):
    return {c.claim: c.verdict for c in claims if kind is None or c.kind == kind}


class FileClaimTests(unittest.TestCase):
    def test_existing_and_missing_files(self):
        with tempfile.TemporaryDirectory() as d:
            ev = make_evidence(d, {"app.py": "print(1)\n", "notes.md": "hi\n"})
            claims = check_report("Built app.py and notes.md plus ghost.py.", ev)
            v = verdicts(claims, "file")
            self.assertEqual(v["app.py"], "SUPPORTED")
            self.assertEqual(v["notes.md"], "SUPPORTED")
            self.assertEqual(v["ghost.py"], "CONTRADICTED")

    def test_nested_path_found_by_suffix(self):
        with tempfile.TemporaryDirectory() as d:
            ev = make_evidence(d, {"src/deep/tool.py": "x = 1\n"})
            claims = check_report("Wrote src/deep/tool.py today.", ev)
            self.assertEqual(verdicts(claims, "file")["src/deep/tool.py"], "SUPPORTED")

    def test_non_file_tokens_ignored(self):
        with tempfile.TemporaryDirectory() as d:
            ev = make_evidence(d, {"a.py": "x\n"})
            claims = check_report("Used model muse-spark-1.3, e.g. for drafting.", ev)
            self.assertEqual(verdicts(claims, "file"), {})

    def test_sentence_final_filename_still_a_claim(self):
        # Regression: a filename ending a sentence ("...plus ghost.py.")
        # must not be swallowed by its own full stop.
        with tempfile.TemporaryDirectory() as d:
            ev = make_evidence(d, {"a.py": "x\n"})
            claims = check_report("Created a.py and missing.py.", ev)
            v = verdicts(claims, "file")
            self.assertEqual(v["a.py"], "SUPPORTED")
            self.assertEqual(v["missing.py"], "CONTRADICTED")


class HashClaimTests(unittest.TestCase):
    def test_real_hash_supported_wrong_hash_contradicted(self):
        payload = b"payload\n"
        good = hashlib.sha256(payload).hexdigest()
        bad = hashlib.sha256(b"other\n").hexdigest()
        with tempfile.TemporaryDirectory() as d:
            ev = make_evidence(d, {"data.bin": payload})
            claims = check_report(f"hash {good} and also {bad}", ev)
            v = verdicts(claims, "hash")
            self.assertEqual(v[f"SHA-256 {good[:12]}..."], "SUPPORTED")
            self.assertEqual(v[f"SHA-256 {bad[:12]}..."], "CONTRADICTED")

    def test_pair_mismatch_contradicted(self):
        payload = b"real\n"
        wrong = hashlib.sha256(b"claimed\n").hexdigest()
        with tempfile.TemporaryDirectory() as d:
            ev = make_evidence(d, {"out.zip": payload})
            claims = check_report(f"out.zip  {wrong}", ev)
            v = verdicts(claims, "hash-pair")
            self.assertEqual(v[f"out.zip = {wrong[:12]}..."], "CONTRADICTED")

    def test_hash_case_insensitive_text_match(self):
        # A hash printed UPPERCASE in the report, lowercase in an
        # evidence receipt, for a file not itself in evidence: the
        # text match must still support it (case is not a lie).
        digest = hashlib.sha256(b"external\n").hexdigest()
        with tempfile.TemporaryDirectory() as d:
            ev = make_evidence(d, {"receipt.txt": f"digest was {digest}\n"})
            claims = check_report(f"Final hash: {digest.upper()}", ev)
            v = verdicts(claims, "hash")
            self.assertEqual(v[f"SHA-256 {digest[:12]}..."], "SUPPORTED")

    def test_pair_match_supported(self):
        payload = b"real\n"
        right = hashlib.sha256(payload).hexdigest()
        with tempfile.TemporaryDirectory() as d:
            ev = make_evidence(d, {"out.zip": payload})
            claims = check_report(f"out.zip: {right}", ev)
            v = verdicts(claims, "hash-pair")
            self.assertEqual(v[f"out.zip = {right[:12]}..."], "SUPPORTED")


class CountClaimTests(unittest.TestCase):
    def test_file_count(self):
        with tempfile.TemporaryDirectory() as d:
            ev = make_evidence(d, {"a.py": "x", "b.py": "y"})
            ok = check_report("Shipped 2 files.", ev)
            self.assertEqual(verdicts(ok, "count")["2 files"], "SUPPORTED")
            bad = check_report("Shipped 5 files.", ev)
            self.assertEqual(verdicts(bad, "count")["5 files"], "CONTRADICTED")

    def test_test_count_from_log(self):
        with tempfile.TemporaryDirectory() as d:
            ev = make_evidence(d, {"log.txt": "Ran 8 tests in 0.2s\n\nOK\n"})
            ok = check_report("All 8 tests pass.", ev)
            self.assertEqual(verdicts(ok, "count")["8 tests"], "SUPPORTED")
            bad = check_report("All 12 tests pass.", ev)
            self.assertEqual(verdicts(bad, "count")["12 tests"], "CONTRADICTED")

    def test_count_without_basis_unverifiable(self):
        with tempfile.TemporaryDirectory() as d:
            ev = make_evidence(d, {"a.py": "x"})
            claims = check_report("Produced 42 pages of docs.", ev)
            self.assertEqual(verdicts(claims, "count")["42 pages"], "UNVERIFIABLE")


class SuccessClaimTests(unittest.TestCase):
    def test_success_vs_traceback_contradicted(self):
        with tempfile.TemporaryDirectory() as d:
            ev = make_evidence(d, {"log.txt": "Traceback (most recent call last):\n boom\n"})
            claims = check_report("Everything passed cleanly.", ev)
            v = verdicts(claims, "success")
            self.assertEqual(v["report asserts a clean pass"], "CONTRADICTED")

    def test_success_vs_ok_log_supported(self):
        with tempfile.TemporaryDirectory() as d:
            ev = make_evidence(d, {"log.txt": "Ran 3 tests in 0.1s\n\nOK\n"})
            claims = check_report("All tests passed.", ev)
            v = verdicts(claims, "success")
            self.assertEqual(v["report asserts a clean pass"], "SUPPORTED")

    def test_admitted_failure_skips_success_claim(self):
        with tempfile.TemporaryDirectory() as d:
            ev = make_evidence(d, {"log.txt": "FAILED (failures=2)\n"})
            claims = check_report("Mostly passed but 2 failed.", ev)
            self.assertEqual(verdicts(claims, "success"), {})


class NumberClaimTests(unittest.TestCase):
    def test_number_appears_and_absent(self):
        with tempfile.TemporaryDirectory() as d:
            ev = make_evidence(d, {"r.txt": "total 771 tokens used\n"})
            claims = check_report("Used 771 tokens across 99 calls.", ev)
            v = verdicts(claims, "number")
            self.assertEqual(v["771"], "SUPPORTED")
            self.assertEqual(v["99"], "UNVERIFIABLE")

    def test_algo_label_is_not_a_number_claim(self):
        # Regression: the "256" in "SHA-256:" is a label, not a claim.
        with tempfile.TemporaryDirectory() as d:
            ev = make_evidence(d, {"r.txt": "nothing numeric\n"})
            claims = check_report("Digest, SHA-256: none taken.", ev)
            self.assertNotIn("256", verdicts(claims, "number"))

    def test_number_inside_a_word_does_not_match(self):
        # Regression: a bare "3" must not match the 3 in "python3".
        with tempfile.TemporaryDirectory() as d:
            ev = make_evidence(d, {"r.txt": "run it with python3 -m x\n"})
            claims = check_report("Handles 3 formats.", ev)
            self.assertEqual(verdicts(claims, "number")["3"], "UNVERIFIABLE")


class AuditFixTests(unittest.TestCase):
    """Regression tests for the v0.1 independent audit (AUDIT-v0.1.md)."""

    def test_f1_ordinary_failure_admission_not_a_success_claim(self):
        with tempfile.TemporaryDirectory() as d:
            ev = make_evidence(d, {"log.txt": "FAILED (failures=3)\n"})
            claims = check_report(
                "Ran the suite: 3 tests failed; remaining tests passed.", ev)
            self.assertEqual(verdicts(claims, "success"), {})

    def test_f2_pytest_short_summary_is_a_failure_marker(self):
        with tempfile.TemporaryDirectory() as d:
            ev = make_evidence(d, {
                "log.txt": "FAILED tests/test_x.py::test_b - AssertionError\n"})
            claims = check_report("All tests passed.", ev)
            self.assertEqual(
                verdicts(claims, "success")["report asserts a clean pass"],
                "CONTRADICTED")

    def test_f3_prose_passed_is_not_a_test_total(self):
        with tempfile.TemporaryDirectory() as d:
            ev = make_evidence(d, {"essay.txt": "500 passed the entrance exam.\n"})
            claims = check_report("Ran 500 tests.", ev)
            self.assertEqual(verdicts(claims, "count")["500 tests"],
                             "UNVERIFIABLE")

    def test_f4_two_files_one_hash_no_pair_stated(self):
        payload = b"app\n"
        digest = hashlib.sha256(payload).hexdigest()
        with tempfile.TemporaryDirectory() as d:
            ev = make_evidence(d, {"app.py": payload, "lib.py": "x = 2\n"})
            claims = check_report(
                f"Built app.py and lib.py - SHA-256: {digest}", ev)
            self.assertEqual(verdicts(claims, "hash-pair"), {})
            self.assertEqual(
                verdicts(claims, "hash")[f"SHA-256 {digest[:12]}..."],
                "SUPPORTED")

    def test_f5_large_file_disclosed_as_unsearched(self):
        with tempfile.TemporaryDirectory() as d:
            big = os.path.join(d, "big.txt")
            with open(big, "w") as fh:
                fh.write("x" * 1_100_000)
            ev = load_evidence(d)
            self.assertIn("big.txt", ev.text_unsearched)

    def test_f6_report_inside_evidence_does_not_grade_itself(self):
        with tempfile.TemporaryDirectory() as d:
            report = os.path.join(d, "report.md")
            with open(report, "w") as fh:
                fh.write("Wrote 999999 lines of code.\n")
            with open(os.path.join(d, "real.txt"), "w") as fh:
                fh.write("nothing\n")
            result, _code = run_check(report, d)
            self.assertTrue(result["limits"]["report_excluded_from_evidence"])
            nums = {c["claim"]: c["verdict"] for c in result["claims"]
                    if c["kind"] == "number"}
            self.assertEqual(nums.get("999999"), "UNVERIFIABLE")

    def test_f7_count_claim_comma_retry(self):
        with tempfile.TemporaryDirectory() as d:
            ev = make_evidence(d, {"r.txt": "total 56,474 verdicts recorded\n"})
            claims = check_report("Issued 56474 verdicts.", ev)
            self.assertEqual(verdicts(claims, "count")["56474 verdicts"],
                             "SUPPORTED")

    def test_zero_claim_verdict_line(self):
        with tempfile.TemporaryDirectory() as d:
            report = os.path.join(d, "r.md")
            with open(report, "w") as fh:
                fh.write("It went fine, trust me.\n")
            result, code = run_check(report, d)
            self.assertEqual(result["summary"]["total"], 0)
            self.assertEqual(code, 0)


class CliTests(unittest.TestCase):
    def test_exit_codes_and_json(self):
        with tempfile.TemporaryDirectory() as d:
            ev_dir = os.path.join(d, "ev")
            os.makedirs(ev_dir)
            with open(os.path.join(ev_dir, "a.py"), "w") as fh:
                fh.write("x\n")
            good = os.path.join(d, "good.md")
            with open(good, "w") as fh:
                fh.write("Created a.py. 1 file total.\n")
            bad = os.path.join(d, "bad.md")
            with open(bad, "w") as fh:
                fh.write("Created a.py and missing.py.\n")
            self.assertEqual(main(["check", good, "--evidence", ev_dir]), 0)
            self.assertEqual(main(["check", bad, "--evidence", ev_dir]), 1)
            self.assertEqual(main(["check", os.path.join(d, "nope.md"),
                                   "--evidence", ev_dir]), 2)

    def test_run_check_schema(self):
        with tempfile.TemporaryDirectory() as d:
            ev_dir = os.path.join(d, "ev")
            os.makedirs(ev_dir)
            with open(os.path.join(ev_dir, "a.py"), "w") as fh:
                fh.write("x\n")
            report = os.path.join(d, "r.md")
            with open(report, "w") as fh:
                fh.write("Created a.py.\n")
            result, code = run_check(report, ev_dir)
            self.assertEqual(code, 0)
            blob = json.dumps(result)
            self.assertIn("doctrine", json.loads(blob))
            self.assertEqual(result["summary"]["total"],
                             len(result["claims"]))


if __name__ == "__main__":
    unittest.main()
