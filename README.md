# DataCheck

DataCheck is a Python command-line project for checking CSV data quality.

## Day 1

- Ask for a CSV file path
- Check that the file exists and is a CSV file

## Day 2

- Display CSV column names and data row count

## Day 3

- Show non-empty and distinct value counts for each column

## Day 4

- Report missing values and their percentage for each column

## Day 5

- Detect repeated duplicate rows and show their row numbers

## Day 6

- Detect leading or trailing whitespace in values

## Day 7

- Estimate whether each column contains text, numbers, dates, mixed values, or no values

# Day 8

- Flag possible non-numeric values in columns containing numbers

# Day 9

- Validate date columns against a selected date format

# Day 10

- Check that specified columns exist and contain no blank value

# Day 11

- Check numeric columns against a chosen minimum and maximum

# Day 12

- Load required-column, date-format, and numeric-range rules from schema.json

# Day 13

- Detect CSV rows with too many or too few fields

# Day 14

- Show a summary of profiling issues and an overall pass or review status

# Day 15

- Save profiling and schema-check results as a Markdown report

# Day 16

- Export analysis results to JSON

# Day 17

- Accept a CSV path and report options from command-line arguments

# Day 18

## Run Tests

```powershell
python -m unittest discover -s tests -v

## Run the app

Requires Python 3.

```bash
python datacheck.py