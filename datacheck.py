import csv
import json
import math
from datetime import date, datetime
from pathlib import Path


DATE_FORMATS = [
    ("YYYY-MM-DD", "%Y-%m-%d"),
    ("DD/MM/YYYY", "%d/%m/%Y"),
    ("MM/DD/YYYY", "%m/%d/%Y"),
    ("DD-MM-YYYY", "%d-%m-%Y"),
    ("YYYY/MM/DD", "%Y/%m/%d"),
]
SUPPORTED_DATE_FORMATS = {fmt for _, fmt in DATE_FORMATS}


def choose_csv_file():
    file_input = input("Enter the path to a CSV file: ").strip().strip("\"'")
    if not file_input:
        print("File path cannot be empty.")
        return None

    csv_path = Path(file_input).expanduser()
    if not csv_path.is_absolute() and not csv_path.exists():
        csv_path = Path(__file__).parent / csv_path

    try:
        if not csv_path.exists():
            print(f"File not found: {csv_path}")
            return None
        if not csv_path.is_file():
            print("Please enter a file path, not a folder.")
            return None
        if csv_path.suffix.lower() != ".csv":
            print("The selected file must have a .csv extension.")
            return None
        return csv_path.resolve()
    except OSError as error:
        print(f"Could not access that file: {error}")
        return None


def classify_value(value):
    try:
        number = float(value)
        if math.isfinite(number):
            return "number"
    except ValueError:
        pass

    try:
        date.fromisoformat(value)
        return "date"
    except ValueError:
        pass

    for _, date_format in DATE_FORMATS:
        try:
            datetime.strptime(value, date_format)
            return "date"
        except ValueError:
            continue

    return "text"


def infer_column_type(value_types):
    if not value_types:
        return "empty"
    if len(value_types) == 1:
        return next(iter(value_types))
    return "mixed"


