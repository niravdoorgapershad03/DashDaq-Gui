#!/usr/bin/env python3
"""
Analyze DashDAQ log from Pajero_Run1.csv (or any similar DashDAQ CSV).

- Automatically skips the metadata at the top of the file.
- Extracts Time, Speed, RPM, ECT, IAT, MAP, AFR, etc.
- Converts Time from ms to seconds starting at 0.
- Creates one plot per signal vs time and saves PNG files in a 'plots' folder.

Usage:
    python analyze_dashdaq.py Pajero_Run1.csv
"""

import sys
import io
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


def load_dashdaq_csv(csv_path: Path) -> pd.DataFrame:
    """
    Load a DashDAQ CSV file and return a cleaned DataFrame.

    Handles:
    - Header metadata lines ("DashDAQ Log File", "Format", "Signal", etc.)
    - Units row (ms, kph, RPM, °C, kpa, ...)
    - Trailing empty column from extra comma
    """
    csv_path = Path(csv_path)

    # Read whole file as text first to locate the actual header
    with csv_path.open("r", encoding="latin1") as f:
        lines = f.readlines()

    # Find the line where the actual column header starts (begins with "Time")
    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith('"Time"'):
            header_idx = i
            break

    if header_idx is None:
        raise ValueError("Could not find a header line starting with '\"Time\"' in the CSV.")

    # Rebuild the CSV string starting from the header line
    data_str = "".join(lines[header_idx:])

    # Read that portion with pandas
    df = pd.read_csv(io.StringIO(data_str))

    # Drop any trailing 'Unnamed' columns created by extra commas
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]

    # First row after the header is the units row (e.g. ms, kph, RPM, °C ...)
    # We can safely drop it.
    if isinstance(df.loc[0, "Time"], str):
        df = df.iloc[1:].reset_index(drop=True)

    # Convert all columns to numeric where possible
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Create a Time_s column in seconds relative to start
    if "Time" in df.columns:
        t = df["Time"].astype(float)
        df["Time_s"] = (t - t.min()) / 1000.0

    return df


def plot_all_signals(df: pd.DataFrame, output_dir: Path) -> None:
    """
    For each numeric column (except Time), plot value vs Time_s (or Time)
    and save as PNG in output_dir.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    time_col = "Time_s" if "Time_s" in df.columns else "Time"

    # Choose all numeric columns except the time column itself
    numeric_cols = [
        col for col in df.columns
        if col != time_col and pd.api.types.is_numeric_dtype(df[col])
    ]

    if not numeric_cols:
        print("No numeric columns found to plot.")
        return

    for col in numeric_cols:
        if df[col].dropna().empty:
            # Skip completely empty signals (e.g. AFR if sensor wasn't connected)
            continue

        plt.figure(figsize=(10, 4))
        plt.plot(df[time_col], df[col])
        plt.xlabel("Time (s)" if time_col == "Time_s" else "Time (ms)")
        plt.ylabel(col)
        plt.title(f"{col} vs Time")
        plt.grid(True)
        plt.tight_layout()

        out_file = output_dir / f"{col}_vs_time.png"
        plt.savefig(out_file, dpi=150)
        plt.close()

        print(f"Saved {out_file}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_dashdaq.py <dashdaq_csv_file>")
        print("Example: python analyze_dashdaq.py Pajero_Run1.csv")
        sys.exit(1)

    csv_path = Path(sys.argv[1])

    if not csv_path.exists():
        print(f"File not found: {csv_path}")
        sys.exit(1)

    print(f"Loading {csv_path} ...")
    df = load_dashdaq_csv(csv_path)

    print("Columns loaded:", list(df.columns))
    print("Creating plots ...")

    output_dir = csv_path.with_suffix("")  # e.g. Pajero_Run1
    output_dir = output_dir.parent / f"{output_dir.name}_plots"

    plot_all_signals(df, output_dir)

    print("Done.")


if __name__ == "__main__":
    main()
