import csv
import re
import os
from pypdf import PdfReader

INPUT_DIR = r"data/raw/india/fira_lab"
OUTPUT = r"data/curated/india_lab_rejection_aggregates.csv"

FILES = {
    "2021-2022.pdf": "2021-22",
    "2022-2023.pdf": "2022-23",
    "2023-2024.pdf": "2023-24",
}

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

rows = []

for filename, financial_year in FILES.items():
    path = os.path.join(INPUT_DIR, filename)

    print(f"[*] Reading {path}")

    reader = PdfReader(path)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)

    text = text.replace("\r", "")
    text = text.replace("ï‚·", "•")

    # Match numbered country blocks until the next numbered country
    # or the final total.
    pattern = re.compile(
        r"(?ms)^\s*(\d+)\.?\s+"
        r"([A-Z][A-Z &\-]+?)\s+"
        r"(\d+)\s+"
        r"(.*?)(?=^\s*\d+\.?\s+[A-Z]|^Total rejections|\Z)"
    )

    matches = pattern.finditer(text)

    count = 0

    for match in matches:
        serial, country, rejection_count, items = match.groups()

        country = re.sub(r"\s+", " ", country).strip()
        items = re.sub(r"\s+", " ", items).strip()

        rows.append([
            financial_year,
            country,
            int(rejection_count),
            items,
            filename,
            "Laboratory Stage (Safety/ Quality parameters)"
        ])

        count += 1

    print(f"    [+] Country records extracted: {count}")

with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)

    writer.writerow([
        "financial_year",
        "country_of_origin",
        "rejection_count",
        "rejected_items",
        "source_file",
        "stage"
    ])

    writer.writerows(rows)

print()
print("=" * 70)
print(" INDIA FIRA LABORATORY REJECTION EXTRACTION")
print("=" * 70)
print(f"Output file       : {OUTPUT}")
print(f"Country records   : {len(rows):,}")
print(f"Total rejections  : {sum(r[2] for r in rows):,}")
print(f"Financial years   : {sorted(set(r[0] for r in rows))}")
print("=" * 70)