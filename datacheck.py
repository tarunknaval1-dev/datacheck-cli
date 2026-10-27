import csv
from pathlib import Path


def choose_csv_file():
    file_input = input("Enter the path to a CSV file: ").strip()
    file_input = file_input.strip("\"'")

    if not file_input:
        print("File path cannot be empty.")
        return None

    csv_path = Path(file_input).expanduser()

    # If a relative path wasn't found from the terminal's folder,
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


def inspect_csv(csv_path):
    try:
        with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.reader(file)

            try:
                columns = next(reader)
            except StopIteration:
                print("The CSV file is empty.")
                return

            row_count = sum(1 for _ in reader)

    except (OSError, UnicodeError, csv.Error) as error:
        print(f"Could not read the CSV file: {error}")
        return

    print(f"\nFile: {csv_path.name}")
    print(f"Columns: {len(columns)}")

    if columns:
        print("Column names:")
        for number, column in enumerate(columns, start=1):
            print(f"  {number}. {column}")
    else:
        print("The header row is empty.")

    print(f"Data rows: {row_count}")


def main():
    print("--- DataCheck ---")
    print("Inspect a CSV file's columns and row count.\n")

    csv_path = choose_csv_file()

    if csv_path:
        inspect_csv(csv_path)


if __name__ == "__main__":
    main()