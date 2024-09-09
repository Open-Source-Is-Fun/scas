# ERC-20 Token Accounting Spreadsheet Generator Version 1
# Currently based on the Snowtrace API but future version might include more API calls
# Tested Python Versions: 3.12.3, 3.10.12

import os
import json
import pytz
import pandas as pd
from requests import get
from datetime import datetime
from odf.opendocument import OpenDocumentSpreadsheet
from odf.table import Table


# Save the timestamp of the last recorderd transaction and put it into last_reference.json
def save_last_reference(last_reference):
    print(f"Saving new reference: {last_reference}")
    with open(f"{directory_path}last_reference.json", "w") as f:
        json.dump({"last_reference": last_reference}, f)

# Load the last timestamp of previous run
def load_last_reference():
    try:
        with open(f"{directory_path}last_reference.json", "r") as f:
            data = json.load(f)
            last_reference = data.get("last_reference", 0)
            print(f"Loading last reference: {last_reference}")
            return last_reference
    except FileNotFoundError:
        print("No previous reference")
        return "2023-01-01T00:00:00.000Z"

# Import User-to-Wallet address bindings
def load_memberId():
    with open(f"{directory_path}Wallets.json", "r") as f:
        data = json.load(f)
    return data

# Find the UserID based on the "Wallet" Value from Wallets.json
def find_memberId(dictionary, value):
    for key, val in dictionary[0].items():
        if value in val['Wallets']:
            return int(key)
    return None

# Check if .ods file exists from before
def odf_exist_checker(file_path, sheet_name):
    if os.path.exists(file_path):
        print(f"The file {file_path} exists.")
    else:
        print(f"The file {file_path} does not exist.")
        create_new_ods(file_path, sheet_name)

# Create new .ods file if it doesn't exist from before
def create_new_ods(file_path, sheet_name):
    print(f"Creating new .ods file with sheet name '{sheet_name}': {file_path}")
    doc = OpenDocumentSpreadsheet()
    table = Table(name=sheet_name)
    doc.spreadsheet.addElement(table)
    doc.save(file_path)
    print(f"The file: {file_path} has been created")

# Convert timestamps to a human readable format
def convert_timestamp(timestamp_str):
    print(f"Converting timestamp: {timestamp_str} ", end="")
    utc_time = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    utc_zone = pytz.utc
    oslo_zone = pytz.timezone('Europe/Oslo')
    utc_time = utc_zone.localize(utc_time)
    datetime_oslo = utc_time.astimezone(oslo_zone)

    formatted_date = datetime_oslo.strftime("%d-%m-%Y")
    print(f"To: {formatted_date}")
    return formatted_date

# Concatenates the token value, token symbol (i.e. ETH) and decimal number to produce a human readable value
def convert_token_value(value, decimals, token_symbol):
    print(f"Converting Token value: {value} ", end="")
    non_decimals = int(len(value)) - int(decimals)
    if non_decimals == 0:
        rounded_decimals = round(
            float(f"0{value[:non_decimals]}.{value[non_decimals:non_decimals+2]}"), 2
        )
    else:
        rounded_decimals = round(
            float(f"{value[:non_decimals]}.{value[non_decimals:non_decimals+2]}"), 2
        )
    new_value = f"{rounded_decimals} {token_symbol.upper()}"
    print(f"To: {rounded_decimals}")
    return new_value

# Translate Chain ID's of Ethereum and Avalanche to their respective names
def convert_chainID_value(chain_id):
    print(f"Converting chainID: {chain_id}", end="")
    if chain_id == "1":
        network = "Ethereum"
    elif chain_id == "43114":
        network = "Avalanche"
    else:
        network = chain_id
    print(f"To: {network}")
    return network

# If the script has run before, only fetch new data after the value inside last_reference.json
def fetch_new_data(last_reference):
    print("Fetching data from api")
    transactions_url = f"https://api.routescan.io/v2/network/mainnet/evm/all/address/{address}/erc20-transfers?sort=desc&limit=100"
    response = get(transactions_url)
    response_data = response.json()
    print(response_data)
    return response_data

