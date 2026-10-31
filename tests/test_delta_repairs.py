"""Behavior regressions for independent review findings from October 31."""
import contextlib
import hashlib
import io
import os
from pathlib import Path
import tempfile
import unittest

from showyourwork.core import check_report, load_evidence, run_check
from showyourwork.cli import main


def rows(report, log, kind):
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, 'log.txt').write_text(log)
        return [c for c in check_report(report, load_evidence(tmp)) if c.kind == kind]


class TestCountMeaning(unittest.TestCase):
    def test_failure_subset_is_not_compared_with_total(self):
        got = rows('3 tests failed; remaining tests passed.',
                   'Ran 9 tests in 0.1s\nFAILED (failures=3)\n', 'count')
        self.assertEqual(got[0].verdict, 'SUPPORTED')
        self.assertIn('failed', got[0].reason)

    def test_unknown_failure_subtotal_stays_unknown(self):
        got = rows('3 tests failed.', 'Ran 9 tests in 0.1s\n', 'count')
        self.assertEqual(got[0].verdict, 'UNVERIFIABLE')

    def test_pytest_outcomes_supply_distinct_total_and_passed_counts(self):
        log = '======== 3 failed, 5 passed in 0.42s ========\n'
        for report, expected in [('Ran 8 tests.', 'SUPPORTED'),
                                 ('Ran 5 tests.', 'CONTRADICTED'),
                                 ('5 tests passed.', 'SUPPORTED'),
                                 ('8 tests passed.', 'CONTRADICTED')]:
            with self.subTest(report=report):
                self.assertEqual(rows(report, log, 'count')[0].verdict, expected)

    def test_fraction_about_packets_is_not_a_test_count(self):
        self.assertEqual(rows('Ran 500 tests.', '500/1000 packets delivered.', 'count')[0].verdict,
                         'UNVERIFIABLE')

    def test_explicit_test_fraction_preserves_denominator(self):
        log = '7/10 tests passed\n'
        self.assertEqual(rows('Ran 10 tests.', log, 'count')[0].verdict, 'SUPPORTED')
        self.assertEqual(rows('7 tests passed.', log, 'count')[0].verdict, 'SUPPORTED')
        self.assertEqual(rows('10 tests passed.', log, 'count')[0].verdict, 'CONTRADICTED')
        self.assertEqual(rows('7/10 tests passed.', log, 'count')[0].verdict, 'SUPPORTED')

    def test_multiple_independent_totals_do_not_invent_a_contradiction(self):
        self.assertEqual(rows('Ran 12 tests.', 'Ran 3 tests\nRan 8 tests\n', 'count')[0].verdict,
                         'UNVERIFIABLE')


class TestSuccessMeaning(unittest.TestCase):
    def test_negated_failure_is_not_an_admission(self):
        got = rows('No tests failed; all tests passed.',
                   'FAILED tests/test_a.py::test_b\n', 'success')
        self.assertEqual(got[0].verdict, 'CONTRADICTED')

    def test_subset_passes_are_not_global_clean_passes(self):
        for report in ('The remaining tests passed.', 'Some tests passed.',
                       'The rest of the tests passed.',
                       '3 suites failed; remaining suites passed.'):
            with self.subTest(report=report):
                self.assertEqual(rows(report, 'FAILED (failures=3)\n', 'success'), [])

    def test_numeric_pass_subtotal_does_not_assert_entire_run_passed(self):
        log = '===== 3 failed, 5 passed in 0.1s =====\n'
        self.assertEqual(rows('5 tests passed.', log, 'success'), [])
        self.assertEqual(rows('5 tests passed.', log, 'count')[0].verdict,
                         'SUPPORTED')
        explicit = rows('All 5 tests passed.', log, 'success')
        self.assertEqual(explicit[0].verdict, 'CONTRADICTED')

    def test_pytest_error_summary_and_collection_header_contradict_clean_pass(self):
        for log in ('===== 3 passed, 1 error in 0.42s =====\n',
                    'ERROR tests/test_import.py - ImportError\n3 passed\n'):
            with self.subTest(log=log):
                self.assertEqual(rows('All tests passed.', log, 'success')[0].verdict,
                                 'CONTRADICTED')


class TestFilesystemInputs(unittest.TestCase):
    def test_report_aliases_are_excluded_but_independent_copy_is_kept(self):
        for alias_kind in ('symlink', 'hardlink', 'root-symlink', 'copy'):
            with self.subTest(alias=alias_kind), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); ev = root / 'ev'; ev.mkdir()
                report = root / 'report.md'; report.write_text('999999 lines\n')
                evidence_path = ev
                if alias_kind == 'symlink':
                    (ev / 'alias.md').symlink_to(report)
                elif alias_kind == 'hardlink':
                    os.link(report, ev / 'alias.md')
                elif alias_kind == 'root-symlink':
                    (ev / 'report.md').write_text(report.read_text())
                    report = ev / 'report.md'
                    alias = root / 'alias'; alias.symlink_to(ev, target_is_directory=True)
                    evidence_path = alias
                else:
                    (ev / 'copy.md').write_text(report.read_text())
                result, code = run_check(report, evidence_path)
                self.assertEqual(code, 0)
                if alias_kind == 'copy':
                    self.assertEqual(result['summary']['SUPPORTED'], 1)
                    self.assertFalse(result['limits']['report_excluded_from_evidence'])
                else:
                    self.assertEqual(result['summary']['SUPPORTED'], 0)
                    self.assertTrue(result['limits']['report_excluded_from_evidence'])
                    self.assertEqual(result['evidence_files'], 0)

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'POSIX FIFO required')
    def test_fifo_root_is_input_error_and_nested_fifo_is_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); report = root / 'r.md'; report.write_text('All tests passed.')
            ev = root / 'ev'; ev.mkdir(); fifo = ev / 'stream'; os.mkfifo(fifo)
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(['check', str(report), '--evidence', str(fifo)]), 2)
            result, _ = run_check(report, ev)
            self.assertEqual(result['limits']['files_skipped_unreadable'], 1)
            self.assertEqual(result['evidence_files'], 0)


class TestTokenBoundaries(unittest.TestCase):
    def test_long_filename_is_not_cut_before_hash_pairing(self):
        with tempfile.TemporaryDirectory() as tmp:
            name = 'long_' + 'a' * 95 + '.py'; payload = b'print(1)\n'
            Path(tmp, name).write_bytes(payload)
            digest = hashlib.sha256(payload).hexdigest()
            got = [c for c in check_report(f'{name}: {digest}', load_evidence(tmp))
                   if c.kind == 'hash-pair']
            self.assertEqual(len(got), 1)
            self.assertEqual(got[0].verdict, 'SUPPORTED')
            self.assertTrue(got[0].claim.startswith(name))

    def test_comma_count_matches_in_either_direction(self):
        self.assertEqual(rows('56,474 verdicts.', '56474 verdicts', 'count')[0].verdict,
                         'SUPPORTED')

    def test_model_version_is_not_a_number_claim(self):
        self.assertEqual(rows('Used model muse-spark-1.3 for drafting.', '', 'number'), [])


if __name__ == '__main__':
    unittest.main()
