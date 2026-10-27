"""Integration safety tests using invented manuscript fixtures."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from integrate_lanl_replication_section import integrate

OLD = r'''\section{LANL}
\subsection{Preregistered Second-Cohort Replication}
Protocol frozen.
\textbf{Replication status at the time of drafting:} The second-cohort
execution workflow and tests have been committed, but the replication
outcome is not reported here pending verified workflow artifacts. Even
a successful replication would not establish a false-positive rate.

\section{Threats to Validity}
Limits.
'''

class IntegrationTests(unittest.TestCase):
    def test_replace_only_pending_paragraph(self):
        new = integrate(OLD)
        self.assertIn(r'\input{lanl-second-cohort-auto}', new)
        self.assertIn('Protocol frozen.', new)
        self.assertIn('Limits.', new)
        self.assertNotIn('pending verified workflow artifacts', new)

    def test_idempotent(self):
        self.assertEqual(integrate(integrate(OLD)), integrate(OLD))

    def test_fail_closed_on_unrecognized_status(self):
        with self.assertRaisesRegex(ValueError, 'status paragraph changed'):
            integrate(OLD.replace('pending verified workflow artifacts', 'not available'))

    def test_fail_closed_on_missing_marker(self):
        with self.assertRaisesRegex(ValueError, 'not found'):
            integrate(OLD.replace(r'\textbf{Replication status at the time of drafting:}', 'Results'))

    def test_current_manuscript_two_path_include_is_idempotent(self):
        current = r'''\IfFileExists{lanl-second-cohort-auto.tex}{%
  \input{lanl-second-cohort-auto.tex}%
}{%
  \input{paper/lanl-second-cohort-auto.tex}%
}
'''
        self.assertEqual(integrate(current), current)

    def test_incomplete_current_include_rejected(self):
        current = r'''\IfFileExists{lanl-second-cohort-auto.tex}{%
  \input{lanl-second-cohort-auto.tex}%
}{% missing fallback
}
'''
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            integrate(current)

    def test_duplicate_input_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            integrate(integrate(OLD) + r'\input{lanl-second-cohort-auto}')

if __name__ == '__main__':
    unittest.main()
