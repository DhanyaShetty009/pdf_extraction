import pdfplumber
import json
import configparser

config = configparser.ConfigParser()
config.read("config.properties")

pdf_path = config.get("WeeklyAccount", "pdf_path")
json_output_path = config.get("WeeklyAccount", "json_output_path")

def extract_table_to_json(pdf_path):
   
    result = {
        "Ledger Code" : "HG9197",
        "Statement of Accounts of Funds for the period":"2024-05-27 to 2024-06-01 (Monday to Saturday)",
        "Statement of Account reflecting Clear Balance as on the last date of statement":[],
        "Pending Obligations/Uncleared cheques as on 2024-06-01 (as on Saturday)": []
    }
    
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        tables = page.extract_tables()
        
        for table in tables:
            for row in table[1:]:
                transaction = {
                    "Unique Client Code (UCC).": row[0],
                    "Charges date": row[1],
                    "Back Office Client Code": row[2],
                    "Client Name": row[3],
                    "Client PAN": row[4],
                    "Transaction Date": row[5],
                    "Settlement Date": row[6],
                    "Clearing Corporation/Clearing Member": row[7],
                    "Segment Type": row[8],
                    "Settlement No.": row[9],
                    "Bill/Chq No.": row[10],
                    "Transaction Type": row[11],
                    "Particulars/Narration": row[12],
                    "Voucher No.": row[13],
                    "Debit(Rs.)": row[14],
                    "Credit(Rs.)": row[15],
                    "Balance(Rs.)": row[16]
                  }
                
                if float(transaction["Balance(Rs.)"]) >= 0:
                    result["Statement of Account reflecting Clear Balance as on the last date of statement"].append(transaction)
                else:
                    result["Pending Obligations/Uncleared cheques as on 2024-06-01 (as on Saturday)"].append(transaction)
    
    return result

table_data = extract_table_to_json(pdf_path)
json_output = json.dumps(table_data, indent=4)

with open(json_output_path, 'w') as json_file:
    json.dump(table_data, json_file, indent=4)
  
print(f"JSON data saved to: {json_output_path}")