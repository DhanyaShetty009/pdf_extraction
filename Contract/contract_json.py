import pdfplumber
import json
import re
import configparser

tax_mapping = {
    "Pay in/Pay out obligation": "Pay in/Pay out obligation",
    "Taxable value of Supply": "Taxable value of Supply (Brokerage)",
    "Exchange transaction": "Exchange transaction charges",
    "Clearing charges": "Clearing charges",
    "CGST": "CGST (@9% of Brok, SEBI, Trans & Clearing Charges)",
    "SGST": "SGST (@9% of Brok, SEBI, Trans & Clearing Charges)",
    "IGST": "IGST (@18% of Brok, SEBI, Trans & Clearing Charges)",
    "Securities transaction": "Securities transaction tax",
    "SEBI turnover": "SEBI turnover fees",
    "Stamp duty": "Stamp duty",
    "Net amount": "Net amount receivable/(payable by client)"
}

def tax_section(line):
    parts = re.split(r'\s+', line.strip())
    equity = "NA"
    futures = "NA"
    net_total = "NA"
    
    numbers = [p for p in parts if re.match(r'\(?\-?\d+\.?\d*\)?', p)]
    if numbers:
        if len(numbers) >= 3:
            equity = numbers[-3]
            futures = numbers[-2]
            net_total = numbers[-1]
        elif len(numbers) == 2:
            equity = numbers[0]
            futures = "NA"
            net_total = numbers[1]
        elif len(numbers) == 1:
            equity = numbers[0]
            futures = "NA"
            net_total = numbers[0]
    
    return equity, futures, net_total

def extract_contract_data(pdf_path,password):
    with pdfplumber.open(pdf_path,password=password) as pdf:
        page = pdf.pages[0]
        text = page.extract_text()
        lines = text.split('\n')
        
        contract_data = {
            "Equities": [],
            "Net Total": "",
            "Tax Invoice": []
        }
        
        current_stocks = []
        in_tax_section = False
        constant_quantity = 14
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            if re.match(r'\d{16,19}', line):
                parts = line.split()
              
                order_no = parts[0]
                order_time = parts[1]
                trade_no = parts[2]
                trade_time = parts[3]
                
                security_desc = ""
                desc_parts = []
                j = 4
                while j < len(parts) and not re.match(r'^[BS]$', parts[j]):
                    desc_parts.append(parts[j])
                    j += 1
                security_desc = ' '.join(desc_parts)
                
                if i + 1 < len(lines) and "EQ/" in lines[i + 1]:
                    security_desc += "\n" + lines[i + 1].strip()
            
                bs = parts[j]
                exchange = parts[j + 1]
                quantity = parts[j + 2]
                price = parts[j + 3]
                
                net_total = float(quantity) * float(price)
                
                stock_entry = {
                    "Order No.": order_no,
                    "Order Time": order_time,
                    "Trade No.": trade_no,
                    "Trade Time": trade_time,
                    "Security / Contract Description": security_desc,
                    "Buy(B)/ Sell(S)": bs,
                    "Exchange": exchange,
                    "Quantity": quantity,
                    "Gross Rate/Trade Price Per Unit(Rs)": f"{float(price):.2f}",
                    "Brokerage per Unit (Rs)": "NA",
                    "Net Rate per Unit (Rs)": price,
                    "Closing Rate per Unit (only for Derivatives) (Rs)": "NA",
                    "Net Total (Before Levies) (Rs)": f"({net_total:.2f})",
                    "Remarks": "NA"
                }
                current_stocks.append(stock_entry)

            elif "Sub Total" in line:
                if current_stocks:
                    sub_total = sum(float(stock["Net Total (Before Levies) (Rs)"].strip("()")) 
                                  for stock in current_stocks)
                    equity_entry = {
                        "Stock": current_stocks,
                        "Sub Total": {
                            "quantity": constant_quantity,
                            "Net Total (Before Levies) (Rs)": f"({sub_total:.2f})"
                        }
                    }
                    contract_data["Equities"].append(equity_entry)
                    current_stocks = []
            if contract_data["Equities"]:
                total = sum(float(entry["Sub Total"]["Net Total (Before Levies) (Rs)"].strip("()"))
                          for entry in contract_data["Equities"])
                contract_data["Net Total"] = f"({total:.2f})"
           
            if "Trade Equity" in line:
                in_tax_section = True
                continue
                
            if in_tax_section:
                for key_start, full_key in tax_mapping.items():
                    if line.startswith(key_start):
                        equity, futures, net_total = tax_section(line)
                        
                        if futures == "0.00":
                            futures = "0.00"
                        
                        tax_entry = {
                            full_key: {
                                "Equity": equity,
                                "Futures and Options": futures
                            },
                            "NET TOTAL": net_total
                        }
                        contract_data["Tax Invoice"].append(tax_entry)
                        break
        
        return contract_data

def save_json(data, json_output_path):
    with open(json_output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def main():
    config = configparser.ConfigParser()
    config.read("config.properties")
    pdf_path = config.get("Contract", "pdf_path")
    json_output_path = config.get("Contract", "json_output_path")
    pdf_password = 'ADFPV2032B'  
    
    try:
        contract_data = extract_contract_data(pdf_path,pdf_password)
        save_json(contract_data, json_output_path)
        print(f"JSON data saved to: {json_output_path}")
    except Exception as e:
        print(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    main()