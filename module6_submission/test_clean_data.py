"""Dependency-free behavioral checks for the generated evidence."""

import json
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent


class CleaningEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validation = json.loads(
            (ROOT / "outputs" / "validation.json").read_text(encoding="utf-8")
        )

    def test_pipeline_assertions_and_source_preservation(self):
        self.assertTrue(self.validation["all_assertions_passed"])
        self.assertTrue(self.validation["source_hashes_unchanged"])

    def test_full_source_row_counts(self):
        self.assertEqual(self.validation["claude"]["rows"], 1_636_573)
        self.assertEqual(self.validation["oews"]["rows"], 198_712)

    def test_california_scope_and_join_reconciliation(self):
        analysis = self.validation["analysis"]
        self.assertEqual(analysis["areas"], 28)
        self.assertEqual(analysis["base_rows"], 11_847)
        self.assertEqual(
            analysis["employment_checksum_before"],
            analysis["employment_checksum_after"],
        )

    def test_five_predeclared_records(self):
        self.assertEqual(self.validation["record_checks_passed"], 5)
        self.assertEqual(self.validation["record_checks_total"], 5)

    def test_screening_scores_are_bounded_and_missing_not_reweighted(self):
        path = ROOT / "outputs" / "analysis_california_occupation_region.csv.gz"
        data = pd.read_csv(path, usecols=["screening_eligible", "screening_score"])
        eligible = data["screening_eligible"].astype(str).str.lower().eq("true")
        self.assertTrue(data.loc[eligible, "screening_score"].between(0, 100).all())
        self.assertTrue(data.loc[~eligible, "screening_score"].isna().all())

    def test_sample_cap(self):
        sample = pd.read_csv(ROOT / "outputs" / "cleaned_sample_max_50.csv")
        self.assertLessEqual(len(sample), 50)
        self.assertGreaterEqual(len(sample), 5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
