"""
Viva R. Horowitz
Vibe-coded using chatgpt

The required CSV format for importing to Monarch and exporting is 8 columns, 
which must be listed in the following order in the spreadsheet table (see link
to download an example in the next section). If you're getting an error, 
try not including a header row. 
1. Date 
2. Merchant
3. Category 
4. Account 
5. Original Statement 
6. Notes 
7. Amount 
8. Tags 

Note: Monarch uses positive numbers for income and negative numbers for expenses. 
So an amount listed as +$100.00 would be seen as income, and 
-$100.00 would be seen as an expense. 

Some apps and banks export expenses as positive numbers, or with parenthesis 
around them [i.e. ($100)], which means they will show up incorrectly if 
imported directly into Monarch.

To upload: in Monarch, click "Edit" then "Upload transactions"

2025-07-05 and 2025-08-31
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
    Automatically fills in categories based on vendor/note rules.
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

    weekdays = {'monday','tuesday','wednesday','thursday','friday','saturday','sunday'}

    def infer_category(merchant, note):
        note_lower = str(note).lower()
        if merchant == "Stephanie Fancher":
            return "House cleaning"
        if merchant == "Meg Young":
            return "House Maintenance"
        if merchant == "Kaya Lutz" or merchant == "Senna Camp" or \
            merchant == "josie cooper" or merchant == "Cloee EldevikLaCotera":
                return "Child Care"
        if "watching mendel" in note_lower or "babysitting" in note_lower:
            return "Child Care"
        if note_lower.strip() in weekdays:
            return "Child Care"
        if merchant == "Andrew Horowitz":
            return "Inheritance maintenance"
        return ""

    def process_row(row):
        tx_type = str(row['Type']).strip()
        note = str(row['Note']).strip()
    
        amt_raw = str(row['Amount (total)'])
        amt_clean = amt_raw.replace('$', '').replace(',', '').replace('(', '-').replace(')', '').replace('−', '-').replace('--', '-').replace(' ', '')
        try:
            amount = float(amt_clean)
        except Exception:
            return None
    
        # Direction & merchant
        if tx_type == 'Payment':
            if amount < 0:
                merchant = str(row['To']).strip()   # You paid them
            else:
                merchant = str(row['From']).strip() # You received money
        elif tx_type == 'Charge':
            merchant = str(row['From']).strip()
        else:
            return None
    
    
        category = infer_category(merchant, note)
    
        return pd.Series([
            pd.to_datetime(row['Datetime']).strftime('%Y-%m-%d'),
            merchant,
            category,
            "Venmo",
            note,
            note,
            f"{amount:.2f}",
            ""
        ])


    output_df = df.apply(process_row, axis=1).dropna()

    # Step 4: Write output in Monarch format (no headers)
    output_df.to_csv(monarch_csv_path, index=False, header=False)



def select_multiple_venmo():
    """
    Open a file dialog to select multiple Venmo CSV exports.
    Convert them all to Monarch format with categories, and combine into one CSV.
    """

    # Hide the root Tk window
    root = Tk()
    root.withdraw()

    # Step 1: Ask user to select Venmo files
    venmo_files = filedialog.askopenfilenames(
        title="Select Venmo Export CSV files",
        filetypes=[("CSV files", "*.csv")]
    )

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

    # print(f"Selected files: {venmo_files}")

    for venmo_file in venmo_files:
        venmo_file = os.path.normpath(venmo_file)
        print(f"Processing: {venmo_file}")

        # Use a temporary file for each conversion
        temp_path = tempfile.mktemp(suffix=".csv")
        convert_venmo_to_monarch(venmo_file, temp_path)

        # Read back the converted file and append
        df = pd.read_csv(temp_path, header=None)
        all_outputs.append(df)

    # Step 4: Concatenate everything
    if all_outputs:
        combined_df = pd.concat(all_outputs, ignore_index=True)

        # Convert first column to datetime for sorting
        combined_df[0] = pd.to_datetime(combined_df[0], errors='coerce')
        combined_df = combined_df.sort_values(by=0)  # Sort by Date
        combined_df[0] = combined_df[0].dt.strftime('%Y-%m-%d')  # Format back to string

        combined_df.to_csv(output_file, index=False, header=False)
        print(f"Combined Monarch import file saved to {output_file}")
        print("Monarch: You can upload a .CSV file for a single account on the account details page using the edit button in the top right:",
              "\n • On desktop, navigate to Accounts and select the account to which you want to import.",
              "\n • Select Edit > Upload transactions.\n • Select Upload a .CSV file",
              "\n • Choose the .CSV file and click Add to account",
              "\n • An 'Upload is complete' pop-up will appear in the bottom right-hand corner")
        
    else:
        print("No valid Venmo data found.")
        
        

