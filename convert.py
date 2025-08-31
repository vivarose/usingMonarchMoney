"""
Viva R. Horowitz
Vibe-coded using chatgpt
2025-07-05
"""

import pandas as pd
from datetime import datetime

def convert_multiple_venmo_to_monarch(venmo_csv_paths, monarch_csv_path):
    all_dfs = []

    for venmo_csv_path in venmo_csv_paths:
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

        processed_df = df.apply(process_row, axis=1).dropna()
        all_dfs.append(processed_df)

    # Step 4: Combine all exports
    final_df = pd.concat(all_dfs, ignore_index=True)

    # Step 5: Sort by date
    final_df = final_df.sort_values(by=0)

    # Step 6: Write output in Monarch format (no headers)
    final_df.to_csv(monarch_csv_path, index=False, header=False)

# Example usage:
# convert_multiple_venmo_to_monarch(
#     ["venmo_export_jan.csv", "venmo_export_feb.csv"],
#     "monarch_import.csv"
# )
