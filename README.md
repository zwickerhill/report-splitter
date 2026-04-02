# Planned Media Report Splitter

Splits condensed planned media buy lines into individual spot-per-day rows for client reporting.

## What it does

Takes a planned media `.xls` export where each line shows aggregated spots (e.g., 5 spots on M-F) and expands it into one row per spot per day, splitting costs proportionally:

| Field | Original | Split |
|-------|----------|-------|
| Spots | N (e.g., 5) | 1 per row |
| Purch AD35+ | Total | Divided by N |
| Spot Cost | Per-spot | Unchanged |
| Net Cost | Total | Divided by N |
| Week | Week start date | Actual air date |
| Rotation | Range (M-F) | Day name (MON, TUE, etc.) |

### Rules
- **Added Value lines** (DPT Code "G") are dropped — only counted post-buy
- **Subtotal/total rows** (`***`) are dropped
- **Day cycling**: When spots exceed available days (e.g., 7 spots on M-F), extra spots cycle back to the beginning of the rotation
- **Remainder handling**: Rounding remainders from cost division go to the first spot so totals always match exactly

## Web App

A Streamlit web interface is available for non-technical users — upload a file and download the split report.

## CLI Usage

### Requirements

- Python 3.8+
- `pandas`
- `xlrd` (for reading `.xls` files)

```bash
pip install pandas xlrd
```

```bash
python splitter.py <input_file.xls> [output_file.xlsx]
```

If no output file is specified, it creates `<input_name> Split.xlsx` in the same directory.

## Supported Rotations

| Rotation | Days |
|----------|------|
| M-F | Monday – Friday |
| SA-SU | Saturday – Sunday |
| SAT | Saturday |
| SUN | Sunday |
| M-SU | Monday – Sunday |
