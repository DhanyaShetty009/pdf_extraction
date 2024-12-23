import pdfplumber
import re
import json
import configparser


def clean_value(value):
    if value is None or value.strip() == '' or value.strip().upper() == 'NA':
        return "NA"
    return value.strip()


def extract_margin_available(text):
    data = []
    segments = ['EQ', 'FO', 'CDS', 'SLB', 'Sub Total']
    lines = text.split('\n')
    start_idx = None
    end_idx = None
    
    for i, line in enumerate(lines):
        if 'Margin Available' in line:
            start_idx = i + 1
        elif start_idx and 'Margin Required' in line:
            end_idx = i
            break
    
    if start_idx and end_idx:
        section_lines = lines[start_idx:end_idx]
        for segment in segments:
            segment_line = next((line for line in section_lines if line.strip().startswith(segment)), None)
            if segment_line:
                parts = segment_line.split()
                while len(parts) < 6:
                    parts.append("NA")
                    
                data.append({
                    "Segment": segment,
                    "Trade Date": "21/05/2024",
                    "Funds - Annex A": clean_value(parts[2] if len(parts) > 2 else "NA"),
                    "Value of Securities - Annex B": clean_value(parts[3] if len(parts) > 3 else "NA"),
                    "Any other approved form of Margins (EPI) - Annex C": clean_value(parts[4] if len(parts) > 4 else "NA"),
                    "Total Margin Available": clean_value(parts[5] if len(parts) > 5 else "NA")
                })
    
    return data


def extract_margin_required(text):
    data = []
    segments = ['EQ', 'FO', 'CDS', 'SLB', 'Sub Total']
    lines = text.split('\n')
    start_idx = None
    end_idx = None
    margin_data = []
    
    for i, line in enumerate(lines):
        if 'Margin Required' in line and ('Upfront' in line or 'Required' in line):
            start_idx = i
            continue
        if start_idx is not None and 'Margin Collected' in line:
            end_idx = i
            break
        if start_idx is not None and end_idx is None:
            margin_data.append(line.strip())
    
    for segment in segments:
        segment_line = next((line for line in margin_data if line.startswith(segment)), None)
        if segment_line:
            parts = [p for p in re.split(r'\s+', segment_line) if p]
           
            segment_data = {
                "Segment": segment,
                "Trade Date": "21/05/2024",
                "Upfront Margin Required": clean_value(parts[2] if len(parts) > 2 else "NA"),
                "Consolidated Crystallized Obligation Required": clean_value(parts[3] if len(parts) > 3 else "NA"),
                "Delivery Margin Required": clean_value(parts[4] if len(parts) > 4 else "NA"),
                "Total EOD Margin required": clean_value(parts[5] if len(parts) > 5 else "NA"),
                "Total Peak Margins required": clean_value(parts[6] if len(parts) > 6 else "NA")
            }
            data.append(segment_data)
    
    return data


def extract_margin_collected(text):
    data = []
    segments = ['EQ', 'FO', 'CDS', 'SLB', 'Sub Total']
    
    lines = text.split('\n')
    start_idx = None
    end_idx = None
    
    for i, line in enumerate(lines):
        if 'Margin Collected' in line and 'Upfront Margin' in line:
            start_idx = i + 1
        elif start_idx and 'Indicative Peak Snapshot' in line:
            end_idx = i
            break
    
    if start_idx and end_idx:
        section_lines = lines[start_idx:end_idx]
        for segment in segments:
            segment_line = next((line for line in section_lines if line.strip().startswith(segment)), None)
            if segment_line:
                parts = re.split(r'\s+', segment_line.strip())
                
                data.append({
                    "Segment": segment,
                    "Trade Date": "21/05/2024",
                    "Upfront Margin Collected": clean_value(parts[2] if len(parts) > 2 else "NA"),
                    "Consolidated Crystallized Obligation Collected": clean_value(parts[3] if len(parts) > 3 else "NA"),
                    "Delivery Margin Collected": clean_value(parts[4] if len(parts) > 4 else "NA"),
                    "Total EOD Margin Collected": clean_value(parts[5] if len(parts) > 5 else "NA"),
                    "EOD Excess/Short": clean_value(parts[6] if len(parts) > 6 else "NA"),
                    "Total Peak Margin Collected": clean_value(parts[7] if len(parts) > 7 else "NA"),
                    "Peak Excess/Shortfall": clean_value(parts[8] if len(parts) > 8 else "NA")
                })
    
    return data


def extract_annex_a(text):
    lines = text.split('\n')
    annex_data = {}
    
    start_idx = None
    for i, line in enumerate(lines):
        if 'Annex A Funds Explained' in line:
            start_idx = i + 1
            break
    
    if start_idx:
        try:
            values = []
            for j in range(4):
                if start_idx + j < len(lines):
                    line = lines[start_idx + j].strip()
                    value = line.split()[-1] if line.split() else "NA"
                    values.append(value)
            
            if len(values) == 4:
                annex_data = {
                    "Closing Balance": clean_value(values[0]),
                    "Unsettled Credit(-)": clean_value(values[1]),
                    "Unsettled Debts(+)": clean_value(values[2]),
                    "Funds Available": clean_value(values[3])
                }
        except Exception as e:
            print(f"Error extracting Annex A data: {str(e)}")
    
    return annex_data


def create_empty_annex_structure():
    return [{
        "Trading Symbol": "NA",
        "ISIN": "NA",
        "QTY": "NA",
        "Value(Post Haircut)": "NA"
    }]


def extract_peak_snapshot(text):
    data = []
    segments = ['EQ', 'FO', 'CDS']
    
    lines = text.split('\n')
    snapshot_section = False
    
    for line in lines:
        if 'Indicative Peak Snapshot Time' in line:
            snapshot_section = True
            continue
        if snapshot_section and any(segment in line.split() for segment in segments):
            parts = line.strip().split()
            if len(parts) >= 2:
                data.append({
                    "Segment": parts[0],
                    "Indicative Peak Snapshot Time": ' '.join(parts[-2:]) if 'PM' in line or 'AM' in line else clean_value(parts[-1])
                })
    
    return data


def process_pdf(pdf_path, json_output_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        margin_required_data = extract_margin_required(text)
        
        result = [
            {"Margin Available": extract_margin_available(text)},
            {"Margin Required": margin_required_data},  
            {"Margin Collected": extract_margin_collected(text)},
            {"Annex A: FundsExplained": extract_annex_a(text)},
            {"Annex B: Pledging Stocks": create_empty_annex_structure()},
            {"Annex C: Value of EPI": create_empty_annex_structure()}
        ]

        snapshot_data = extract_peak_snapshot(text)
        result.extend(snapshot_data)
        
        with open(json_output_path, "w") as json_file:
            json.dump(result,json_file, indent=2)

        print(f"JSON data saved to: {json_output_path}")

    except Exception as e:
        print(f"Error processing PDF: {str(e)}")


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("config.properties")

    pdf_path = config.get("Margin", "pdf_path")
    json_output_path = config.get("Margin", "json_output_path")
    
    process_pdf(pdf_path, json_output_path)


