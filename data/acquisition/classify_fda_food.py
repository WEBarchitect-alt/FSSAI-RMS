import os
import sys
import hashlib
import pandas as pd

RAW_DIR = os.path.join("data", "raw")
ACQ_DIR = os.path.join("data", "acquisition")

RAW_FILES = [
    "REFUSAL_ENTRY_2019_2023.csv",
    "REFUSAL_ENTRY_2024-Aug2026.csv"
]
OUTPUT_CSV = os.path.join(ACQ_DIR, "fda_refusals_classified.csv")
OUTPUT_MD = os.path.join(ACQ_DIR, "FDA_CLASSIFICATION_SUMMARY.md")

HUMAN_FOOD_CODES = {
    "02", "03", "04", "05", "07", "09", "12", "13", "14", "15",
    "16", "17", "18", "20", "21", "22", "23", "24", "25", "26",
    "27", "28", "29", "30", "31", "32", "33", "34", "35", "36",
    "37", "38", "39", "40", "41", "42"
}
DIETARY_SUPPLEMENT_CODES = {"54"}

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

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

def classify_industry(code):
    if pd.isna(code) or len(str(code).strip()) < 2:
        return "", "UNCLASSIFIED_INVALID_CODE"
    
    code_str = str(code).strip()
    prefix = code_str[:2]
    
    if not prefix.isdigit():
        return prefix, "UNCLASSIFIED_INVALID_CODE"

    if prefix in HUMAN_FOOD_CODES:
        return prefix, "HUMAN_FOOD"
    elif prefix in DIETARY_SUPPLEMENT_CODES:
        return prefix, "DIETARY_SUPPLEMENT"
    else:
        return prefix, "NON_FOOD"

def main():
    os.makedirs(ACQ_DIR, exist_ok=True)

    raw_file_metadata = []
    dfs = []

    print("[*] Reading raw FDA refusal files...")
    for filename in RAW_FILES:
        filepath = os.path.join(RAW_DIR, filename)
        if not os.path.exists(filepath):
            print(f"ERROR: Raw file not found: {filepath}")
            sys.exit(1)

        size_before = os.path.getsize(filepath)
        sha_before = compute_sha256(filepath)
        enc, sep = detect_csv_properties(filepath)

        df_part = pd.read_csv(filepath, sep=sep, encoding=enc, dtype=str, low_memory=False)
        df_part.columns = [c.strip() for c in df_part.columns]
        row_count = len(df_part)

        raw_file_metadata.append({
            "filename": filename,
            "filepath": filepath,
            "size_before": size_before,
            "sha_before": sha_before,
            "row_count": row_count
        })
        dfs.append(df_part)
        print(f"    - Loaded `{filename}`: {row_count:,} rows")

    # Combine datasets
    df = pd.concat(dfs, ignore_index=True)
    total_combined_rows = len(df)
    print(f"[*] Total rows loaded across sources: {total_combined_rows:,}")

    # Locate PRODUCT_CODE column
    prod_col = next((c for c in df.columns if c.upper() == "PRODUCT_CODE"), None)
    if not prod_col:
        print(f"ERROR: Column PRODUCT_CODE not found. Existing columns: {list(df.columns)}")
        sys.exit(1)

    print("[*] Applying verified SENTRA-FS classification rules...")
    classified_results = [classify_industry(val) for val in df[prod_col]]
    df["INDUSTRY_CODE"] = [res[0] for res in classified_results]
    df["FOOD_CLASS"] = [res[1] for res in classified_results]

    # Save output CSV
    print(f"[*] Saving classified dataset to: {OUTPUT_CSV}")
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    output_size = os.path.getsize(OUTPUT_CSV)
    print(f"[+] Saved successfully ({output_size:,} bytes).")

    # Verify raw file immutability
    print("[*] Verifying raw file immutability...")
    immutability_verified = True
    for meta in raw_file_metadata:
        current_size = os.path.getsize(meta["filepath"])
        current_sha = compute_sha256(meta["filepath"])
        if current_size != meta["size_before"] or current_sha != meta["sha_before"]:
            immutability_verified = False
            print(f"ERROR: Raw file was altered: {meta['filename']}")
        else:
            meta["verified_unchanged"] = True

    # Parse date using explicit format to prevent inferencing warnings
    date_col = next((c for c in df.columns if "DATE" in c.upper()), None)
    min_date_str, max_date_str = "N/A", "N/A"
    if date_col:
        parsed_dates = pd.to_datetime(df[date_col], format="%d-%b-%y", errors="coerce").dropna()
        if not parsed_dates.empty:
            min_date_str = parsed_dates.min().strftime("%Y-%m-%d")
            max_date_str = parsed_dates.max().strftime("%Y-%m-%d")

    # Summary metrics
    class_counts = df["FOOD_CLASS"].value_counts(dropna=False)
    invalid_count = int(class_counts.get("UNCLASSIFIED_INVALID_CODE", 0))
    industry_counts = df["INDUSTRY_CODE"].value_counts(dropna=False)

    print("[*] Generating summary markdown...")
    md = []
    md.append("# FDA Import Refusal Food Classification Summary\n")

    md.append("## 1. Source Files & Row Counts")
    md.append("| Source File | Row Count | File Size (Bytes) | SHA-256 (Post-Run Check) | Unchanged Verified |")
    md.append("|---|---|---|---|---|")
    for meta in raw_file_metadata:
        md.append(f"| `{meta['filename']}` | {meta['row_count']:,} | {meta['size_before']:,} | `{meta['sha_before']}` | {'YES' if meta.get('verified_unchanged') else 'FAILED'} |")
    md.append(f"\n- **Total Combined Source Rows:** {total_combined_rows:,}")
    md.append(f"- **Total Output Records in Classified CSV:** {len(df):,}")
    md.append(f"- **Output CSV Path:** `{OUTPUT_CSV}`")
    md.append(f"- **Date Range ({date_col}):** `{min_date_str}` to `{max_date_str}`\n")

    md.append("## 2. Counts and Percentages by FOOD_CLASS")
    md.append("| FOOD_CLASS | Record Count | Percentage |")
    md.append("|---|---|---|")
    for fclass, count in class_counts.items():
        pct = (count / total_combined_rows) * 100
        md.append(f"| `{fclass}` | {count:,} | {pct:.2f}% |")
    md.append(f"\n- **Total Invalid `PRODUCT_CODE` Count:** {invalid_count:,}\n")

    md.append("## 3. Counts and Percentages by INDUSTRY_CODE (Top 30)")
    md.append("| INDUSTRY_CODE | Record Count | Percentage | Primary Association |")
    md.append("|---|---|---|---|")
    for ind, count in industry_counts.head(30).items():
        pct = (count / total_combined_rows) * 100
        label = "INVALID/MISSING" if ind == "" else ("HUMAN_FOOD" if ind in HUMAN_FOOD_CODES else ("DIETARY_SUPPLEMENT" if ind in DIETARY_SUPPLEMENT_CODES else "NON_FOOD"))
        md.append(f"| `{ind if ind != '' else '(empty)'}` | {count:,} | {pct:.2f}% | {label} |")
    md.append("")

    md.append("## 4. Raw File Immutability Confirmation")
    if immutability_verified:
        md.append("- **Confirmation:** All source files in `data/raw/` were confirmed unmodified via pre- and post-execution SHA-256 integrity verification.")
    else:
        md.append("- **WARNING:** One or more files in `data/raw/` showed mismatched integrity hashes.")
    md.append("")

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print(f"[+] Summary written successfully to: {OUTPUT_MD}")

if __name__ == "__main__":
    main()