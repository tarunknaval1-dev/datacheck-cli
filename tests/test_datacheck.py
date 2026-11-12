import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import datacheck


class DataCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp_directory.name)

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_classifies_numbers_dates_and_text(self):
        self.assertEqual(datacheck.classify_value("23"), "number")
        self.assertEqual(datacheck.classify_value("2026-11-12"), "date")
        self.assertEqual(datacheck.classify_value("hello"), "text")

    def test_infers_empty_and_mixed_columns(self):
        self.assertEqual(datacheck.infer_column_type(set()), "empty")
        self.assertEqual(
            datacheck.infer_column_type({"number", "text"}),
            "mixed"
        )

    def test_profile_reports_rows_with_wrong_field_count(self):
        csv_path = self.folder / "example.csv"
        csv_path.write_text(
            "name,age\nAsha,20\nRavi\n",
            encoding="utf-8"
        )

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            columns, rows = datacheck.profile_csv(csv_path)

        self.assertEqual(columns, ["name", "age"])
        self.assertEqual(len(rows), 2)
        self.assertIn("Rows with the wrong number of fields: 1", output.getvalue())

    def test_schema_validation_reports_invalid_values(self):
        columns = ["name", "age", "signup_date"]
        rows = [
            (2, ["Asha", "20", "2026-05-01"]),
            (3, ["", "bad", "31/12/2025"]),
        ]
        schema = {
            "required_columns": ["name"],
            "date_columns": {"signup_date": "%Y-%m-%d"},
            "numeric_ranges": {"age": {"min": 0, "max": 120}},
        }

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            datacheck.validate_schema(columns, rows, schema)

        report = output.getvalue()
        self.assertIn("'name' has 1 blank value(s)", report)
        self.assertIn("'signup_date' has 1 invalid date value(s)", report)
        self.assertIn("'age' has 1 range issue(s)", report)

    def test_markdown_and_json_reports_are_written(self):
        csv_path = self.folder / "example.csv"
        csv_path.write_text("name\nAsha\n", encoding="utf-8")
        markdown_path = self.folder / "report.md"
        json_path = self.folder / "report.json"

        with contextlib.redirect_stdout(io.StringIO()):
            datacheck.save_markdown_report(
                csv_path, "Profile status: PASS", markdown_path
            )
            datacheck.save_json_report(
                csv_path, "Profile status: PASS", json_path
            )

        self.assertTrue(markdown_path.exists())
        self.assertIn("DataCheck Report", markdown_path.read_text(encoding="utf-8"))

        saved_json = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertEqual(saved_json["csv_file"], "example.csv")
        self.assertIn("Profile status: PASS", saved_json["analysis_lines"])


if __name__ == "__main__":
    unittest.main()