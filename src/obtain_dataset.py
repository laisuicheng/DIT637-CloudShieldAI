"""Dataset acquisition helper for CICIDS2017.

CICIDS2017 is distributed by the Canadian Institute for Cybersecurity (CIC),
University of New Brunswick. The dataset is large, so this project does not
redistribute it. This helper prints the official source and validates the local
folder after the user downloads and extracts the MachineLearningCSV archive.
"""
from __future__ import annotations

import argparse
from pathlib import Path

OFFICIAL_DATASET_PAGE = "https://www.unb.ca/cic/datasets/ids-2017.html"
EXPECTED_ARCHIVE_NAME = "MachineLearningCSV.zip"


def find_csvs(data_dir: Path) -> list[Path]:
    return sorted(data_dir.rglob("*.csv"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Show how to obtain and verify CICIDS2017.")
    parser.add_argument("--data-dir", default="data/raw", help="Folder where CICIDS2017 CSV files are stored")
    args = parser.parse_args()

    base = Path(__file__).resolve().parents[1]
    data_dir = Path(args.data_dir)
    if not data_dir.is_absolute():
        data_dir = base / data_dir
    data_dir.mkdir(parents=True, exist_ok=True)

    print("CloudShield AI - CICIDS2017 dataset setup")
    print("1. Open the official CIC dataset page:")
    print(f"   {OFFICIAL_DATASET_PAGE}")
    print("2. Locate CICIDS2017 and download the machine-learning CSV package")
    print(f"   (commonly named {EXPECTED_ARCHIVE_NAME}).")
    print("3. Extract the CSV files into:")
    print(f"   {data_dir}")
    print("4. Do not commit the large dataset files to GitHub.")
    print("5. Re-run this command to verify the files are visible.")

    csvs = find_csvs(data_dir)
    if csvs:
        print(f"\nFound {len(csvs)} CSV file(s):")
        for p in csvs:
            print(f" - {p.relative_to(data_dir)}")
    else:
        print("\nNo CSV files found yet. Download and extract CICIDS2017 first.")


if __name__ == "__main__":
    main()
