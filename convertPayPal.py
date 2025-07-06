"""
convertPayPal.py
Viva R. Horowitz
vibe-coded using chatGPT
2025-07-05
"""

import pandas as pd


def convert_paypal_to_monarch(paypal_csv_path: str, monarch_csv_path: str, account_name: str) -> None:
    """
    Convert PayPal CSV export to Monarch-compatible CSV format (8 columns).
    
    Parameters:
    - paypal_csv_path: input path to PayPal CSV file
    - monarch_csv_path: output path for Monarch CSV file
    - account_name: string for the Account column in Monarch CSV
    """
    # Load PayPal CSV
    paypal_df = pd.read_csv(paypal_csv_path)

    # Convert date format from MM/DD/YYYY to YYYY-MM-DD
    paypal_df["Date"] = pd.to_datetime(paypal_df["Date"], format="%m/%d/%Y").dt.strftime("%Y-%m-%d")

    monarch_rows = []

    for _, row in paypal_df.iterrows():
        date = row["Date"]
        name = row["Name"] if pd.notna(row["Name"]) else ""
        txn_type = row["Type"] if pd.notna(row["Type"]) else ""
        amount = float(row["Amount"])
        fee = float(row["Fees"])
        transaction_id = row["Transaction ID"] if pd.notna(row["Transaction ID"]) else ""
        item_title = row["Item Title"] if pd.notna(row["Item Title"]) else ""

        # Handle special transfer rows
        if txn_type == "Bank Deposit to PP Account " and name.strip() == "":
            merchant = "Transfer"
            category = "Transfer for paypal"
            memo = txn_type
        else:
            merchant = name
            category = ""  # You can improve by categorizing based on type or name if desired
            memo_parts = [txn_type]
            if transaction_id:
                memo_parts.append(f"({transaction_id})")
            if item_title.strip():
                memo_parts.append(f"- {item_title}")
            memo = " ".join(memo_parts)

            # Skip these "Bank Deposit to PP Account " transfers (non-transfer blank name handled above)
            if txn_type == "Bank Deposit to PP Account ":
                continue

        # Add main transaction row
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

        # Add fee transaction if applicable
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
    monarch_df.to_csv(monarch_csv_path, index=False)
    print(f"Converted transactions saved to '{monarch_csv_path}'")


# Example usage:
# convert_paypal_to_monarch("paypal_export.csv", "paypal_to_monarch.csv", "PayPal Checking")