def profile_csv(csv_path):
    try:
        with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.reader(file)

            try:
                columns = next(reader)
            except StopIteration:
                print("The CSV file is empty.")
                return None, None

            column_stats = [
                {
                    "non_empty": 0,
                    "missing": 0,
                    "unique": set(),
                    "types": set(),
                    "whitespace_count": 0,
                    "whitespace_examples": [],
                    "text_count": 0,
                    "text_examples": [],
                }
                for _ in columns
            ]

            data_rows = []
            seen_rows = {}
            duplicate_examples = []
            malformed_rows = []
            row_count = 0

            for row_number, row in enumerate(reader, start=2):
                if not row or all(not value.strip() for value in row):
                    continue

                row_count += 1
                data_rows.append((row_number, row))

                if len(row) != len(columns):
                    malformed_rows.append((row_number, len(row)))

                for index in range(len(columns)):
                    value = row[index] if index < len(row) else ""
                    cleaned = value.strip()
                    stats = column_stats[index]

                    if value != cleaned:
                        stats["whitespace_count"] += 1
                        if len(stats["whitespace_examples"]) < 3:
                            stats["whitespace_examples"].append(
                                (row_number, value)
                            )

                    if cleaned:
                        stats["non_empty"] += 1
                        stats["unique"].add(cleaned)
                        value_type = classify_value(cleaned)
                        stats["types"].add(value_type)

                        if value_type == "text":
                            stats["text_count"] += 1
                            if len(stats["text_examples"]) < 5:
                                stats["text_examples"].append(
                                    (row_number, cleaned)
                                )
                    else:
                        stats["missing"] += 1

                normalized_row = tuple(value.strip() for value in row)
                if normalized_row in seen_rows:
                    duplicate_examples.append(
                        (seen_rows[normalized_row], row_number)
                    )
                else:
                    seen_rows[normalized_row] = row_number

    except (OSError, UnicodeError, csv.Error) as error:
        print(f"Could not read the CSV file: {error}")
        return None, None

    print(f"\nCSV profile: {csv_path.name}")
    print(f"Rows: {row_count}")
    print(f"Columns: {len(columns)}")
    print("\nColumn details:")

    for index, column in enumerate(columns):
        name = column.strip() or f"(unnamed column {index + 1})"
        stats = column_stats[index]
        missing_percent = stats["missing"] / row_count * 100 if row_count else 0

        print(
            f"- {name}: "
            f"type={infer_column_type(stats['types'])}, "
            f"{stats['non_empty']} non-empty, "
            f"{stats['missing']} missing ({missing_percent:.1f}%), "
            f"{len(stats['unique'])} distinct, "
            f"{stats['whitespace_count']} whitespace issue(s)"
        )

        for issue_row, value in stats["whitespace_examples"]:
            print(f"    Whitespace at row {issue_row}: {value!r}")

        types = stats["types"]
        if "number" in types and "text" in types and "date" not in types:
            print(f"    Possible invalid numeric values: {stats['text_count']}")
            for issue_row, value in stats["text_examples"]:
                print(f"      Row {issue_row}: {value!r}")
            extra = stats["text_count"] - len(stats["text_examples"])
            if extra:
                print(f"      ...and {extra} more")

    print(f"\nDuplicate rows: {len(duplicate_examples)}")
    for first_row, repeated_row in duplicate_examples[:5]:
        print(f"- Row {first_row} repeats row {repeated_row}")
    if len(duplicate_examples) > 5:
        print(f"- ...and {len(duplicate_examples) - 5} more")

    print(f"\nRows with the wrong number of fields: {len(malformed_rows)}")
    for row_number, field_count in malformed_rows[:5]:
        print(
            f"- Row {row_number}: expected {len(columns)} fields, "
            f"found {field_count}"
        )
    if len(malformed_rows) > 5:
        print(f"- ...and {len(malformed_rows) - 5} more")

        missing_total = sum(stats["missing"] for stats in column_stats)
    whitespace_total = sum(stats["whitespace_count"] for stats in column_stats)

    possible_numeric_total = sum(
        stats["text_count"]
        for stats in column_stats
        if "number" in stats["types"]
        and "text" in stats["types"]
        and "date" not in stats["types"]
    )

    profile_issues = (
        missing_total
        + whitespace_total
        + possible_numeric_total
        + len(duplicate_examples)
        + len(malformed_rows)
    )

    print("\n--- Profile Summary ---")
    print(f"Missing values: {missing_total}")
    print(f"Whitespace issues: {whitespace_total}")
    print(f"Possible invalid numbers: {possible_numeric_total}")
    print(f"Duplicate rows: {len(duplicate_examples)}")
    print(f"Rows with incorrect field counts: {len(malformed_rows)}")

    if profile_issues:
        print(f"Status: REVIEW — {profile_issues} profile issue(s) found.")
    else:
        print("Status: PASS — no profile issues found.")

    return columns, data_rows


def load_schema():
    schema_path = Path(__file__).with_name("schema.json")

    try:
        with schema_path.open("r", encoding="utf-8") as file:
            schema = json.load(file)
    except FileNotFoundError:
        print("\nschema.json was not found. Schema checks skipped.")
        return None
    except (OSError, json.JSONDecodeError) as error:
        print(f"\nCould not read schema.json: {error}")
        return None

    if not isinstance(schema, dict):
        print("schema.json must contain a JSON object.")
        return None

    return schema


