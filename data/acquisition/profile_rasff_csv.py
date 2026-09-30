import os
import sys
import csv
import json

RAW_CSV_PATH = os.path.join("data", "raw", "RASFF_window.csv")
EXPECTED_COLUMNS = [
    "reference", "category", "type", "subject", "date",
    "notifying_country", "classification", "risk_decision",
    "distribution", "forAttention", "forFollowUp", "operator",
    "origin", "hazards"
]
EXPECTED_FIELD_COUNT = 14

def detect_csv_properties(filepath):
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            with open(filepath, "r", encoding=enc) as f:
                header = f.readline()
                if header:
                    return enc
        except UnicodeDecodeError:
            continue
    return "utf-8"

def attempt_reconstruction(fields, line_num):
    """
    Attempts deterministic reconstruction of a row with != 14 fields.
    Schema anchors:
      0: reference (e.g., '2024.1234' or alphanumeric reference)
      1: category
      2: type (e.g., 'food', 'feed', 'fcm')
      3..k: subject (most common point of failure due to unquoted commas)
      Last 10 fields anchored from right:
      -1: hazards
      -2: origin
      -3: operator
      -4: forFollowUp
      -5: forAttention
      -6: distribution
      -7: risk_decision
      -8: classification
      -9: notifying_country
      -10: date (YYYY-MM-DD or standard date format)
    """
    raw_count = len(fields)
    ref = fields[0] if fields else f"LINE_{line_num}"

    # Excess fields: typically commas splitting the 'subject' field
    if raw_count > EXPECTED_FIELD_COUNT:
        excess = raw_count - EXPECTED_FIELD_COUNT
        # Anchor left: reference, category, type (indices 0, 1, 2)
        left_fixed = fields[:3]
        # Anchor right: last 10 fields (date through hazards)
        right_fixed = fields[-(EXPECTED_FIELD_COUNT - 4):]
        # Merged candidate subject spans fields[3 : 3 + excess + 1]
        reconstructed_subject = ",".join(fields[3:3 + excess + 1])
        repaired_candidate = left_fixed + [reconstructed_subject] + right_fixed

        # Check validity: date field is at index 4 and repaired count is 14
        candidate_date = repaired_candidate[4]
        # Basic structural check: date usually has hyphens or slashes (e.g. YYYY-MM-DD)
        is_date_plausible = len(candidate_date) >= 8 and any(c in candidate_date for c in ["-", "/"])

        if len(repaired_candidate) == EXPECTED_FIELD_COUNT and is_date_plausible:
            return {
                "line_num": line_num,
                "reference": ref,
                "original_count": raw_count,
                "original_fields": fields,
                "repaired_fields": repaired_candidate,
                "repair_reason": f"Merged {excess + 1} comma-split tokens into 'subject'; verified trailing 10-column anchor & date token.",
                "confidence": "HIGH"
            }
        else:
            return {
                "line_num": line_num,
                "reference": ref,
                "original_count": raw_count,
                "original_fields": fields,
                "repaired_fields": repaired_candidate,
                "repair_reason": f"Attempted 'subject' token merge, but trailing date token ('{candidate_date}') failed standard date heuristic.",
                "confidence": "MEDIUM"
            }

    # Deficit fields: fewer than 14 fields (typically unhandled newline in multi-line field)
    elif raw_count < EXPECTED_FIELD_COUNT:
        return {
            "line_num": line_num,
            "reference": ref,
            "original_count": raw_count,
            "original_fields": fields,
            "repaired_fields": [],
            "repair_reason": f"Field deficit (found {raw_count} fields, expected {EXPECTED_FIELD_COUNT}). Indicates broken row break or truncated stream.",
            "confidence": "LOW / REVIEW_REQUIRED"
        }

    return None

def main():
    if not os.path.exists(RAW_CSV_PATH):
        print(f"ERROR: Raw file not found: {RAW_CSV_PATH}")
        sys.exit(1)

    encoding = detect_csv_properties(RAW_CSV_PATH)
    print(f"[*] Analyzing: {RAW_CSV_PATH}")
    print(f"[*] Detected encoding: {encoding}")
    print(f"[*] Target column structure: {EXPECTED_FIELD_COUNT} columns\n")

    total_data_rows = 0
    valid_rows = 0
    malformed_rows = []
    
    high_repairs = 0
    medium_repairs = 0
    review_required = 0

    with open(RAW_CSV_PATH, "r", encoding=encoding, errors="replace") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            print("ERROR: File is empty.")
            sys.exit(1)

        header_clean = [c.strip() for c in header]
        if len(header_clean) != EXPECTED_FIELD_COUNT:
            print(f"[!] Warning: Header length is {len(header_clean)}, expected {EXPECTED_FIELD_COUNT}")

        line_num = 1
        for row in reader:
            line_num += 1
            total_data_rows += 1
            if len(row) == EXPECTED_FIELD_COUNT:
                valid_rows += 1
            else:
                repair_info = attempt_reconstruction(row, line_num)
                malformed_rows.append(repair_info)
                if repair_info["confidence"] == "HIGH":
                    high_repairs += 1
                elif repair_info["confidence"] == "MEDIUM":
                    medium_repairs += 1
                else:
                    review_required += 1

    # Print detailed diagnosis for each malformed record
    print("=" * 75)
    print(f" MALFORMED RECORD DIAGNOSTIC REPORT ({len(malformed_rows)} records detected)")
    print("=" * 75)

    for idx, item in enumerate(malformed_rows, 1):
        print(f"\n[{idx}] Line {item['line_num']} | Reference: '{item['reference']}'")
        print(f"    - Parsed Field Count : {item['original_count']} (Expected: {EXPECTED_FIELD_COUNT})")
        print(f"    - Repair Assessment  : {item['confidence']}")
        print(f"    - Repair Reason      : {item['repair_reason']}")
        print(f"    - Original Tokens    : {item['original_fields']}")
        if item["repaired_fields"]:
            print(f"    - Repaired (14 cols) : {item['repaired_fields']}")
            assert len(item["repaired_fields"]) == EXPECTED_FIELD_COUNT, "Repaired row field count check failed!"

    # Final Audit Summary
    print("\n" + "=" * 55)
    print(" FINAL DATA INTEGRITY AUDIT")
    print("=" * 55)
    print(f"TOTAL DATA ROWS                  : {total_data_rows:,}")
    print(f"VALID ROWS                       : {valid_rows:,}")
    print(f"MALFORMED ROWS                   : {len(malformed_rows):,}")
    print(f"HIGH-CONFIDENCE REPAIRS          : {high_repairs:,}")
    print(f"MEDIUM-CONFIDENCE REPAIRS        : {medium_repairs:,}")
    print(f"LOW-CONFIDENCE / REVIEW_REQUIRED : {review_required:,}")
    print(f"ROWS DROPPED                     : 0")
    print("=" * 55 + "\n")

if __name__ == "__main__":
    main()