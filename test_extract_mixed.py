"""
Tests for EXTRACT_MIXED.jcl - DFSORT job that extracts records
where the same NUMCPT has both negative and positive AMOUNT values.

JCL logic (4 DFSORT steps):
  STEP01 - unique NUMCPTs with >= 1 negative amount  -> &&TEMPNEG
  STEP02 - unique NUMCPTs with >= 1 positive amount  -> &&TEMPPOS
  STEP03 - JOINKEYS intersection (PAIRED only)       -> &&TEMPBOTH
  STEP04 - JOINKEYS original vs TEMPBOTH, full recs  -> MY.OUTPUT.MIXED
"""

import unittest
from collections import defaultdict


# ---------------------------------------------------------------------------
# Python simulation of the 4-step DFSORT logic
# ---------------------------------------------------------------------------

def extract_mixed_numcpts(records):
    """
    records: list of (numcpt: str, amount: int)
    returns: list of matching records sorted by numcpt
    """
    has_neg = {n for n, a in records if a < 0}       # STEP01 INCLUDE LT,0
    has_pos = {n for n, a in records if a > 0}       # STEP02 INCLUDE GT,0
    both = has_neg & has_pos                          # STEP03 JOINKEYS intersection
    result = [(n, a) for n, a in records if n in both]  # STEP04 filter
    return sorted(result, key=lambda x: x[0])


# ---------------------------------------------------------------------------
# Business-logic tests (validate the algorithm, independent of JCL syntax)
# ---------------------------------------------------------------------------

class TestExtractMixedLogic(unittest.TestCase):

    def test_basic_mixed_numcpt_included(self):
        records = [('ACCT001   ', 100), ('ACCT001   ', -50),
                   ('ACCT002   ', 200)]
        result = extract_mixed_numcpts(records)
        numcpts = {r[0] for r in result}
        self.assertIn('ACCT001   ', numcpts)
        self.assertNotIn('ACCT002   ', numcpts)

    def test_only_negative_excluded(self):
        records = [('ACCT003   ', -100), ('ACCT003   ', -200)]
        self.assertEqual(extract_mixed_numcpts(records), [])

    def test_only_positive_excluded(self):
        records = [('ACCT004   ', 100), ('ACCT004   ', 200)]
        self.assertEqual(extract_mixed_numcpts(records), [])

    def test_zero_alone_does_not_qualify(self):
        """Zero is neither LT 0 nor GT 0 — numcpt must not appear."""
        records = [('ACCT005   ', 0), ('ACCT005   ', 100)]
        self.assertEqual(extract_mixed_numcpts(records), [])

    def test_zero_alongside_both_signs_included(self):
        """Zero record is still returned when numcpt qualifies."""
        records = [('ACCT006   ', 0), ('ACCT006   ', 50), ('ACCT006   ', -50)]
        result = extract_mixed_numcpts(records)
        self.assertEqual(len(result), 3)

    def test_multiple_qualifying_numcpts(self):
        records = [
            ('ACCT001   ',  100), ('ACCT001   ', -100),
            ('ACCT002   ', -200),
            ('ACCT003   ',  300), ('ACCT003   ', -300),
            ('ACCT004   ',  400),
        ]
        result = extract_mixed_numcpts(records)
        numcpts = {r[0] for r in result}
        self.assertIn('ACCT001   ', numcpts)
        self.assertIn('ACCT003   ', numcpts)
        self.assertNotIn('ACCT002   ', numcpts)
        self.assertNotIn('ACCT004   ', numcpts)
        self.assertEqual(len(result), 4)

    def test_all_records_returned_for_qualifying_numcpt(self):
        """Every record for a qualifying NUMCPT must appear — not just one."""
        records = [('ACCT007   ', 10), ('ACCT007   ', 20),
                   ('ACCT007   ', -5), ('ACCT007   ', -15)]
        self.assertEqual(len(extract_mixed_numcpts(records)), 4)

    def test_empty_input(self):
        self.assertEqual(extract_mixed_numcpts([]), [])

    def test_output_sorted_by_numcpt(self):
        records = [('ACCT003   ', 10), ('ACCT003   ', -1),
                   ('ACCT001   ',  5), ('ACCT001   ', -2)]
        result = extract_mixed_numcpts(records)
        keys = [r[0] for r in result]
        self.assertEqual(keys, sorted(keys))

    def test_single_record_cannot_qualify(self):
        """One record can't have both signs — must be excluded."""
        records = [('ACCT008   ', -999)]
        self.assertEqual(extract_mixed_numcpts(records), [])

    def test_large_mix(self):
        records = [(f'ACCT{i:06}', v)
                   for i in range(1, 6)
                   for v in [i * 10, -(i * 5)]]
        result = extract_mixed_numcpts(records)
        self.assertEqual(len(result), 10)   # all 5 numcpts qualify, 2 recs each


