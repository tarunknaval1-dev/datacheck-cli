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

SUPPORTED_DATE_FORMATS = {date_format for _, date_format in DATE_FORMATS}


def choose_csv_file():
    file_input = input("Enter the path to a CSV file: ").strip().strip("\"'")

    if not file_input:
        print("File path cannot be empty.")
        return None

    csv_path = Path(file_input).expanduser()

    # If a relative path isn't found from the terminal's folder,
    # also look beside this Python script.
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
    """Estimate whether a non-empty value is a number, date, or text."""
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
                    "unique_values": set(),
                    "whitespace_count": 0,
                    "whitespace_examples": [],
                    "value_types": set(),
                    "text_count": 0,
                    "text_examples": []
                }
                for _ in columns
            ]

            seen_rows = {}
            duplicate_examples = []
            data_rows = []
            row_count = 0

            for row_number, row in enumerate(reader, start=2):
                # Ignore completely blank lines.
                if not row or all(not value.strip() for value in row):
                    continue

                row_count += 1
                data_rows.append((row_number, row))

                for index in range(len(columns)):
                    value = row[index] if index < len(row) else ""
                    cleaned_value = value.strip()
                    stats = column_stats[index]

                    if value != cleaned_value:
                        stats["whitespace_count"] += 1
                        if len(stats["whitespace_examples"]) < 3:
                            stats["whitespace_examples"].append(
                                (row_number, value)
                            )

                    if cleaned_value:
                        stats["non_empty"] += 1
                        stats["unique_values"].add(cleaned_value)

                        value_type = classify_value(cleaned_value)
                        stats["value_types"].add(value_type)

                        if value_type == "text":
                            stats["text_count"] += 1
                            if len(stats["text_examples"]) < 5:
                                stats["text_examples"].append(
                                    (row_number, cleaned_value)
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
        display_name = column.strip() or f"(unnamed column {index + 1})"
        stats = column_stats[index]
        missing_percent = stats["missing"] / row_count * 100 if row_count else 0
        estimated_type = infer_column_type(stats["value_types"])

        print(
            f"- {display_name}: "
            f"type={estimated_type}, "
            f"{stats['non_empty']} non-empty, "
            f"{stats['missing']} missing ({missing_percent:.1f}%), "
            f"{len(stats['unique_values'])} distinct, "
            f"{stats['whitespace_count']} whitespace issue(s)"
        )

        for issue_row, original_value in stats["whitespace_examples"]:
            print(f"    Whitespace at row {issue_row}: {original_value!r}")

        value_types = stats["value_types"]
        if (
            "number" in value_types
            and "text" in value_types
            and "date" not in value_types
        ):
            print(f"    Possible invalid numeric values: {stats['text_count']}")
            for issue_row, value in stats["text_examples"]:
                print(f"      Row {issue_row}: {value!r}")

            extra_count = stats["text_count"] - len(stats["text_examples"])
            if extra_count:
                print(f"      ...and {extra_count} more")

    print(f"\nDuplicate rows: {len(duplicate_examples)}")

    if duplicate_examples:
        print("Repeated row examples (first occurrence → repeated occurrence):")
        for first_row, repeated_row in duplicate_examples[:5]:
            print(f"- Row {first_row} → row {repeated_row}")

        if len(duplicate_examples) > 5:
            print(f"- ...and {len(duplicate_examples) - 5} more")

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

    required_columns = schema.get("required_columns", [])

    if not isinstance(required_columns, list):
        print("'required_columns' must be a list.")
    else:
        for name in required_columns:
            if not isinstance(name, str) or not name.strip():
                print(f"Invalid required column name: {name!r}")
                continue

            key = name.strip().casefold()

            if key not in column_lookup:
                print(f"- Required column '{name}' is missing from the header.")
                continue

            index = column_lookup[key]
            missing_rows = [
                row_number
                for row_number, row in data_rows
                if index >= len(row) or not row[index].strip()
            ]

            if missing_rows:
                print(
                    f"- '{name}' has {len(missing_rows)} blank value(s); "
                    f"first affected row: {missing_rows[0]}"
                )
            else:
                print(f"- '{name}' exists and has no blank values.")

    date_columns = schema.get("date_columns", {})

    if not isinstance(date_columns, dict):
        print("'date_columns' must be an object mapping column names to formats.")
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
                print(
                    f"- Unsupported date format for '{name}'. "
                    "Use one of the formats listed in the README."
                )
                continue

            index = column_lookup[key]
            invalid_rows = []

            for row_number, row in data_rows:
                value = row[index].strip() if index < len(row) else ""
                if not value:
                    continue

                try:
                    datetime.strptime(value, date_format)
                except ValueError:
                    invalid_rows.append((row_number, value))

            if invalid_rows:
                print(f"- '{name}' has {len(invalid_rows)} invalid date value(s):")
                for row_number, value in invalid_rows[:5]:
                    print(f"    Row {row_number}: {value!r}")
                if len(invalid_rows) > 5:
                    print(f"    ...and {len(invalid_rows) - 5} more")
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

            if not math.isfinite(minimum) or not math.isfinite(maximum):
                print(f"- Range limits for '{name}' must be finite numbers.")
                continue

            if minimum > maximum:
                print(f"- Minimum for '{name}' cannot exceed its maximum.")
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