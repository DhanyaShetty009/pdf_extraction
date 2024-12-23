import pdfplumber
import json
import configparser

config = configparser.ConfigParser()
config.read("config.properties")

pdf_path = config.get("WeeklySecurities", "pdf_path")
json_output_path = config.get("WeeklySecurities", "json_output_path")

def extract_table_to_json(pdf_path):
   
    result = {
        "Ledger Code": "HG9197",
        "Statement of Accounts of Securities/Commodities for the period": "2024-05-27 to 2024-06-01",
        "Statement of Account reflecting Clear Balance as on the last date of statement": [],
        "Pending Obligations as on 2024-06-01 (as on Saturday)": []
    }
    
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        tables = page.extract_tables()
        
        for table in tables:
            for row in table[1:]:
                transaction = {
                    "Transaction Date": row[0],
                    "Execution Date": row[1],
                    "Clearing Corporation / Clearing Member": row[2],
                    "Segment Type": row[3],
                    "Unique Client Code (UCC)": row[4],
                    "Back Office Client Code": row[5],
                    "Client Name": row[6],
                    "Client PAN": row[7],
                    "Member Demat Account No.": {
                        "To": "",
                        "From": row[8]
                    },
                    "Counterparty Demat Account No.": {
                        "To": row[9],
                        "From": ""
                    },
                    "Settlement No.": row[10],
                    "ISIN Code": row[11],
                    "Scrip Name": row[12],
                    "Quantity Delivered (Qty.)": row[13],
                    "Quantity Received (Qty.)": row[14],
                    "Balance(Qty.)": row[15],
                    "Trf.Ref. No.": row[16],
                    "Transaction Type": row[17],
                    "Purpose": row[18]
                }
                
                if transaction["Transaction Type"] == "Transactions within DP":
                    result["Statement of Account reflecting Clear Balance as on the last date of statement"].append(transaction)
                else:
                    result["Pending Obligations as on 2024-06-01 (as on Saturday)"].append(transaction)
    
    return result

table_data = extract_table_to_json(pdf_path)
json_output = json.dumps(table_data, indent=4)

with open(json_output_path, 'w') as json_file:
    json.dump(table_data, json_file, indent=4)

print(f"JSON data saved to: {json_output_path}")