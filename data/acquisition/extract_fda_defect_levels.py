import os
import sys
import re
import hashlib
import pandas as pd

HTML_PATH = os.path.join("data", "reference", "food_safety", "Food Defect Levels Handbook _ FDA.html")
ACQ_DIR = os.path.join("data", "acquisition")

DEFECT_CSV = os.path.join(ACQ_DIR, "fda_defect_levels.csv")
NUT_CSV = os.path.join(ACQ_DIR, "fda_nut_defect_levels.csv")
SUMMARY_MD = os.path.join(ACQ_DIR, "FDA_DEFECT_LEVELS_SUMMARY.md")

SOURCE_DOC_NAME = "Food Defect Levels Handbook _ FDA.html"

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def clean_text(val):
    if pd.isna(val):
        return ""
    text = str(val).replace("\xa0", " ").strip()
    return re.sub(r"\s+", " ", text)

def parse_defect_and_method(raw_defect_text):
    text = clean_text(raw_defect_text)
    if not text:
        return "", ""
    
    # Check for method patterns like (AOAC 981.21), (MPM-V81), etc. in parentheses
    match = re.search(r"^(.*?)\s*\((AOAC[^)]+\vert{}MPM[^)]+\vert{}V-?\d+[^)]*\vert{}Method[^)]*)\)\s*$", text, re.IGNORECASE)
    if match:
        defect_part = match.group(1).strip()
        method_part = match.group(2).strip()
        return defect_part, method_part
    
    # Generic parentheses match at end of string if containing typical method markers
    match_gen = re.search(r"^(.*?)\s*\(([^)]+)\)\s*$", text)
    if match_gen:
        inside = match_gen.group(2).strip()
        if any(marker in inside.upper() for marker in ["AOAC", "MPM", "METHOD", "JAOAC"]):
            return match_gen.group(1).strip(), inside
            
    return text, ""

