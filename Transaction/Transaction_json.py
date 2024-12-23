import pdfplumber
import json
import configparser

config = configparser.ConfigParser()
config.read("config.properties")

pdf_path = config.get("Transaction", "pdf_path")
json_output_path = config.get("Transaction", "json_output_path")
pdf_password = 'ADFPV2032B'

def extract_data(pdf_path,password):
    data = {
        "Statement of Account": "2024-04-01 to 2024-04-30",
        "Transactions for given Period": [],
        "Holding as on 2024-04-30": {"List": [], "Total": {}}
    }

    with pdfplumber.open(pdf_path,password=password) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            lines = text.split("\n")
            
            current_isin = None
            current_symbol = None
            opening_balance = None
            closing_balance = None
            transactions = []

            for line in lines:
                if "ISIN:" in line:
                    if current_isin:  
                        data["Transactions for given Period"].append({
                            "ISIN": current_isin,
                            "Symbol": current_symbol,
                            "Opening balance": opening_balance,
                            "Closing balance": closing_balance,
                            "Transactions": transactions
                        })
                        transactions = [] 

                    parts = line.split("Symbol:")
                    current_isin = parts[0].replace("ISIN:", "").strip()
                    current_symbol = parts[1].strip() if len(parts) > 1 else None

                elif "Opening balance:" in line:
                    opening_balance = line.split(":")[1].strip()

                elif "Closing balance:" in line:
                    closing_balance = line.split(":")[1].strip()

                elif any(keyword in line for keyword in ["Transactions", "Early Pay-in", "CA"]):  
                    txn_parts = line.split()
                    if len(txn_parts) >= 5:
                        date = txn_parts[0]
                        desc = " ".join(txn_parts[1:-3])
                        buy = txn_parts[-3]
                        sell = txn_parts[-2]
                        balance = txn_parts[-1]
                        transactions.append({
                            "Date": date,
                            "Transaction Description": desc,
                            "Buy/Cr": buy,
                            "Sell/Dr": sell,
                            "Balance": balance
                        })

                elif "ISIN Code" in line: 
                    for hold_line in lines[lines.index(line) + 1:]:
                        if "Total:" in hold_line:
                            totals = hold_line.split()
                            data["Holding as on 2024-04-30"]["Total"] = {
                                "Curr. Bal": totals[2],
                                "Free Bal": totals[3],
                                "Pldg. Bal": totals[4],
                                "Earmark Bal": totals[5],
                                "Demat": totals[6],
                                "Remat": totals[7],
                                "Lockin": totals[8],
                                "Rate": "",
                                "Value": totals[10]
                            }
                            break
                        else:
                            hold_parts = hold_line.split()
                            if len(hold_parts) >= 10:  
                                data["Holding as on 2024-04-30"]["List"].append({
                                    "ISIN Code": hold_parts[0],
                                    "Company Name": " ".join(hold_parts[1:-9]),
                                    "Curr. Bal": hold_parts[-9],
                                    "Free Bal": hold_parts[-8],
                                    "Pldg. Bal": hold_parts[-7],
                                    "Earmark Bal": hold_parts[-6],
                                    "Demat": hold_parts[-5],
                                    "Remat": hold_parts[-4],
                                    "Lockin": hold_parts[-3],
                                    "Rate": hold_parts[-2],
                                    "Value": hold_parts[-1]
                                })
                    break  

            if current_isin:
                data["Transactions for given Period"].append({
                    "ISIN": current_isin,
                    "Symbol": current_symbol,
                    "Opening balance": opening_balance,
                    "Closing balance": closing_balance,
                    "Transactions": transactions
                })

    return data

data = extract_data(pdf_path,pdf_password)
with open(json_output_path, 'w') as json_file:
    json.dump(data, json_file, indent=4)


print(f"JSON data saved to: {json_output_path}")
