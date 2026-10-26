from pathlib import Path


def choose_csv_file():
    file_input = input("Enter the path to a CSV file: ").strip()

    if not file_input:
        print("File path cannot be empty.")
        return None

    csv_path = Path(file_input).expanduser()

    if not csv_path.exists():
        print("That file does not exist. Check the path and try again.")
        return None

    if not csv_path.is_file():
        print("Please enter a file path, not a folder.")
        return None

    if csv_path.suffix.lower() != ".csv":
        print("The selected file must have a .csv extension.")
        return None

    print(f"CSV file selected: {csv_path.resolve()}")
    return csv_path


def main():
    print("--- DataCheck ---")
    print("A simple tool for checking CSV data quality.\n")

    csv_path = choose_csv_file()

    if csv_path:
        print(f"\nReady to analyze: {csv_path.name}")
        print("CSV analysis features are coming in the next update.")


if __name__ == "__main__":
    main()