def main():
    if not os.path.exists(HTML_PATH):
        print(f"ERROR: Local HTML source not found: {HTML_PATH}")
        sys.exit(1)

    os.makedirs(ACQ_DIR, exist_ok=True)

    file_size = os.path.getsize(HTML_PATH)
    file_sha256 = compute_sha256(HTML_PATH)
    print(f"[*] Source loaded: {HTML_PATH} ({file_size:,} bytes, SHA-256: {file_sha256[:12]}...)")

    # Read HTML tables
    tables = pd.read_html(HTML_PATH)
    num_tables = len(tables)
    print(f"[*] HTML tables detected: {num_tables}")

    if num_tables < 2:
        print(f"ERROR: Expected at least 2 tables, found {num_tables}")
        sys.exit(1)

    # -------------------------------------------------------------
    # Process Table 0: General Food Defect Levels
    # -------------------------------------------------------------
    df0 = tables[0].copy()
    raw_table0_rows = len(df0)

    # Clean headers and drop completely empty columns
    df0.columns = [clean_text(c) for c in df0.columns]
    df0 = df0.dropna(how="all", axis=1)

    # Identify relevant columns dynamically
    prod_col = next((c for c in df0.columns if "PRODUCT" in c.upper()), df0.columns[0])
    defect_col = next((c for c in df0.columns if "DEFECT" in c.upper()), df0.columns[1])
    action_col = next((c for c in df0.columns if "ACTION" in c.upper()), df0.columns[2])

    structured_records = []
    special_records = []

    current_product = ""
    for idx, row in df0.iterrows():
        p_val = clean_text(row.get(prod_col, ""))
        d_val = clean_text(row.get(defect_col, ""))
        a_val = clean_text(row.get(action_col, ""))

        # Check for DEFECT SOURCE / SIGNIFICANCE indicator rows
        combined_row_str = f"{p_val} {d_val} {a_val}".upper()
        if "DEFECT SOURCE" in combined_row_str or "SIGNIFICANCE" in combined_row_str:
            special_records.append({
                "PRODUCT_CONTEXT": current_product,
                "RAW_ROW_TEXT": f"{p_val} | {d_val} | {a_val}".strip(" |")
            })
            continue

        # Check if this row is just empty padding or headers
        if not p_val and not d_val and not a_val:
            continue

        # Product name propagation (some rows omit product if multiple defects apply)
        if p_val:
            current_product = p_val

        defect_name, method = parse_defect_and_method(d_val)

        # Retain action level text exactly as written
        structured_records.append({
            "PRODUCT": current_product,
            "DEFECT": defect_name,
            "METHOD": method,
            "ACTION_LEVEL": a_val,
            "SOURCE_DOCUMENT": SOURCE_DOC_NAME,
            "SOURCE_TABLE": "Table 0 (General Foods)"
        })

    df_defects = pd.DataFrame(structured_records)
    df_defects.to_csv(DEFECT_CSV, index=False, encoding="utf-8")
    print(f"[+] Output file generated: {DEFECT_CSV} ({len(df_defects):,} records)")

    # -------------------------------------------------------------
    # Process Table 1: Nut Defect Levels
    # -------------------------------------------------------------
    df1 = tables[1].copy()
    df1.columns = [clean_text(c) for c in df1.columns]
    df1 = df1.dropna(how="all", axis=1)

    nut_records = []
    # Identify nut columns
    nut_col = df1.columns[0]
    unshelled_col = df1.columns[1] if len(df1.columns) > 1 else ""
    shelled_col = df1.columns[2] if len(df1.columns) > 2 else ""

    for idx, row in df1.iterrows():
        n_val = clean_text(row.get(nut_col, ""))
        u_val = clean_text(row.get(unshelled_col, "")) if unshelled_col else ""
        s_val = clean_text(row.get(shelled_col, "")) if shelled_col else ""

        if not n_val and not u_val and not s_val:
            continue

        nut_records.append({
            "NUT_TYPE": n_val,
            "UNSHELLED_PERCENT": u_val,
            "SHELLED_PERCENT": s_val,
            "SOURCE_DOCUMENT": SOURCE_DOC_NAME,
            "SOURCE_TABLE": "Table 1 (Tree Nuts)"
        })

    df_nuts = pd.DataFrame(nut_records)
    df_nuts.to_csv(NUT_CSV, index=False, encoding="utf-8")
    print(f"[+] Output file generated: {NUT_CSV} ({len(df_nuts):,} records)")

    # -------------------------------------------------------------
    # Output Verification
    # -------------------------------------------------------------
    test_defects = pd.read_csv(DEFECT_CSV, dtype=str)
    test_nuts = pd.read_csv(NUT_CSV, dtype=str)
    if len(test_defects) == len(df_defects) and len(test_nuts) == len(df_nuts):
        print(f"[+] Validation result: SUCCESS (Both CSVs verified readable via pandas)")
    else:
        print("[!] Validation result: MISMATCH during verification read-back")

    # -------------------------------------------------------------
    # Summary Report Generation
    # -------------------------------------------------------------
    md = []
    md.append("# FDA Food Defect Levels Extraction Summary\n")
    md.append("## Source Verification & Metadata")
    md.append(f"- **Source File:** `{HTML_PATH}`")
    md.append(f"- **File Size:** {file_size:,} bytes")
    md.append(f"- **SHA-256:** `{file_sha256}`")
    md.append(f"- **HTML Tables Detected:** {num_tables}\n")

    md.append("## Extraction Statistics")
    md.append(f"- **Table 0 Raw Row Count:** {raw_table0_rows:,}")
    md.append(f"- **Structured Defect-Level Records:** {len(df_defects):,}")
    md.append(f"- **DEFECT SOURCE / SIGNIFICANCE Rows Filtered:** {len(special_records):,}")
    md.append(f"- **Table 1 Nut Records:** {len(df_nuts):,}\n")

    md.append("## Output Deliverables")
    md.append(f"- **Primary Defect Levels:** `{DEFECT_CSV}`")
    md.append(f"- **Nut Defect Percentages:** `{NUT_CSV}`\n")

    md.append("## First 10 Structured Defect Records")
    md.append("| Product | Defect | Method | Action Level |")
    md.append("|---|---|---|---|")
    for _, r in df_defects.head(10).iterrows():
        md.append(f"| {r['PRODUCT']} | {r['DEFECT']} | {r['METHOD']} | {r['ACTION_LEVEL']} |")
    md.append("")

    with open(SUMMARY_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print(f"[+] Summary written successfully: {SUMMARY_MD}")

if __name__ == "__main__":
    main()