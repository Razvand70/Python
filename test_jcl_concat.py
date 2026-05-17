"""
Tests for IBM JCL concatenation job files.

Validates JCL syntax rules and structure for CONCAT.jcl and CONCAT_SORT.jcl.
"""

import re
import unittest


def load_jcl(filepath):
    with open(filepath) as f:
        return f.readlines()


def parse_statements(lines):
    """Return list of (name, operation, operands) tuples, skipping comments."""
    statements = []
    for line in lines:
        # Strip newline; JCL lines are columns 1-80
        raw = line.rstrip('\n')
        if len(raw) < 2:
            continue
        # Comment cards: // followed by * in col 3
        if raw.startswith('//*'):
            continue
        # Continuation cards start with //  (spaces after //)
        if raw.startswith('//'):
            name_field = raw[2:10].strip()
            rest = raw[10:].strip()
            parts = rest.split(None, 1)
            operation = parts[0] if parts else ''
            operands = parts[1] if len(parts) > 1 else ''
            statements.append((name_field, operation, operands))
    return statements


class TestConcatJCL(unittest.TestCase):

    def setUp(self):
        self.lines = load_jcl('/home/user/Python/CONCAT.jcl')
        self.statements = parse_statements(self.lines)

    def test_file_loads(self):
        self.assertGreater(len(self.lines), 0, "JCL file should not be empty")

    def test_job_card_present(self):
        ops = [s[1] for s in self.statements]
        self.assertIn('JOB', ops, "Must have a JOB statement")

    def test_job_card_is_first_statement(self):
        self.assertEqual(self.statements[0][1], 'JOB',
                         "JOB must be the first statement")

    def test_exec_iebgener(self):
        ops = [s[1] for s in self.statements]
        self.assertIn('EXEC', ops, "Must have an EXEC statement")
        exec_stmt = next(s for s in self.statements if s[1] == 'EXEC')
        self.assertIn('IEBGENER', exec_stmt[2],
                      "EXEC must invoke IEBGENER for simple concatenation")

    def test_sysut1_present(self):
        """SYSUT1 is the input DD for IEBGENER."""
        names = [s[0] for s in self.statements]
        self.assertIn('SYSUT1', names, "SYSUT1 DD must be defined")

    def test_sysut2_present(self):
        """SYSUT2 is the output DD for IEBGENER."""
        names = [s[0] for s in self.statements]
        self.assertIn('SYSUT2', names, "SYSUT2 DD must be defined")

    def test_sysprint_present(self):
        names = [s[0] for s in self.statements]
        self.assertIn('SYSPRINT', names, "SYSPRINT DD must be defined")

    def test_sysin_dummy(self):
        """IEBGENER requires SYSIN DD DUMMY when no control cards are needed."""
        sysin = next((s for s in self.statements if s[0] == 'SYSIN'), None)
        self.assertIsNotNone(sysin, "SYSIN DD must be present")
        self.assertIn('DUMMY', sysin[2], "SYSIN should be DUMMY for simple copy")

    def test_two_input_files_concatenated(self):
        """Both input files must appear after SYSUT1 as DD concatenation."""
        input_dsns = []
        in_sysut1 = False
        for line in self.lines:
            if line.startswith('//*'):
                continue
            name = line[2:10].strip()
            rest = line[10:].strip().upper()
            if name == 'SYSUT1':
                in_sysut1 = True
            if in_sysut1:
                # stop at next named DD that isn't a continuation
                if name and name not in ('SYSUT1',) and rest.startswith('DD'):
                    break
                if 'DSN=' in rest:
                    dsn = re.search(r'DSN=([^\s,]+)', rest)
                    if dsn:
                        input_dsns.append(dsn.group(1))
        self.assertEqual(len(input_dsns), 2,
                         f"Expected 2 input DSNs, found {input_dsns}")

    def test_output_has_new_disp(self):
        """Output dataset should be created new."""
        sysut2_line = next(
            (l for l in self.lines if l[2:10].strip() == 'SYSUT2'), None)
        self.assertIsNotNone(sysut2_line)
        # Look through continuation lines for DISP
        idx = self.lines.index(sysut2_line)
        block = ''.join(self.lines[idx:idx + 6]).upper()
        self.assertIn('NEW', block, "Output DISP should include NEW")

    def test_jcl_line_length(self):
        """JCL lines must not exceed 80 characters (col 1-80)."""
        for i, line in enumerate(self.lines, start=1):
            self.assertLessEqual(
                len(line.rstrip('\n')), 80,
                f"Line {i} exceeds 80 characters: {line.rstrip()!r}")

    def test_no_tab_characters(self):
        """JCL does not support tab characters."""
        for i, line in enumerate(self.lines, start=1):
            self.assertNotIn('\t', line,
                             f"Line {i} contains a tab character")


class TestConcatSortJCL(unittest.TestCase):

    def setUp(self):
        self.lines = load_jcl('/home/user/Python/CONCAT_SORT.jcl')
        self.statements = parse_statements(self.lines)

    def test_file_loads(self):
        self.assertGreater(len(self.lines), 0, "JCL file should not be empty")

    def test_job_card_present(self):
        ops = [s[1] for s in self.statements]
        self.assertIn('JOB', ops, "Must have a JOB statement")

    def test_exec_sort(self):
        exec_stmt = next(s for s in self.statements if s[1] == 'EXEC')
        self.assertIn('SORT', exec_stmt[2],
                      "EXEC must invoke SORT utility")

    def test_sortin_present(self):
        names = [s[0] for s in self.statements]
        self.assertIn('SORTIN', names, "SORTIN DD must be defined")

    def test_sortout_present(self):
        names = [s[0] for s in self.statements]
        self.assertIn('SORTOUT', names, "SORTOUT DD must be defined")

    def test_sysin_has_sort_fields_copy(self):
        """SORT FIELDS=COPY preserves order while concatenating."""
        content = ''.join(self.lines).upper()
        self.assertIn('SORT FIELDS=COPY', content,
                      "SYSIN must contain 'SORT FIELDS=COPY'")

    def test_two_input_files_under_sortin(self):
        """Two DD cards must appear under SORTIN."""
        input_dsns = []
        in_sortin = False
        for line in self.lines:
            if line.startswith('//*'):
                continue
            name = line[2:10].strip()
            rest = line[10:].strip().upper()
            if name == 'SORTIN':
                in_sortin = True
            if in_sortin:
                if name and name not in ('SORTIN',) and rest.startswith('DD'):
                    break
                if 'DSN=' in rest:
                    dsn = re.search(r'DSN=([^\s,]+)', rest)
                    if dsn:
                        input_dsns.append(dsn.group(1))
        self.assertEqual(len(input_dsns), 2,
                         f"Expected 2 input DSNs under SORTIN, found {input_dsns}")

    def test_jcl_line_length(self):
        for i, line in enumerate(self.lines, start=1):
            self.assertLessEqual(
                len(line.rstrip('\n')), 80,
                f"Line {i} exceeds 80 characters: {line.rstrip()!r}")

    def test_no_tab_characters(self):
        for i, line in enumerate(self.lines, start=1):
            self.assertNotIn('\t', line,
                             f"Line {i} contains a tab character")


if __name__ == '__main__':
    unittest.main(verbosity=2)
