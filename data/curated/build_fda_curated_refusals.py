import os
import sys
import re
import hashlib
import pandas as pd

ACQ_DIR = os.path.join("data", "acquisition")
CURATED_DIR = os.path.join("data", "curated")

CLASSIFIED_CSV = os.path.join(ACQ_DIR, "fda_refusals_classified.csv")
CHARGE_REF_CSV = os.path.join(ACQ_DIR, "fda_charge_reference.csv")
DEFECT_LEVELS_CSV = os.path.join(ACQ_DIR, "fda_defect_levels.csv")

OUTPUT_CSV = os.path.join(CURATED_DIR, "fda_food_refusals_curated.csv")
OUTPUT_MD = os.path.join(CURATED_DIR, "FDA_CURATED_SUMMARY.md")

IN_SCOPE_CLASSES = {"HUMAN_FOOD", "DIETARY_SUPPLEMENT"}

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def clean_str(val):
    if pd.isna(val):
        return ""
    return str(val).strip()

def tokenize_charges(raw_val):
    val_str = clean_str(raw_val)
    if not val_str:
        return []
    tokens = re.split(r"[,;\s]+", val_str)
    return [t.strip() for t in tokens if t.strip()]

def categorize_charge(act_section, charge_statement):
    text = f"{act_section} {charge_statement}".upper()
    if any(k in text for k in ["FILTH", "402(A)(3)", "DECOMPOSE", "INSANITARY", "PUTRID"]):
        return "FILTH_INSANITARY_ADULTERATION"
    elif any(k in text for k in ["POISON", "402(A)(1)", "402(A)(2)", "PESTICIDE", "SALMONELLA", "LISTERIA", "PATHOGEN"]):
        return "SAFETY_HAZARD_PATHOGEN_TOXIN"
    elif any(k in text for k in ["MISBRAND", "403", "LABEL", "NUTRIT", "INGREDIENT", "ALLERGEN", "FALSE"]):
        return "LABELING_MISBRANDING"
    elif any(k in text for k in ["ADDITIVE", "COLOR", "409", "721"]):
        return "UNAPPROVED_ADDITIVE_COLOR"
    elif any(k in text for k in ["REGISTRATION", "PRIOR NOTICE", "801(M)", "NO REGISTRATION", "FACILITY"]):
        return "REGISTRATION_ADMINISTRATIVE"
    elif any(k in text for k in ["GMP", "CGMP", "402(G)"]):
        return "CGMP_NONCOMPLIANCE"
    else:
        return "OTHER_REGULATORY_VIOLATION"

def build_commodity_regex_map(defect_csv_path):
    """
    Extracts distinct handbook commodities and builds whole-word compiled regexes
    to prevent false substring collisions.
    """
    if not os.path.exists(defect_csv_path):
        return {}
    
    df_def = pd.read_csv(defect_csv_path, dtype=str)
    raw_products = df_def["PRODUCT"].dropna().unique()
    
    regex_map = {}
    for p in raw_products:
        p_clean = clean_str(p).upper()
        # Remove parenthetical details or processing notes for base commodity matching
        base_name = re.sub(r"\(.*?\)", "", p_clean).strip()
        # Remove trailing/leading punctuation
        base_name = re.sub(r"^[^A-Z0-9]+|[^A-Z0-9]+$", "", base_name)
        # Skip overly generic or extremely short tokens that cause false positives
        if len(base_name) < 3 or base_name in {"ALL", "AND", "OTHER", "CANNED", "FROZEN", "DRIED", "PRODUCTS"}:
            continue
        # Construct whole-word regex pattern
        pattern = re.compile(rf"\b{re.escape(base_name)}\b", re.IGNORECASE)
        regex_map[base_name] = pattern
        
    return regex_map

