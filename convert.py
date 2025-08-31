"""
Viva R. Horowitz
Vibe-coded using chatgpt
2025-07-05
"""

import pandas as pd
#from datetime import datetime
from tkinter import Tk, filedialog
import os
import tempfile

def convert_venmo_to_monarch(venmo_csv_path, monarch_csv_path):
    """
    Convert a single Venmo CSV export to a Monarch import CSV.
    Paths are normalized for Windows and stripped of extra whitespace.
    """
    venmo_csv_path = os.path.normpath(venmo_csv_path.strip())
    monarch_csv_path = os.path.normpath(monarch_csv_path.strip())

    # Step 1: Read lines and find the correct header row
    with open(venmo_csv_path, encoding='utf-8-sig') as f:
        lines = f.readlines()

    header_line_index = None
    for i, line in enumerate(lines):
        if line.strip().startswith("ID,Datetime") or line.strip().startswith(",ID,Datetime"):
            header_line_index = i
            break

    if header_line_index is None:
        raise ValueError(f"Could not find the header row in {venmo_csv_path}")

    # Step 2: Read CSV with corrected header
    df = pd.read_csv(venmo_csv_path, skiprows=header_line_index)

    # Step 3: Drop rows missing type or amount
    df = df.dropna(subset=['Type', 'Amount (total)'])

    def process_row(row):
        tx_type = str(row['Type']).strip()
        note = str(row['Note']).strip()

        if tx_type == 'Payment':
            merchant = str(row['To']).strip()
            sign = -1
        elif tx_type == 'Charge':
            merchant = str(row['From']).strip()
            sign = 1
        else:
            return None

        try:
            date = pd.to_datetime(row['Datetime']).strftime('%Y-%m-%d')
        except Exception:
            return None

        amt_raw = str(row['Amount (total)'])
        amt_clean = amt_raw.replace('$', '').replace(',', '').replace('(', '-').replace(')', '').replace('−', '-').replace('--', '-').replace(' ', '')
        try:
            amount = sign * float(amt_clean)
        except Exception:
            return None

        return pd.Series([
            date, merchant, "", "Venmo", note, note, f"{amount:.2f}", ""
        ])

    output_df = df.apply(process_row, axis=1).dropna()

    # Step 4: Write output in Monarch format (no headers)
    output_df.to_csv(monarch_csv_path, index=False, header=False)


def select_multiple_venmo():
    """
    Open a file dialog to select multiple Venmo CSV exports.
    Convert them all to Monarch format and combine into one CSV.
    """

    # Hide the root Tk window
    root = Tk()
    root.withdraw()

    # Step 1: Ask user to select Venmo files
    venmo_files = list(filedialog.askopenfilenames(
        title="Select Venmo Export CSV files",
        filetypes=[("CSV files", "*.csv")]
    ))

    if not venmo_files:
        print("No files selected.")
        return

    # Step 2: Ask where to save the combined Monarch file
    output_file = filedialog.asksaveasfilename(
        title="Save Combined Monarch Import File",
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv")]
    )

    if not output_file:
        print("No output file chosen.")
        return

    # Step 3: Convert each file and collect results
    all_outputs = []

    print("Selected files:", venmo_files)

    for venmo_file in venmo_files:
        venmo_file = os.path.normpath(venmo_file.strip())
        print("Processing:", venmo_file)

        temp_path = tempfile.mktemp(suffix=".csv")
        try:
            convert_venmo_to_monarch(venmo_file, temp_path)
        except Exception as e:
            print(f"Error converting {venmo_file}: {e}")
            continue

        # Read back and append
        df = pd.read_csv(temp_path, header=None)
        all_outputs.append(df)

    # Step 4: Concatenate everything
    if all_outputs:
        combined_df = pd.concat(all_outputs, ignore_index=True)
        output_file = os.path.normpath(output_file.strip())
        combined_df.to_csv(output_file, index=False, header=False)
        print(f"Combined Monarch import file saved to {output_file}")
    else:
        print("No valid Venmo data found.")
