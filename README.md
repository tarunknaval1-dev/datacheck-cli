# DataCheck

DataCheck is a Python command-line tool that profiles CSV files, checks data quality, and saves analysis reports.

## Features

- Show CSV row and column counts
- Summarize each column’s estimated type, missing values, and distinct values
- Detect duplicate rows and rows with incorrect field counts
- Flag leading or trailing whitespace
- Flag possible non-numeric values in mixed columns
- Validate required columns, date formats, and numeric ranges using a JSON schema
- Export analysis results to Markdown and JSON
- Run automated tests with Python’s built-in `unittest`

## Requirements

- Python 3
- No external packages required

## Project structure

```text
datacheck-cli/
├── datacheck.py
├── schema.json
├── sample_data.csv
├── tests/
│   └── test_datacheck.py
├── .gitignore
└── README.md
```

The app creates `datacheck_report.md` and `datacheck_report.json` when it runs. These generated reports are ignored by Git because they may contain values from the CSV being analyzed.

## Run DataCheck

Open a terminal in the project folder.

Analyze the included sample:

```powershell
python datacheck.py sample_data.csv
```

You can also start the program without a filename and enter one when prompted:

```powershell
python datacheck.py
```

Use `--help` to see all options:

```powershell
python datacheck.py --help
```

## Command-line options

Use a different schema file:

```powershell
python datacheck.py sample_data.csv --schema another_schema.json
```

Run without schema checks:

```powershell
python datacheck.py sample_data.csv --no-schema
```

Choose where the reports are saved:

```powershell
python datacheck.py sample_data.csv --markdown-report reports\result.md --json-report reports\result.json
```

Display results without writing reports:

```powershell
python datacheck.py sample_data.csv --no-reports
```

## Configure validation rules

By default, DataCheck looks for `schema.json` beside `datacheck.py`.

Example schema:

```json
{
  "required_columns": ["name", "email"],
  "date_columns": {
    "signup_date": "%Y-%m-%d"
  },
  "numeric_ranges": {
    "age": {
      "min": 0,
      "max": 120
    }
  }
}
```

Column names should match the CSV headers; matching ignores capitalization. Supported date formats are `%Y-%m-%d`, `%d/%m/%Y`, `%m/%d/%Y`, `%d-%m-%Y`, and `%Y/%m/%d`.

## Run the tests

From the project folder:

```powershell
python -m unittest discover -s tests -v
```

## Limitations

- Only CSV files are supported.
- The estimated column types and possible invalid-number warnings are heuristics; they may need review.
- Schema validation checks only the rules configured in `schema.json`.
- Blank values are reported separately and skipped by date and numeric range checks.
- The generated reports include the analysis output and may contain example values from the CSV.

## Author

Tarun kumar naval