import pdfplumber
import json
import configparser

config = configparser.ConfigParser()
config.read("config.properties")

pdf_path = config.get("TradeDetails", "pdf_path")
json_output_path = config.get("TradeDetails", "json_output_path")
pdf_password = 'ADFPV2032B'  

def extract_table_to_json(pdf_path, password):
    with pdfplumber.open(pdf_path, password=password) as pdf:
        first_page = pdf.pages[0]
        tables = first_page.extract_tables()
        
        json_data = []
        if tables:
            for table in tables:
                headers = [header.replace("\n", " ").strip() for header in table[0]]
                for row in table[1:]:
                    row_data = dict(zip(headers, row))
                    json_data.append(row_data)
    
    return json_data
table_data = extract_table_to_json(pdf_path,pdf_password)
json_output = json.dumps(table_data, indent=4)
print(f"JSON data saved to: {json_output_path}")

with open(json_output_path, 'w') as json_file:
    json.dump(table_data, json_file, indent=4)

