import os
import sys
import csv
import re

RAW_PATH = os.path.join("data", "raw", "RASFF_window.csv")
CLEAN_PATH = os.path.join("data", "curated", "rasff_border_events_clean.csv")
AUDIT_PATH = os.path.join("data", "curated", "RASFF_CLEANING_AUDIT.md")

EXPECTED_COLUMNS = [
    "reference", "category", "type", "subject", "date",
    "notifying_country", "classification", "risk_decision",
    "distribution", "forAttention", "forFollowUp", "operator",
    "origin", "hazards"
]
EXPECTED_FIELD_COUNT = 14

KNOWN_MALFORMED_REFERENCES = {
    "2026.6704", "2026.0039", "2024.6416", "2024.4612", "2024.3652",
    "2023.7761", "2023.7640", "2023.7176", "2023.2459", "2023.2422",
    "2022.6073", "2022.3330", "2022.3085", "2022.0520", "2021.4513",
    "2021.2621", "2020.5385"
}

DATE_PATTERN = re.compile(r"^\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}$")
EMBEDDED_DATE_PATTERN = re.compile(r"(\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2})")

def main():
    if not os.path.exists(RAW_PATH):
        print(f"FATAL ERROR: Raw source file not found at {RAW_PATH}")
        sys.exit(1)

    print(f"[*] Starting RASFF cleaning pipeline...")
    print(f"[*] Reading raw file: {RAW_PATH}")

    total_raw_rows = 0
    malformed_rows_detected = 0
    repaired_rows = []
    unresolved_rows = []
    cleaned_data = []
    seen_references = set()
    duplicate_references = []

    with open(RAW_PATH, "r", encoding="utf-8", errors="replace") as f_in:
        reader = csv.reader(f_in)
        try:
            raw_header = next(reader)
        except StopIteration:
            print("FATAL ERROR: Raw CSV file is completely empty.")
            sys.exit(1)

        raw_header_clean = [c.strip() for c in raw_header]
        if raw_header_clean != EXPECTED_COLUMNS:
            print(f"FATAL ERROR: Header mismatch! Found: {raw_header_clean}")
            sys.exit(1)

        for line_no, row in enumerate(reader, start=2):
            total_raw_rows += 1
            ref = row[0].strip() if row else f"UNKNOWN_LINE_{line_no}"

            if len(row) == EXPECTED_FIELD_COUNT:
                clean_row = row
            else:
                malformed_rows_detected += 1
                try:
                    if ref == "2021.2621" or len(row) == 13:
                        # Special case: date embedded inside field 3
                        t3 = row[3]
                        m = EMBEDDED_DATE_PATTERN.search(t3)
                        if not m:
                            raise ValueError(f"No date pattern found in token 3: {t3}")
                        date_val = m.group(1)
                        subj_val = t3[:m.start()].rstrip('",\\ \t\n')
                        # Remaining fields: notifying_country through hazards (9 items)
                        clean_row = [row[0], row[1], row[2], subj_val, date_val] + row[4:]
                        repair_method = "Extracted embedded timestamp from subject token; realigned trailing 9 fields."
                    elif len(row) > EXPECTED_FIELD_COUNT:
                        # Find date token index dynamically using DD-MM-YYYY HH:MM:SS
                        date_idx = -1
                        for i, token in enumerate(row):
                            if DATE_PATTERN.match(token.strip()):
                                date_idx = i
                                break
                        
                        if date_idx == -1:
                            raise ValueError(f"No standard date token found across parsed tokens: {row}")
                        
                        subj_val = ",".join(row[3:date_idx])
                        clean_row = row[:3] + [subj_val] + row[date_idx:]
                        repair_method = f"Reconstructed subject from fields [3:{date_idx}]; anchored date at field {date_idx}."
                    else:
                        raise ValueError(f"Unhandled field count ({len(row)})")

                    if len(clean_row) != EXPECTED_FIELD_COUNT:
                        raise ValueError(f"Repaired row length is {len(clean_row)}, expected {EXPECTED_FIELD_COUNT}")

                    repaired_rows.append({
                        "line_no": line_no,
                        "reference": ref,
                        "original_field_count": len(row),
                        "repair_method": repair_method,
                        "clean_row": clean_row
                    })

                except Exception as ex:
                    unresolved_rows.append({
                        "line_no": line_no,
                        "reference": ref,
                        "error": str(ex),
                        "row": row
                    })
                    continue

            # Track duplicate references
            if clean_row[0] in seen_references:
                duplicate_references.append(clean_row[0])
            seen_references.add(clean_row[0])

            cleaned_data.append(clean_row)

    # -------------------------------------------------------------
    # Write Destination Clean CSV
    # -------------------------------------------------------------
    os.makedirs(os.path.dirname(CLEAN_PATH), exist_ok=True)
    with open(CLEAN_PATH, "w", encoding="utf-8", newline="") as f_out:
        writer = csv.writer(f_out)
        writer.writerow(EXPECTED_COLUMNS)
        writer.writerows(cleaned_data)

    clean_row_count = len(cleaned_data)
    rows_dropped = total_raw_rows - clean_row_count

    # -------------------------------------------------------------
    # Verification & Strict Failure Checks
    # -------------------------------------------------------------
    repaired_references = {r["reference"] for r in repaired_rows}
    missing_known_malformed = KNOWN_MALFORMED_REFERENCES - repaired_references

    print(f"[*] Validating output integrity...")

    if clean_row_count != total_raw_rows:
        print(f"FATAL: Clean row count ({clean_row_count:,}) != Raw row count ({total_raw_rows:,})")
        sys.exit(1)

    if rows_dropped != 0:
        print(f"FATAL: Rows were dropped ({rows_dropped})!")
        sys.exit(1)

    if len(unresolved_rows) != 0:
        print(f"FATAL: Unresolved malformed rows remain ({len(unresolved_rows)})!")
        sys.exit(1)

    if missing_known_malformed:
        print(f"FATAL: Missing known malformed references from repaired set: {missing_known_malformed}")
        sys.exit(1)

    # Verify each row in cleaned_data has 14 fields
    for idx, row in enumerate(cleaned_data, start=1):
        if len(row) != EXPECTED_FIELD_COUNT:
            print(f"FATAL: Output row {idx} has {len(row)} fields instead of {EXPECTED_FIELD_COUNT}")
            sys.exit(1)

    # -------------------------------------------------------------
    # Generate Audit Markdown
    # -------------------------------------------------------------
    md = []
    md.append("# SENTRA-FS RASFF Cleaning Audit Report\n")
    md.append("## 1. Executive Summary")
    md.append(f"- **Raw Source File:** `{RAW_PATH}`")
    md.append(f"- **Clean Output File:** `{CLEAN_PATH}`")
    md.append(f"- **Raw Row Count:** {total_raw_rows:,}")
    md.append(f"- **Clean Row Count:** {clean_row_count:,}")
    md.append(f"- **Malformed Rows Detected:** {malformed_rows_detected}")
    md.append(f"- **Rows Successfully Repaired:** {len(repaired_rows)}")
    md.append(f"- **Rows Unresolved:** {len(unresolved_rows)}")
    md.append(f"- **Rows Dropped:** {rows_dropped} (0 required)")
    md.append(f"- **Duplicate References:** {len(duplicate_references)}")
    md.append(f"- **Integrity Status:** **100% PRESERVED & VALIDATED**\n")

    md.append("## 2. Cleaning & Reconstruction Methodology")
    md.append("1. **Fixed Left Anchor (Columns 0–2):** `reference`, `category`, and `type` remain pristine.")
    md.append("2. **Dynamic Date Anchor (Column 4):** Identifies the official timestamp token using strict `DD-MM-YYYY HH:MM:SS` regex pattern matching.")
    md.append("3. **Subject Reconstitution (Column 3):** Commas split by unescaped quotation inside `subject` are deterministically re-joined from index 3 up to the date anchor index.")
    md.append("4. **Fixed Right Anchor (Columns 5–13):** All trailing 9 fields (`notifying_country` through `hazards`) preserve their exact alignment.")
    md.append("5. **Deterministic Handling of Reference `2021.2621`:** Unescaped trailing backslash quote (`\\\",`) parsed by standard RFC-4180 readers was isolated; embedded timestamp extracted and aligned with trailing attributes.\n")

    md.append("## 3. Detailed Register of Repaired References")
    md.append("| # | Line No | Reference | Raw Token Count | Clean Token Count | Repair Method |")
    md.append("|---|---|---|---|---|---|")
    for idx, r in enumerate(repaired_rows, 1):
        md.append(f"| {idx} | {r['line_no']} | `{r['reference']}` | {r['original_field_count']} | 14 | {r['repair_method']} |")
    md.append("")

    with open(AUDIT_PATH, "w", encoding="utf-8") as f_audit:
        f_audit.write("\n".join(md))

    print(f"[+] Audit report saved: {AUDIT_PATH}")
    print(f"[+] Clean CSV saved: {CLEAN_PATH}")

    # -------------------------------------------------------------
    # Print Validation Summary
    # -------------------------------------------------------------
    print("\n" + "=" * 65)
    print(" SENTRA-FS RASFF CLEANING PIPELINE VALIDATION SUMMARY")
    print("=" * 65)
    print(f"Raw Row Count             : {total_raw_rows:,}")
    print(f"Clean Row Count           : {clean_row_count:,}")
    print(f"Malformed Rows Detected   : {malformed_rows_detected}")
    print(f"Rows Repaired             : {len(repaired_rows)}")
    print(f"Rows Unresolved           : {len(unresolved_rows)}")
    print(f"Rows Dropped              : {rows_dropped}")
    print(f"Duplicate References      : {len(duplicate_references)}")
    print(f"Columns in Clean CSV      : {EXPECTED_FIELD_COUNT}")
    print(f"Known Malformed Repaired  : {len(repaired_references & KNOWN_MALFORMED_REFERENCES)} / {len(KNOWN_MALFORMED_REFERENCES)}")
    print(f"Pipeline Result           : SUCCESS - ALL AUDIT CRITERIA MET")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    main()