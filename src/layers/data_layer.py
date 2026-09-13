from __future__ import annotations

from pathlib import Path
import pandas as pd


def discover_csvs(data_dir: Path) -> list[Path]:
    files = sorted(data_dir.rglob("*.csv"))
    if not files:
        raise FileNotFoundError(
            f"No CICIDS2017 CSV files found under {data_dir}. "
            "Run: python src/obtain_dataset.py"
        )
    return files


def load_cicids2017(
    data_dir: Path,
    sample_frac: float | None = None,
    max_rows_per_file: int | None = None,
    random_state: int = 42,
) -> pd.DataFrame:
    """Load one or more CICIDS2017 CSV files into one DataFrame.

    sample_frac is useful for a quick course demonstration. max_rows_per_file
    offers a deterministic memory cap for machines with limited RAM.
    """
    frames: list[pd.DataFrame] = []
    for path in discover_csvs(data_dir):
        frame = pd.read_csv(path, low_memory=False)
        frame.columns = [str(c).strip() for c in frame.columns]

        if sample_frac is not None and 0 < sample_frac < 1:
            frame = frame.sample(frac=sample_frac, random_state=random_state)
        if max_rows_per_file is not None and max_rows_per_file > 0 and len(frame) > max_rows_per_file:
            frame = frame.sample(n=max_rows_per_file, random_state=random_state)

        frames.append(frame)
        print(f"Loaded {path.name}: {len(frame):,} rows")

    return pd.concat(frames, ignore_index=True)
