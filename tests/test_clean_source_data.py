"""Regression tests for cleaning decisions that could change the analysis."""
import sys
from pathlib import Path
import unittest

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clean_source_data import normalize, parse_bls_number, unique


class CleaningTests(unittest.TestCase):
    def test_censored_wage_is_not_an_exact_estimate(self):
        values, status, lower = parse_bls_number(pd.Series(['#', '*', '', '0', '80000']), 'a_median')
        self.assertTrue(pd.isna(values[0]))
        self.assertEqual(lower[0], 239200)
        self.assertEqual(status[0], 'top_coded_lower_bound')
        self.assertEqual(status[1], 'wage_not_available')
        self.assertEqual(status[2], 'blank_not_available')
        self.assertEqual(values[3], 0)
        self.assertEqual(values[4], 80000)

    def test_hourly_bound_uses_hourly_units(self):
        values, status, lower = parse_bls_number(pd.Series(['#']), 'h_median')
        self.assertEqual(lower[0], 115)
        self.assertTrue(pd.isna(values[0]))

    def test_unpublished_employment_is_not_zero(self):
        values, status, _ = parse_bls_number(pd.Series(['**', '0', '120']), 'tot_emp')
        self.assertTrue(pd.isna(values[0]))
        self.assertEqual(status[0], 'employment_not_available')
        self.assertEqual(values[1], 0)

    def test_unknown_tokens_fail_instead_of_silently_becoming_null(self):
        with self.assertRaises(ValueError):
            parse_bls_number(pd.Series(['unexpected']), 'tot_emp')

    def test_negative_and_infinite_values_fail(self):
        for value in ['-1', 'inf']:
            with self.assertRaises(ValueError):
                parse_bls_number(pd.Series([value]), 'tot_emp')

    def test_censoring_marker_on_employment_fails(self):
        with self.assertRaises(ValueError):
            parse_bls_number(pd.Series(['#']), 'tot_emp')

    def test_identifiers_keep_leading_zeros_and_extensions(self):
        d = normalize(pd.DataFrame({'area': [' 0600003 '], 'onet': ['11-1011.03'], 'empty': [' ']}))
        self.assertEqual(d.area[0], '0600003')
        self.assertEqual(d.onet[0], '11-1011.03')
        self.assertTrue(pd.isna(d['empty'][0]))

    def test_only_identical_duplicates_are_removed(self):
        result, removed = unique(pd.DataFrame({'id': ['a', 'a'], 'value': [1, 1]}), ['id'], 'test')
        self.assertEqual((len(result), removed), (1, 1))
        with self.assertRaises(ValueError):
            unique(pd.DataFrame({'id': ['a', 'a'], 'value': [1, 2]}), ['id'], 'test')

    def test_scopes_and_periods_are_distinct_keys(self):
        data = pd.DataFrame({'id': ['a', 'a', 'a'], 'geo': ['USA', 'GLOBAL', 'GLOBAL'],
                             'month': ['May', 'May', 'April'], 'value': [1, 2, 3]})
        result, removed = unique(data, ['id', 'geo', 'month'], 'test')
        self.assertEqual((len(result), removed), (3, 0))


if __name__ == '__main__':
    unittest.main()
