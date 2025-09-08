"""
convertPayPal.py
Viva R. Horowitz
vibe-coded using chatGPT
2025-07-05

Download paypal_csv from https://www.paypal.com/reports/dlog


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

"""

import pandas as pd
import os
from tkinter import Tk, filedialog

def convert_paypal_to_monarch(paypal_csv_path: str, monarch_csv_path: str, account_name: str) -> None:
    df = pd.read_csv(paypal_csv_path)
    print(f"Original rows: {len(df)}")

    df["Date"] = pd.to_datetime(df["Date"], errors='coerce').dt.strftime("%Y-%m-%d")
    df["Name"] = df["Name"].fillna("")
    df["Type"] = df["Type"].fillna("")
    df["Transaction ID"] = df["Transaction ID"].fillna("")
    df["Fees"] = pd.to_numeric(df["Fees"], errors='coerce').fillna(0.0)
    df["Amount"] = pd.to_numeric(df["Amount"], errors='coerce').fillna(0.0)

    # Create a key to group by
    df["key"] = df.apply(lambda row: (row["Date"], row["Amount"], row["Name"], row["Transaction ID"]), axis=1)
    print(f"Rows after key creation: {len(df)}")

    def pick_preferred(group):
        completed = group[group["Status"] == "Completed"]
        if not completed.empty:
            non_pre = completed[completed["Type"] != "PreApproved Payment Bill User Payment"]
            if not non_pre.empty:
                return non_pre.iloc[0]
            else:
                return completed.iloc[0]
        else:
            return group.iloc[0]

    # Keep 'key' after reset_index by not dropping it
    filtered_rows = df.groupby("key", group_keys=False).apply(pick_preferred, include_groups=False).reset_index()
    print(f"Rows after picking preferred duplicates: {len(filtered_rows)}")

    def drop_preapproved_duplicates(df):
        # 'key' column is available here
        preapproved = df[df["Type"] == "PreApproved Payment Bill User Payment"]
        others = df[df["Type"] != "PreApproved Payment Bill User Payment"]

        mask = preapproved["key"].isin(others["key"])
        preapproved_to_keep = preapproved[~mask]

        result = pd.concat([others, preapproved_to_keep], ignore_index=True)
        return result

    filtered_rows = drop_preapproved_duplicates(filtered_rows)
    print(f"Rows after dropping preapproved duplicates: {len(filtered_rows)}")

    monarch_rows = []

    for _, row in filtered_rows.iterrows():
        date = row["Date"]
        name = row["Name"]
        txn_type = row["Type"]
        amount = row["Amount"]
        fee = row["Fees"]
        transaction_id = row["Transaction ID"]
        item_title = row.get("Item Title", "")
        original_statement_parts = [txn_type]
        if transaction_id:
            original_statement_parts.append(f"({transaction_id})")
        if isinstance(item_title, str) and item_title.strip():
            original_statement_parts.append(f"- {item_title.strip()}")
        original_statement = " ".join(original_statement_parts)

        category = ""
        if txn_type.strip() == "Bank Deposit to PP Account" and name.strip() == "":
            category = "Transfer for paypal"
            merchant = "Transfer"
            memo = txn_type
        elif txn_type == "General Card Deposit":
            category = "Transfer for paypal"
            merchant = "Transfer"
            memo = txn_type
        else:
            merchant = name
            memo = original_statement
            if "User Initiated Withdrawal" in original_statement:
                category = "Transfer for paypal"
            elif name == "Wikimedia Foundation, Inc.":
                category = "Charity"
            elif name == "Lyft":
                category = "Taxi & Ride Shares"
            elif name == "ChargeSmart EV LLC":
                category = "Gas"
            elif name == "eBay Commerce Inc.":
                category = "Shopping"
            elif name == "Poshmark":
                category = "Shopping"

        monarch_rows.append({
            "Date": date,
            "Merchant": merchant,
            "Category": category,
            "Account": account_name,
            "Original Statement": memo,
            "Notes": "",
            "Amount": amount,
            "Tags": ""
        })

        if fee != 0.0:
            monarch_rows.append({
                "Date": date,
                "Merchant": "PayPal",
                "Category": "Fees",
                "Account": account_name,
                "Original Statement": f"Fee for {merchant} on {date}",
                "Notes": "",
                "Amount": -abs(fee),
                "Tags": ""
            })

    monarch_df = pd.DataFrame(monarch_rows, columns=[
        "Date", "Merchant", "Category", "Account", "Original Statement", "Notes", "Amount", "Tags"
    ])

    print(f"Final rows to export: {len(monarch_df)}")
    monarch_df.to_csv(monarch_csv_path, index=False)
    print(f"Saved Monarch CSV to '{monarch_csv_path}'")


if __name__ == "__main__":
    # File picker for input CSV
    Tk().withdraw()
    print("Look for file dialogue!")
    input_file = filedialog.askopenfilename(
        title="Select PayPal CSV",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )

    if input_file:
        output_file = os.path.join(
            os.path.dirname(input_file),
            "monarch_upload3.csv"
        )
        convert_paypal_to_monarch(input_file, output_file, "PayPal")
    else:
        print("No file selected.")