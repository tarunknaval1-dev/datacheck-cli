import csv
from pathlib import Path


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


def profile_csv(csv_path):
    try:
        with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.reader(file)

            try:
                columns = next(reader)
            except StopIteration:
                print("The CSV file is empty.")
                return

            column_stats = [
                {"non_empty": 0, "missing": 0, "unique_values": set()}
                for _ in columns
            ]

            seen_rows = {}
            duplicate_examples = []
            row_count = 0

            for row_number, row in enumerate(reader, start=2):
                # Ignore completely blank lines in the CSV.
                if not row or all(not value.strip() for value in row):
                    continue

                row_count += 1

                for index in range(len(columns)):
                    value = row[index].strip() if index < len(row) else ""

                    if value:
                        column_stats[index]["non_empty"] += 1
                        column_stats[index]["unique_values"].add(value)
                    else:
                        column_stats[index]["missing"] += 1

                normalized_row = tuple(value.strip() for value in row)

                if normalized_row in seen_rows:
                    duplicate_examples.append(
                        (seen_rows[normalized_row], row_number)
                    )
                else:
                    seen_rows[normalized_row] = row_number

    except (OSError, UnicodeError, csv.Error) as error:
        print(f"Could not read the CSV file: {error}")
        return

    print(f"\nCSV profile: {csv_path.name}")
    print(f"Rows: {row_count}")
    print(f"Columns: {len(columns)}")

    print("\nColumn details:")
    for index, column in enumerate(columns):
        display_name = column.strip() or f"(unnamed column {index + 1})"
        stats = column_stats[index]

        if row_count:
            missing_percent = stats["missing"] / row_count * 100
        else:
            missing_percent = 0

        print(
            f"- {display_name}: "
            f"{stats['non_empty']} non-empty, "
            f"{stats['missing']} missing ({missing_percent:.1f}%), "
            f"{len(stats['unique_values'])} distinct"
        )

    print(f"\nDuplicate rows: {len(duplicate_examples)}")

    if duplicate_examples:
        print("Repeated row examples (first occurrence → repeated occurrence):")
        for first_row, repeated_row in duplicate_examples[:5]:
            print(f"- Row {first_row} → row {repeated_row}")

        if len(duplicate_examples) > 5:
            print(f"- ...and {len(duplicate_examples) - 5} more")


def main():
    print("--- DataCheck ---")
    print("Profile a CSV file and check its data quality.\n")

    csv_path = choose_csv_file()

    if csv_path:
        profile_csv(csv_path)


if __name__ == "__main__":
    main()