# Process the new data from the timestamp in last_reference.json and onwards
def process_data():
    last_reference = load_last_reference()
    response_data = fetch_new_data(last_reference)
    print("Response from api was successful")
    transactions = response_data["items"]
    if transactions:
        counter = 0
        for transaction in transactions:
            if str(transaction["timestamp"]) == str(last_reference):
                print(
                f"Last reference detected in fetched data, deleting it and all subsequent from transactions")
                transactions = transactions[:counter]
                break
            counter += 1
    if not transactions:
        print("No new transactions fetched")
        return []
    else:
        last_transaction = transactions[0]
        new_last_reference = last_transaction["timestamp"]
        save_last_reference(new_last_reference)
        print(f"Transactions fetched: {transactions}")
        return transactions

# Structure new data to be appended to a file
def append_transaction_data(transactions):
    print("Appending data to list rows")
    wallet_data = load_memberId()
    for transaction in transactions:
        curr_timestamp = convert_timestamp(transaction["timestamp"])
        curr_amount = convert_token_value(
            transaction["amount"],
            transaction["tokenDecimals"],
            transaction["tokenSymbol"],
        )
        curr_network = convert_chainID_value(transaction["chainId"])
        curr_memberId = find_memberId(wallet_data, transaction["from"])

        date_rows.append(curr_timestamp)
        from_rows.append(transaction["from"])
        to_rows.append(transaction["to"])
        transactionID_rows.append(transaction["txHash"])
        network_rows.append(curr_network)
        amount_rows.append(curr_amount)
        memberId_rows.append(curr_memberId)

# Write structured data to a .ods file (Libre Office Calc format)
def write_to_odf(file_path, sheet_name):
    print(f"Writing to .odf file: {file_path}")
    # Stores every sheet in file as a dictionary key
    existing_dfs = {}
    try:
        existing_dfs = pd.read_excel(file_path, sheet_name=None, engine="odf")
    except:
        pass
    # Append data to the existing DataFrame of the desired sheet or create a new DataFrame
    if sheet_name in existing_dfs:
        existing_df = existing_dfs[sheet_name]
        new_data = {
            "Date": date_rows,
            "MemberID": memberId_rows,
            "From:": from_rows,
            "To:": to_rows,
            "Transaction ID": transactionID_rows,
            "Network": network_rows,
            "Amount": amount_rows,
            "Other": [None] * len(date_rows), # Can be used for notes
        }
        new_df = pd.DataFrame(new_data)
        appended_df = pd.concat([existing_df, new_df], ignore_index=True)
        existing_dfs[sheet_name] = appended_df
    else:
        new_data = {
            "Date": date_rows,
            "MemberID": memberId_rows,
            "From:": from_rows,
            "To:": to_rows,
            "Transaction ID": transactionID_rows,
            "Network": network_rows,
            "Amount": amount_rows,
            "Other": [None] * len(date_rows),
        }
        new_df = pd.DataFrame(new_data)
        existing_dfs[sheet_name] = new_df

    # Write all data back to the file
    with pd.ExcelWriter(file_path, engine="odf") as writer:
        for sheet_name, df in existing_dfs.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    print(f"Finished writing to .odf file: {file_path}")


# --------------------------
# ---------- Main ----------
# --------------------------

# Snowtrace API call
address = "0x..." # The wallet address of interest

# Current timezone stamp at code execution
timezone = pytz.timezone("Europe/London")
now = datetime.now(timezone)
month = now.strftime("%B")  # Full month name, e.g., "May"
# month = "July"
year = now.strftime("%Y")  # Year with century, e.g., "2024"
# year = "2025"


# .ods yearly file path declaration
# NB! replace directory_path
directory_path = "/path/to/file/"
file_path = f"{directory_path}Crypto_accounting-{year}.ods"

# Create empty rows for each coloum
date_rows = []
from_rows = []
to_rows = []
transactionID_rows = []
network_rows = []
amount_rows = []
memberId_rows = []

print("Starting script")

odf_exist_checker(file_path, sheet_name=month)
transactions = process_data()
if transactions:
    append_transaction_data(transactions)
    # Reverese the list to descending order to align with future runs
    date_rows.reverse()
    from_rows.reverse()
    to_rows.reverse()
    transactionID_rows.reverse()
    network_rows.reverse()
    amount_rows.reverse()
    memberId_rows.reverse()
    write_to_odf(file_path, sheet_name=month)

print("Ending script")
