#!/usr/bin/env python3
"""
Planned Media Report Splitter

Takes a planned media report (.xls) and splits condensed buy lines
into individual spot-per-day rows for client reporting.

Usage: python splitter.py <input_file.xls> [output_file.xlsx]
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

DAY_NAMES = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

ROTATION_OFFSETS = {
    "M-F": [0, 1, 2, 3, 4],
    "SA-SU": [5, 6],
    "SAT": [5],
    "SUN": [6],
    "M-SU": [0, 1, 2, 3, 4, 5, 6],
    "MT.TF..": [0, 1, 3, 4],   # Mon, Tue, Thu, Fri — dot = skip that day position
    # Single-day rotations derived from DAY_NAMES order
    **{day: [i] for i, day in enumerate(DAY_NAMES)},
}

# Column indices in the .xls export
C_MEDIA, C_CLIENT, C_PRODUCT, C_ESTIMATE, C_MARKET = 0, 1, 2, 3, 4
C_STATION, C_AFFIL, C_LINE, C_WEEK, C_DPT = 5, 6, 7, 8, 9
C_LEN, C_ROTATION, C_TIMES, C_PROGRAM = 10, 11, 12, 13
C_SPOTS, C_PURCH, C_SPOT_COST, C_NET = 14, 15, 16, 17


def parse_week_date(val):
    if isinstance(val, datetime):
        return val
    return datetime.strptime(str(val).strip(), "%m/%d/%y")


def find_data_start(df):
    for idx in range(len(df)):
        cell = df.iloc[idx, C_MEDIA]
        if pd.notna(cell) and str(cell).strip() == "MEDIA":
            # Header found; skip header row, sub-header row, then any blanks
            start = idx + 2
            while start < len(df) and pd.isna(df.iloc[start, C_MEDIA]):
                start += 1
            return start
    raise ValueError("Could not find 'MEDIA' header row in input file")


def split_line(row):
    rotation = str(row[C_ROTATION]).strip()
    offsets = ROTATION_OFFSETS.get(rotation)
    if offsets is None:
        raise ValueError(f"Unknown rotation '{rotation}' on line {row[C_LINE]}, station {row[C_STATION]}")

    spots = int(row[C_SPOTS])
    purch = float(row[C_PURCH])
    net = float(row[C_NET])

    week_monday = parse_week_date(row[C_WEEK])
    # Snap to Monday in case it isn't already
    week_monday -= timedelta(days=week_monday.weekday())

    # Per-spot values with remainder handling
    purch_base = round(purch / spots, 2)
    net_base = round(net / spots, 2)
    purch_remainder = round(purch - purch_base * spots, 2)
    net_remainder = round(net - net_base * spots, 2)

    rows = []
    for i in range(spots):
        offset = offsets[i % len(offsets)]
        spot_date = week_monday + timedelta(days=offset)

        p = purch_base + (purch_remainder if i == 0 else 0)
        n = net_base + (net_remainder if i == 0 else 0)

        rows.append({
            "Media": row[C_MEDIA],
            "Client": row[C_CLIENT],
            "Product": row[C_PRODUCT],
            "Estimate": row[C_ESTIMATE],
            "Market": row[C_MARKET],
            "Station": row[C_STATION],
            "Line": row[C_LINE],
            "Date": spot_date.strftime("%m/%d/%Y"),
            "Day": DAY_NAMES[offset],
            "Dpt Code": row[C_DPT],
            "Length": int(row[C_LEN]),
            "Times": row[C_TIMES] if pd.notna(row[C_TIMES]) else "",
            "Program": row[C_PROGRAM] if pd.notna(row[C_PROGRAM]) else "",
            "Spots": 1,
            "Purch AD35+": round(p, 2),
            "Spot Cost": float(row[C_SPOT_COST]),
            "Net Cost": round(n, 2),
        })

    return rows


def process(df):
    """Core splitting logic. Takes a raw DataFrame, returns (result_df, stats_dict)."""
    data_start = find_data_start(df)

    output_rows = []
    orig_total_spots = 0
    orig_total_net = 0.0
    orig_lines = 0
    skipped_g = 0

    for idx in range(data_start, len(df)):
        row = df.iloc[idx]

        if str(row[C_LINE]).strip() == "***" or str(row[C_STATION]).strip() == "***":
            continue
        if pd.isna(row[C_MEDIA]) or str(row[C_MEDIA]).strip() == "":
            continue
        if str(row[C_DPT]).strip() == "G":
            skipped_g += 1
            continue

        orig_lines += 1
        orig_total_spots += int(row[C_SPOTS])
        orig_total_net += float(row[C_NET])
        output_rows.extend(split_line(row))

    result = pd.DataFrame(output_rows)
    split_net = sum(r["Net Cost"] for r in output_rows)

    stats = {
        "orig_lines": orig_lines,
        "orig_spots": orig_total_spots,
        "orig_net": orig_total_net,
        "split_rows": len(result),
        "split_net": split_net,
        "skipped_g": skipped_g,
        "net_diff": abs(orig_total_net - split_net),
    }

    return result, stats


def split_report(input_path, output_path=None):
    df = pd.read_excel(input_path, header=None)
    result, stats = process(df)

    if output_path is None:
        p = Path(input_path)
        output_path = p.parent / f"{p.stem} Split.xlsx"

    result.to_excel(str(output_path), index=False)

    print(f"Input:  {input_path}")
    print(f"Output: {output_path}")
    print(f"Original buy lines:  {stats['orig_spots']} spots across {stats['orig_lines']} lines (excl subtotals/Added Value)")
    print(f"Split output rows:   {stats['split_rows']}")
    print(f"Skipped Added Value: {stats['skipped_g']} lines")
    print(f"Net cost check:      Original ${stats['orig_net']:,.2f}  →  Split ${stats['split_net']:,.2f}  (diff: ${stats['net_diff']:.2f})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python splitter.py <input_file.xls> [output_file.xlsx]")
        sys.exit(1)
    split_report(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
