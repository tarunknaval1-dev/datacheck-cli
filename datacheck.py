import csv
from datetime import date, datetime
from pathlib import Path


DATE_FORMATS = [
    ("YYYY-MM-DD (example: 2026-11-03)", "%Y-%m-%d"),
    ("DD/MM/YYYY (example: 03/11/2026)", "%d/%m/%Y"),
    ("MM/DD/YYYY (example: 11/03/2026)", "%m/%d/%Y"),
    ("DD-MM-YYYY (example: 03-11-2026)", "%d-%m-%Y"),
    ("YYYY/MM/DD (example: 2026/11/03)", "%Y/%m/%d"),
]


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
    """Estimate whether a non-empty value is a number, date, or text."""
    try:
        float(value)
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
        if "number" in value_types and "text" in value_types and "date" not in value_types:
            print(f"    Possible invalid numeric values: {stats['text_count']}")
            for issue_row, value in stats["text_examples"]:
                print(f"      Row {issue_row}: {value!r}")

            extra_count = stats["text_count"] - len(stats["text_examples"])
            if extra_count > 0:
                print(f"      ...and {extra_count} more")

    print(f"\nDuplicate rows: {len(duplicate_examples)}")

    if duplicate_examples:
        print("Repeated row examples (first occurrence → repeated occurrence):")
        for first_row, repeated_row in duplicate_examples[:5]:
            print(f"- Row {first_row} → row {repeated_row}")

        if len(duplicate_examples) > 5:
            print(f"- ...and {len(duplicate_examples) - 5} more")

    return columns, data_rows


def validate_date_column(columns, data_rows):
    if not columns:
        return

    answer = input("\nWould you like to validate a date column? (y/n): ").strip().lower()
    if answer != "y":
        return

    print("\nChoose the date column:")
    for number, column in enumerate(columns, start=1):
        display_name = column.strip() or f"(unnamed column {number})"
        print(f"{number}. {display_name}")

    try:
        column_number = int(input("Enter the column number: "))
    except ValueError:
        print("Please enter a number.")
        return

    if column_number < 1 or column_number > len(columns):
        print("That column number is not in the CSV.")
        return

    print("\nChoose the expected date format:")
    for number, (label, _) in enumerate(DATE_FORMATS, start=1):
        print(f"{number}. {label}")

    try:
        format_number = int(input("Enter the format number: "))
    except ValueError:
        print("Please enter a number.")
        return

    if format_number < 1 or format_number > len(DATE_FORMATS):
        print("That date format number is not available.")
        return

    date_format = DATE_FORMATS[format_number - 1][1]
    column_index = column_number - 1
    column_name = columns[column_index].strip() or f"Column {column_number}"
    checked_count = 0
    invalid_values = []

    for row_number, row in data_rows:
        value = row[column_index].strip() if column_index < len(row) else ""
        if not value:
            continue

        checked_count += 1
        try:
            datetime.strptime(value, date_format)
        except ValueError:
            invalid_values.append((row_number, value))

    print(f"\nDate validation for '{column_name}':")
    print(f"Non-empty values checked: {checked_count}")
    print(f"Invalid date values: {len(invalid_values)}")

    for row_number, value in invalid_values[:10]:
        print(f"- Row {row_number}: {value!r}")

    if len(invalid_values) > 10:
        print(f"- ...and {len(invalid_values) - 10} more")


def validate_required_columns(columns, data_rows):
    raw_input = input(
        "\nEnter required column names separated by commas "
        "(or press Enter to skip): "
    ).strip()

    if not raw_input:
        print("Required-column check skipped.")
        return

    required_names = [
        name.strip() for name in raw_input.split(",") if name.strip()
    ]

    if not required_names:
        print("No column names were entered.")
        return

    column_lookup = {}
    for index, column_name in enumerate(columns):
        normalized_name = column_name.strip().casefold()
        if normalized_name:
            column_lookup.setdefault(normalized_name, index)

    print("\n--- Required Column Check ---")

    for required_name in required_names:
        normalized_name = required_name.casefold()

        if normalized_name not in column_lookup:
            print(f"- Column '{required_name}' is missing from the CSV header.")
            continue

        column_index = column_lookup[normalized_name]
        missing_rows = []

        for row_number, row in data_rows:
            value = row[column_index].strip() if column_index < len(row) else ""
            if not value:
                missing_rows.append(row_number)

        if missing_rows:
            shown_rows = ", ".join(str(number) for number in missing_rows[:10])
            print(
                f"- Column '{required_name}' exists, but has "
                f"{len(missing_rows)} missing value(s) in row(s): {shown_rows}"
            )
            if len(missing_rows) > 10:
                print(f"  ...and {len(missing_rows) - 10} more")
        else:
            print(f"- Column '{required_name}' exists and has no missing values.")


def main():
    print("--- DataCheck ---")
    print("Profile a CSV file and check its data quality.\n")

    csv_path = choose_csv_file()

    if csv_path:
        columns, data_rows = profile_csv(csv_path)

        if columns is not None:
            validate_date_column(columns, data_rows)
            validate_required_columns(columns, data_rows)


if __name__ == "__main__":
    main()