def validate_schema(columns, data_rows, schema):
    column_lookup = {}
    for index, name in enumerate(columns):
        cleaned_name = name.strip().casefold()
        if cleaned_name:
            column_lookup.setdefault(cleaned_name, index)

    print("\n--- Schema Validation ---")

    required = schema.get("required_columns", [])
    if not isinstance(required, list):
        print("'required_columns' must be a list.")
    else:
        for name in required:
            if not isinstance(name, str) or not name.strip():
                print(f"Invalid required column name: {name!r}")
                continue

            key = name.strip().casefold()
            if key not in column_lookup:
                print(f"- Required column '{name}' is missing from the header.")
                continue

            index = column_lookup[key]
            missing = [
                row_number
                for row_number, row in data_rows
                if index >= len(row) or not row[index].strip()
            ]

            if missing:
                print(
                    f"- '{name}' has {len(missing)} blank value(s); "
                    f"first affected row: {missing[0]}"
                )
            else:
                print(f"- '{name}' exists and has no blank values.")

    date_columns = schema.get("date_columns", {})
    if not isinstance(date_columns, dict):
        print("'date_columns' must be an object.")
    else:
        for name, date_format in date_columns.items():
            if not isinstance(name, str) or not name.strip():
                print(f"Invalid date column name: {name!r}")
                continue

            key = name.strip().casefold()
            if key not in column_lookup:
                print(f"- Date column '{name}' is missing from the header.")
                continue

            if date_format not in SUPPORTED_DATE_FORMATS:
                print(f"- Unsupported date format for '{name}': {date_format!r}")
                print(f"  Choose one of: {', '.join(sorted(SUPPORTED_DATE_FORMATS))}")
                continue

            index = column_lookup[key]
            invalid = []

            for row_number, row in data_rows:
                value = row[index].strip() if index < len(row) else ""
                if not value:
                    continue
                try:
                    datetime.strptime(value, date_format)
                except ValueError:
                    invalid.append((row_number, value))

            if invalid:
                print(f"- '{name}' has {len(invalid)} invalid date value(s):")
                for row_number, value in invalid[:5]:
                    print(f"    Row {row_number}: {value!r}")
                if len(invalid) > 5:
                    print(f"    ...and {len(invalid) - 5} more")
            else:
                print(f"- All non-empty values in '{name}' match the date format.")

    numeric_ranges = schema.get("numeric_ranges", {})
    if not isinstance(numeric_ranges, dict):
        print("'numeric_ranges' must be an object.")
    else:
        for name, limits in numeric_ranges.items():
            if not isinstance(name, str) or not name.strip():
                print(f"Invalid numeric column name: {name!r}")
                continue

            key = name.strip().casefold()
            if key not in column_lookup:
                print(f"- Numeric column '{name}' is missing from the header.")
                continue

            if not isinstance(limits, dict):
                print(f"- Range for '{name}' must contain min and max values.")
                continue

            try:
                minimum = float(limits["min"])
                maximum = float(limits["max"])
            except (KeyError, TypeError, ValueError):
                print(f"- Range for '{name}' needs numeric 'min' and 'max'.")
                continue

            if (
                not math.isfinite(minimum)
                or not math.isfinite(maximum)
                or minimum > maximum
            ):
                print(f"- Range limits for '{name}' are invalid.")
                continue

            index = column_lookup[key]
            problems = []

            for row_number, row in data_rows:
                value = row[index].strip() if index < len(row) else ""
                if not value:
                    continue

                try:
                    number = float(value)
                    if not math.isfinite(number):
                        raise ValueError
                except ValueError:
                    problems.append((row_number, value, "not numeric"))
                    continue

                if number < minimum or number > maximum:
                    problems.append((row_number, value, "outside range"))

            if problems:
                print(f"- '{name}' has {len(problems)} range issue(s):")
                for row_number, value, reason in problems[:5]:
                    print(f"    Row {row_number}: {value!r} ({reason})")
                if len(problems) > 5:
                    print(f"    ...and {len(problems) - 5} more")
            else:
                print(
                    f"- All non-empty values in '{name}' are between "
                    f"{minimum:g} and {maximum:g}."
                )


def main():
    print("--- DataCheck ---")
    print("Profile a CSV file and check its data quality.\n")

    csv_path = choose_csv_file()
    if not csv_path:
        return

    columns, data_rows = profile_csv(csv_path)
    if columns is None:
        return

    schema = load_schema()
    if schema is not None:
        validate_schema(columns, data_rows, schema)


if __name__ == "__main__":
    main()