# ---------------------------------------------------------------------------
# JCL structural tests
# ---------------------------------------------------------------------------

JCL_PATH = '/home/user/Python/EXTRACT_MIXED.jcl'


class TestExtractMixedJCL(unittest.TestCase):

    def setUp(self):
        with open(JCL_PATH) as f:
            self.lines = f.readlines()
        self.content = ''.join(self.lines).upper()

    def test_file_loads(self):
        self.assertGreater(len(self.lines), 0)

    def test_job_card_is_first_non_comment(self):
        non_comment = [l for l in self.lines if not l.startswith('//*')]
        self.assertIn('JOB', non_comment[0][2:])

    def test_exactly_four_sort_steps(self):
        exec_lines = [l for l in self.lines
                      if not l.startswith('//*') and 'EXEC PGM=SORT' in l]
        self.assertEqual(len(exec_lines), 4,
                         "Must have exactly 4 EXEC PGM=SORT steps")

    def test_include_negative_condition(self):
        self.assertIn('LT,0', self.content,
                      "STEP01 must INCLUDE COND with LT,0 for negative amounts")

    def test_include_positive_condition(self):
        self.assertIn('GT,0', self.content,
                      "STEP02 must INCLUDE COND with GT,0 for positive amounts")

    def test_sum_fields_none_deduplicates_numcpt(self):
        self.assertIn('SUM FIELDS=NONE', self.content)

    def test_joinkeys_appears_in_steps_3_and_4(self):
        joinkey_lines = [l for l in self.lines if 'JOINKEYS' in l.upper()]
        self.assertGreaterEqual(len(joinkey_lines), 4,
                                "JOINKEYS must appear in both STEP03 and STEP04")

    def test_three_temp_datasets(self):
        self.assertIn('&&TEMPNEG', self.content)
        self.assertIn('&&TEMPPOS', self.content)
        self.assertIn('&&TEMPBOTH', self.content)

    def test_temp_datasets_passed_between_steps(self):
        self.assertIn('PASS', self.content,
                      "Temp datasets need DISP=PASS to survive across steps")

    def test_temp_datasets_deleted_after_use(self):
        self.assertIn('OLD,DELETE', self.content,
                      "Temp datasets should be deleted once consumed")

    def test_final_output_catalogued(self):
        self.assertIn('CATLG', self.content,
                      "Final output dataset must use DISP CATLG")

    def test_reformat_full_80_byte_record(self):
        self.assertIn('REFORMAT FIELDS=(F1:1,80)', self.content,
                      "STEP04 REFORMAT must recover the full 80-byte input record")

    def test_outrec_extracts_numcpt_only(self):
        self.assertIn('OUTREC FIELDS=(1,10)', self.content,
                      "Temp files must contain only the 10-byte NUMCPT key")

    def test_line_length_max_80(self):
        for i, line in enumerate(self.lines, 1):
            self.assertLessEqual(
                len(line.rstrip('\n')), 80,
                f"Line {i} exceeds 80 characters: {line.rstrip()!r}")

    def test_no_tab_characters(self):
        for i, line in enumerate(self.lines, 1):
            self.assertNotIn('\t', line, f"Line {i} contains a tab character")

    def test_sysin_closed_with_delimiter(self):
        """Each inline SYSIN block must end with /* delimiter."""
        delimiter_count = sum(1 for l in self.lines if l.startswith('/*'))
        self.assertGreaterEqual(delimiter_count, 2,
                                "Each SYSIN DD * block needs a /* delimiter")


if __name__ == '__main__':
    unittest.main(verbosity=2)