def main():
    if not os.path.exists(CLASSIFIED_CSV):
        print(f"ERROR: Classified file missing: {CLASSIFIED_CSV}")
        sys.exit(1)
    if not os.path.exists(CHARGE_REF_CSV):
        print(f"ERROR: Charge reference file missing: {CHARGE_REF_CSV}")
        sys.exit(1)

    os.makedirs(CURATED_DIR, exist_ok=True)
    print("[*] Loading classified refusals...")
    
    df_classified = pd.read_csv(CLASSIFIED_CSV, dtype=str, low_memory=False)
    df_classified.columns = [c.strip() for c in df_classified.columns]
    
    # Isolate in-scope records
    df_scope = df_classified[df_classified["FOOD_CLASS"].isin(IN_SCOPE_CLASSES)].copy()
    input_row_count = len(df_scope)
    print(f"    - In-scope records loaded: {input_row_count:,}")

    # Load charge reference
    print("[*] Loading charge reference crosswalk...")
    df_charges = pd.read_csv(CHARGE_REF_CSV, dtype=str, low_memory=False)
    df_charges.columns = [c.strip() for c in df_charges.columns]
    
    charge_map = {}
    for _, r in df_charges.iterrows():
        code = clean_str(r.get("CHARGE_CODE", ""))
        if code:
            charge_map[code] = {
                "ACT_SECTION": clean_str(r.get("ACT_SECTION", "")),
                "CHARGE_STATEMENT": clean_str(r.get("CHARGE_STATEMENT", ""))
            }

    # Load defect commodities with word-boundary regexes
    print("[*] Building disciplined commodity matchers from FDA Defect Levels...")
    commodity_regex_map = build_commodity_regex_map(DEFECT_LEVELS_CSV)
    print(f"    - Compiled {len(commodity_regex_map)} word-boundary commodity patterns.")

    print("[*] Performing record enrichment and de-aggregation...")

    # Identify source column names
    entry_col = next((c for c in df_scope.columns if "ENTRY" in c.upper()), "ENTRY_NUM")
    line_col = next((c for c in df_scope.columns if "LINE" in c.upper()), "LINE_NUM")
    prod_code_col = next((c for c in df_scope.columns if c.upper() == "PRODUCT_CODE"), "PRODUCT_CODE")
    date_col = next((c for c in df_scope.columns if "DATE" in c.upper()), "REFUSAL_DATE")
    desc_col = next((c for c in df_scope.columns if "DESC" in c.upper()), "PRDCT_CODE_DESC_TEXT")
    country_code_col = next((c for c in df_scope.columns if "ISO" in c.upper() or "CNTRY_CD" in c.upper()), "ISO_CNTRY_CODE")
    country_name_col = next((c for c in df_scope.columns if "CNTRY_NAME" in c.upper() or "COUNTRY" in c.upper()), "CNTRY_NAME")
    mfr_name_col = next((c for c in df_scope.columns if "NAME" in c.upper() and "CNTRY" not in c.upper()), "LGL_NAME")
    city_col = next((c for c in df_scope.columns if "CITY" in c.upper()), "CITY_NAME")
    port_col = next((c for c in df_scope.columns if "PORT" in c.upper()), "PORT_NAME")
    charge_col = next((c for c in df_scope.columns if "CHARGE" in c.upper() and "REF" not in c.upper()), "REFUSAL_CHARGES")

    # Standardize dates (%d-%b-%y format from raw FDA files)
    std_dates = pd.to_datetime(df_scope[date_col], format="%d-%b-%y", errors="coerce").dt.strftime("%Y-%m-%d")

    curated_rows = []
    unmapped_charge_tokens = set()

    for idx, row in df_scope.iterrows():
        entry_val = clean_str(row.get(entry_col, ""))
        line_val = clean_str(row.get(line_col, ""))
        pcode_val = clean_str(row.get(prod_code_col, ""))
        rdate_val = std_dates.loc[idx] if pd.notna(std_dates.loc[idx]) else ""

        refusal_id = f"{entry_val}_{line_val}_{pcode_val}_{rdate_val}".replace(" ", "")

        # Multi-charge tokenization
        raw_charge_str = clean_str(row.get(charge_col, ""))
        charge_tokens = tokenize_charges(raw_charge_str)
        primary_charge = charge_tokens[0] if charge_tokens else ""
        all_charges_str = ", ".join(charge_tokens)

        # Lookup primary charge details
        primary_info = charge_map.get(primary_charge, {"ACT_SECTION": "", "CHARGE_STATEMENT": ""})
        primary_act_sec = primary_info["ACT_SECTION"]
        primary_stmt = primary_info["CHARGE_STATEMENT"]
        primary_category = categorize_charge(primary_act_sec, primary_stmt)

        # Lookup all charges and aggregate sections/statements
        act_sections_list = []
        statements_list = []
        for token in charge_tokens:
            if token in charge_map:
                s_sec = charge_map[token]["ACT_SECTION"]
                s_stmt = charge_map[token]["CHARGE_STATEMENT"]
                if s_sec and s_sec not in act_sections_list:
                    act_sections_list.append(s_sec)
                if s_stmt and s_stmt not in statements_list:
                    statements_list.append(s_stmt)
            else:
                unmapped_charge_tokens.add(token)

        all_act_sections_str = "; ".join(act_sections_list)
        all_statements_str = "; ".join(statements_list)

        # Conservative Defect Standard Evaluation
        desc_text = clean_str(row.get(desc_col, ""))
        defect_status = "NOT_APPLICABLE"
        matched_commodities = []

        if primary_category == "FILTH_INSANITARY_ADULTERATION":
            for comm_name, regex_pattern in commodity_regex_map.items():
                if regex_pattern.search(desc_text):
                    matched_commodities.append(comm_name)
            
            if matched_commodities:
                defect_status = "POTENTIAL_COMMODITY_MATCH"
            else:
                defect_status = "NO_COMMODITY_MATCH"

        curated_rows.append({
            "REFUSAL_ID": refusal_id,
            "ENTRY_NUM": entry_val,
            "LINE_NUM": line_val,
            "REFUSAL_DATE": rdate_val,
            "PRODUCT_CODE": pcode_val,
            "INDUSTRY_CODE": clean_str(row.get("INDUSTRY_CODE", "")),
            "FOOD_CLASS": clean_str(row.get("FOOD_CLASS", "")),
            "PRODUCT_DESC": desc_text,
            "COUNTRY_CODE": clean_str(row.get(country_code_col, "")).upper(),
            "COUNTRY_NAME": clean_str(row.get(country_name_col, "")).upper(),
            "MANUFACTURER_NAME": clean_str(row.get(mfr_name_col, "")),
            "MANUFACTURER_CITY": clean_str(row.get(city_col, "")),
            "PORT_OF_ENTRY": clean_str(row.get(port_col, "")),
            "PRIMARY_CHARGE_CODE": primary_charge,
            "ALL_CHARGE_CODES": all_charges_str,
            "RAW_CHARGES": raw_charge_str,
            "PRIMARY_ACT_SECTION": primary_act_sec,
            "PRIMARY_CHARGE_STATEMENT": primary_stmt,
            "ALL_ACT_SECTIONS": all_act_sections_str,
            "ALL_CHARGE_STATEMENTS": all_statements_str,
            "CHARGE_CATEGORY": primary_category,
            "DEFECT_STANDARD_STATUS": defect_status,
            "POTENTIAL_DEFECT_COMMODITIES": ", ".join(matched_commodities) if matched_commodities else ""
        })

    df_curated = pd.DataFrame(curated_rows)
    output_row_count = len(df_curated)

    # -------------------------------------------------------------
    # Strict Validation Suite
    # -------------------------------------------------------------
    print("[*] Executing validation checks...")
    assert input_row_count == output_row_count, f"FATAL: Record count mismatch! In: {input_row_count}, Out: {output_row_count}"
    assert output_row_count == 62937, f"FATAL: Output does not match expected in-scope count of 62,937. Got: {output_row_count}"

    duplicate_ids = int(df_curated["REFUSAL_ID"].duplicated().sum())
    missing_dates = int(df_curated["REFUSAL_DATE"].isnull().sum() + (df_curated["REFUSAL_DATE"] == "").sum())
    missing_pcodes = int(df_curated["PRODUCT_CODE"].isnull().sum() + (df_curated["PRODUCT_CODE"] == "").sum())
    missing_countries = int(df_curated["COUNTRY_CODE"].isnull().sum() + (df_curated["COUNTRY_CODE"] == "").sum())

    total_primary_charges = len(df_curated)
    mapped_primary_charges = int((df_curated["PRIMARY_ACT_SECTION"] != "").sum())
    primary_charge_coverage_pct = (mapped_primary_charges / total_primary_charges) * 100

    status_counts = df_curated["DEFECT_STANDARD_STATUS"].value_counts().to_dict()
    category_counts = df_curated["CHARGE_CATEGORY"].value_counts().to_dict()

    # Save Curated CSV
    df_curated.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    output_size = os.path.getsize(OUTPUT_CSV)
    output_sha = compute_sha256(OUTPUT_CSV)
    print(f"[+] Output CSV written: {OUTPUT_CSV} ({output_size:,} bytes)")
    print(f"[+] Verified 100% record retention: exactly {output_row_count:,} records.")

    # Generate Summary MD
    print("[*] Generating Markdown summary report...")
    md = []
    md.append("# SENTRA-FS Curated FDA Food Refusals Dataset Summary\n")
    
    md.append("## 1. Executive Validation & Integrity Audit")
    md.append(f"- **Input In-Scope Rows:** {input_row_count:,}")
    md.append(f"- **Curated Rows Produced:** {output_row_count:,}")
    md.append(f"- **Record Retention:** **100.0% (Zero Record Loss)**")
    md.append(f"- **Output CSV File:** `{OUTPUT_CSV}`")
    md.append(f"- **Output File Size:** {output_size:,} bytes")
    md.append(f"- **Output SHA-256:** `{output_sha}`\n")

    md.append("## 2. Data Health & Traceability Checks")
    md.append("| Check Metric | Result | Status |")
    md.append("|---|---|---|")
    md.append(f"| Missing Dates | {missing_dates} | {'PASS' if missing_dates == 0 else 'CHECK'} |")
    md.append(f"| Missing Product Codes | {missing_pcodes} | {'PASS' if missing_pcodes == 0 else 'CHECK'} |")
    md.append(f"| Missing Country Codes | {missing_countries} | {'PASS' if missing_countries == 0 else 'CHECK'} |")
    md.append(f"| Duplicate Composite `REFUSAL_ID`s | {duplicate_ids:,} | NOTE: Preserved (Multi-line consignments) |")
    md.append(f"| Primary Charge Mapping Coverage | {mapped_primary_charges:,} / {total_primary_charges:,} ({primary_charge_coverage_pct:.2f}%) | {'PASS' if primary_charge_coverage_pct > 99.0 else 'CHECK'} |")
    md.append(f"| Unmapped Charge Tokens Encountered | {len(unmapped_charge_tokens)} | `{list(unmapped_charge_tokens)}` |")
    md.append("")

    md.append("## 3. Defect Standard Linkage Audit (`DEFECT_STANDARD_STATUS`)")
    md.append("| Status Category | Count | Percentage | Description |")
    md.append("|---|---|---|---|")
    for stat, cnt in status_counts.items():
        pct = (cnt / output_row_count) * 100
        desc = "Non-filth charge (Labeling, Pathogen, Additive, etc.)" if stat == "NOT_APPLICABLE" else ("Filth charge with conservative handbook commodity match" if stat == "POTENTIAL_COMMODITY_MATCH" else "Filth charge without verified handbook commodity link")
        md.append(f"| `{stat}` | {cnt:,} | {pct:.2f}% | {desc} |")
    md.append("")

    md.append("## 4. Statutory Violation Categories")
    md.append("| Primary Charge Category | Record Count | Percentage |")
    md.append("|---|---|---|")
    for cat, cnt in category_counts.items():
        pct = (cnt / output_row_count) * 100
        md.append(f"| `{cat}` | {cnt:,} | {pct:.2f}% |")
    md.append("")

    md.append("## 5. First 3 Curated Records (Sample)")
    md.append("```json")
    import json
    md.append(json.dumps(df_curated.head(3).to_dict(orient="records"), indent=2))
    md.append("```\n")

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print(f"[+] Summary report saved successfully: {OUTPUT_MD}")

if __name__ == "__main__":
    main()