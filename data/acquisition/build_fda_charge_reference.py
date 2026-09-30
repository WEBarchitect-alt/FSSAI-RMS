import os
import sys
import re
from collections import Counter
import pandas as pd

RAW_DIR = os.path.join("data", "raw")
ACQ_DIR = os.path.join("data", "acquisition")

CHARGES_CSV = os.path.join(RAW_DIR, "ACT_SECTION_CHARGES.csv")
CLASSIFIED_CSV = os.path.join(ACQ_DIR, "fda_refusals_classified.csv")

OUTPUT_CSV = os.path.join(ACQ_DIR, "fda_charge_reference.csv")
OUTPUT_MD = os.path.join(ACQ_DIR, "FDA_CHARGE_REFERENCE.md")

TARGET_CLASSES = {"HUMAN_FOOD", "DIETARY_SUPPLEMENT"}

def detect_csv_properties(filepath):
    encodings = ["utf-8", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            with open(filepath, "r", encoding=enc) as f:
                first_lines = [f.readline() for _ in range(5)]
            break
        except UnicodeDecodeError:
            continue

    first_line = first_lines[0] if first_lines else ""
    delimiter = ","
    if "\t" in first_line and first_line.count("\t") > first_line.count(","):
        delimiter = "\t"
    elif "|" in first_line and first_line.count("|") > first_line.count(","):
        delimiter = "|"

    return enc, delimiter

def load_charge_reference():
    if not os.path.exists(CHARGES_CSV):
        print(f"ERROR: Reference table not found: {CHARGES_CSV}")
        sys.exit(1)

    enc, sep = detect_csv_properties(CHARGES_CSV)
    df_ref = pd.read_csv(CHARGES_CSV, sep=sep, encoding=enc, dtype=str, low_memory=False)
    df_ref.columns = [c.strip() for c in df_ref.columns]

    # Identify key column (e.g., CHARGE_ID, CHARGE_CODE, ACT_SECTION_ID, or first column)
    key_col = None
    for c in df_ref.columns:
        if any(term in c.upper() for term in ["CHARGE_ID", "CHARGE_CODE", "ACT_SECTION_ID", "CODE"]):
            key_col = c
            break
    if not key_col:
        key_col = df_ref.columns[0]

    # Standardize lookup key as stripped string
    df_ref["_LOOKUP_KEY"] = df_ref[key_col].astype(str).str.strip()

    # Index by lookup key; drop duplicates if any
    ref_dict = {}
    for _, row in df_ref.iterrows():
        k = row["_LOOKUP_KEY"]
        if k and k not in ref_dict:
            ref_dict[k] = row.to_dict()

    return df_ref, key_col, ref_dict

def extract_charge_tokens(raw_val):
    if pd.isna(raw_val):
        return []
    val_str = str(raw_val).strip()
    if not val_str:
        return []
    # Split on commas, semicolons, or whitespace if multiple codes are grouped
    tokens = re.split(r"[,;\s]+", val_str)
    return [t.strip() for t in tokens if t.strip()]

def main():
    if not os.path.exists(CLASSIFIED_CSV):
        print(f"ERROR: Classified file not found: {CLASSIFIED_CSV}")
        sys.exit(1)

    print("[*] Inspecting ACT_SECTION_CHARGES reference source...")
    df_ref, key_col, ref_dict = load_charge_reference()
    print(f"    - Reference file loaded: {len(df_ref):,} rows, {len(df_ref.columns)} columns")
    print(f"    - Identified Key Column: `{key_col}`")
    print(f"    - Reference columns: {list(df_ref.columns)}")

    print("[*] Reading classified refusals dataset...")
    enc, sep = detect_csv_properties(CLASSIFIED_CSV)
    df = pd.read_csv(CLASSIFIED_CSV, sep=sep, encoding=enc, dtype=str, low_memory=False)
    df.columns = [c.strip() for c in df.columns]

    # Filter to HUMAN_FOOD and DIETARY_SUPPLEMENT
    food_mask = df["FOOD_CLASS"].isin(TARGET_CLASSES)
    df_food = df[food_mask].copy()
    print(f"    - Filtered records (HUMAN_FOOD + DIETARY_SUPPLEMENT): {len(df_food):,} rows")

    # Locate REFUSAL_CHARGES column
    charges_col = next((c for c in df_food.columns if "REFUSAL_CHARGE" in c.upper() or "CHARGE" in c.upper()), None)
    if not charges_col:
        print(f"ERROR: Could not locate refusal charge column in {list(df_food.columns)}")
        sys.exit(1)
    print(f"    - Using Refusal Charges Column: `{charges_col}`")

    # Count charge code occurrences across rows
    charge_counter = Counter()
    for val in df_food[charges_col]:
        tokens = extract_charge_tokens(val)
        for t in tokens:
            charge_counter[t] += 1

    distinct_codes = sorted(charge_counter.keys(), key=lambda x: (not x.isdigit(), int(x) if x.isdigit() else x))
    total_distinct = len(distinct_codes)
    print(f"[*] Found {total_distinct} distinct charge codes across in-scope food records.")

    # Match against reference dictionary
    matched_rows = []
    unmatched_codes = []

    # Get metadata columns from df_ref (excluding temporary lookup key)
    ref_cols = [c for c in df_ref.columns if c != "_LOOKUP_KEY"]

    for code in distinct_codes:
        freq = charge_counter[code]
        if code in ref_dict:
            ref_data = ref_dict[code]
            row_data = {
                "CHARGE_CODE": code,
                "OCCURRENCE_COUNT": freq,
                "MATCH_STATUS": "MATCHED"
            }
            for col in ref_cols:
                row_data[col] = ref_data.get(col, "")
            matched_rows.append(row_data)
        else:
            unmatched_codes.append((code, freq))
            row_data = {
                "CHARGE_CODE": code,
                "OCCURRENCE_COUNT": freq,
                "MATCH_STATUS": "UNMATCHED"
            }
            for col in ref_cols:
                row_data[col] = "UNMATCHED_IN_REFERENCE"
            matched_rows.append(row_data)

    df_out = pd.DataFrame(matched_rows)
    df_out.sort_values(by="OCCURRENCE_COUNT", ascending=False, inplace=True)
    df_out.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    print(f"[+] Output CSV written: {OUTPUT_CSV}")

    # Summary Metrics
    matched_count = total_distinct - len(unmatched_codes)
    match_pct = (matched_count / total_distinct) * 100 if total_distinct > 0 else 0.0

    total_charge_citations = sum(charge_counter.values())
    matched_citations = sum(charge_counter[code] for code in distinct_codes if code in ref_dict)
    citation_coverage_pct = (matched_citations / total_charge_citations) * 100 if total_charge_citations > 0 else 0.0

    print("[*] Generating Markdown report...")
    md = []
    md.append("# SENTRA-FS FDA Refusal Charge Reference Mapping Report\n")

    md.append("## 1. Executive Summary")
    md.append(f"- **Scope:** `HUMAN_FOOD` + `DIETARY_SUPPLEMENT` records")
    md.append(f"- **Total In-Scope Refusal Rows Analyzed:** {len(df_food):,}")
    md.append(f"- **Total Charge Code Citations Counted:** {total_charge_citations:,}")
    md.append(f"- **Distinct Refusal Charge Codes Found:** {total_distinct}")
    md.append(f"- **Matched Against `ACT_SECTION_CHARGES.csv`:** {matched_count} ({match_pct:.2f}%)")
    md.append(f"- **Unmatched Codes:** {len(unmatched_codes)}")
    md.append(f"- **Citation Volume Coverage:** {matched_citations:,} of {total_charge_citations:,} citations mapped ({citation_coverage_pct:.2f}%)\n")

    md.append("## 2. Reference Source Metadata")
    md.append(f"- **Reference File:** `{CHARGES_CSV}`")
    md.append(f"- **Reference Table Rows:** {len(df_ref):,}")
    md.append(f"- **Key Column Used for Lookup:** `{key_col}`")
    md.append(f"- **Reference Attributes Present:** `{ref_cols}`\n")

    md.append("## 3. Top 30 Most Frequent Matched Refusal Charges")
    md.append("| Charge Code | Frequency | Statutory / Charge Details |")
    md.append("|---|---|---|")

    matched_subset = df_out[df_out["MATCH_STATUS"] == "MATCHED"].head(30)
    for _, row in matched_subset.iterrows():
        code = row["CHARGE_CODE"]
        freq = row["OCCURRENCE_COUNT"]
        # Compile available descriptive columns
        details = " | ".join([f"{col}: {row[col]}" for col in ref_cols if col != key_col and pd.notna(row[col]) and str(row[col]).strip() != ""])
        md.append(f"| `{code}` | {freq:,} | {details} |")
    md.append("")

    md.append("## 4. Unmatched Charge Codes")
    if unmatched_codes:
        md.append("| Charge Code | Frequency | Status |")
        md.append("|---|---|---|")
        for code, freq in sorted(unmatched_codes, key=lambda x: x[1], reverse=True):
            md.append(f"| `{code}` | {freq:,} | NOT FOUND IN ACT_SECTION_CHARGES |")
    else:
        md.append("All distinct in-scope charge codes matched successfully into `ACT_SECTION_CHARGES.csv`.")
    md.append("")

    md.append("## 5. Methodological & Governance Confirmations")
    md.append("- No meanings or legal citations were synthesized, inferred by AI, or fabricated for missing entries.")
    md.append("- Files in `data/raw/` were read in read-only mode and remain completely unchanged.")
    md.append("- Downstream mappings strictly trace to verified FDA source dictionaries.")

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print(f"[+] Markdown report generated successfully: {OUTPUT_MD}")

if __name__ == "__main__":
    main()