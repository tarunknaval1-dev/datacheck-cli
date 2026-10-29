import csv
from pathlib import Path


def choose_csv_file():
    file_input = input("Enter the path to a CSV file: ").strip()
    file_input = file_input.strip("\"'")

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
                {
                    "non_empty": 0,
                    "missing": 0,
                    "unique_values": set()
                }
                for _ in columns
            ]

            row_count = 0

            for row in reader:
                row_count += 1

                for index in range(len(columns)):
                    # A row may have fewer cells than the header.
                    value = row[index].strip() if index < len(row) else ""

                    if value:
                        column_stats[index]["non_empty"] += 1
                        column_stats[index]["unique_values"].add(value)
                    else:
                        column_stats[index]["missing"] += 1

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


def main():
    print("--- DataCheck ---")
    print("Profile a CSV file and check for missing values.\n")

    csv_path = choose_csv_file()

    if csv_path:
        profile_csv(csv_path)


if __name__ == "__main__":
    main()