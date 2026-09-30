# SENTRA-FS RASFF Cleaning Audit Report

## 1. Executive Summary
- **Raw Source File:** `data\raw\RASFF_window.csv`
- **Clean Output File:** `data\curated\rasff_border_events_clean.csv`
- **Raw Row Count:** 30,000
- **Clean Row Count:** 30,000
- **Malformed Rows Detected:** 17
- **Rows Successfully Repaired:** 17
- **Rows Unresolved:** 0
- **Rows Dropped:** 0 (0 required)
- **Duplicate References:** 0
- **Integrity Status:** **100% PRESERVED & VALIDATED**

## 2. Cleaning & Reconstruction Methodology
1. **Fixed Left Anchor (Columns 0–2):** `reference`, `category`, and `type` remain pristine.
2. **Dynamic Date Anchor (Column 4):** Identifies the official timestamp token using strict `DD-MM-YYYY HH:MM:SS` regex pattern matching.
3. **Subject Reconstitution (Column 3):** Commas split by unescaped quotation inside `subject` are deterministically re-joined from index 3 up to the date anchor index.
4. **Fixed Right Anchor (Columns 5–13):** All trailing 9 fields (`notifying_country` through `hazards`) preserve their exact alignment.
5. **Deterministic Handling of Reference `2021.2621`:** Unescaped trailing backslash quote (`\",`) parsed by standard RFC-4180 readers was isolated; embedded timestamp extracted and aligned with trailing attributes.

## 3. Detailed Register of Repaired References
| # | Line No | Reference | Raw Token Count | Clean Token Count | Repair Method |
|---|---|---|---|---|---|
| 1 | 776 | `2026.6704` | 15 | 14 | Reconstructed subject from fields [3:5]; anchored date at field 5. |
| 2 | 3816 | `2026.0039` | 16 | 14 | Reconstructed subject from fields [3:6]; anchored date at field 6. |
| 3 | 11031 | `2024.6416` | 15 | 14 | Reconstructed subject from fields [3:5]; anchored date at field 5. |
| 4 | 12001 | `2024.4612` | 16 | 14 | Reconstructed subject from fields [3:6]; anchored date at field 6. |
| 5 | 12555 | `2024.3652` | 15 | 14 | Reconstructed subject from fields [3:5]; anchored date at field 5. |
| 6 | 15226 | `2023.7761` | 16 | 14 | Reconstructed subject from fields [3:6]; anchored date at field 6. |
| 7 | 15297 | `2023.7640` | 15 | 14 | Reconstructed subject from fields [3:5]; anchored date at field 5. |
| 8 | 15545 | `2023.7176` | 15 | 14 | Reconstructed subject from fields [3:5]; anchored date at field 5. |
| 9 | 18056 | `2023.2459` | 16 | 14 | Reconstructed subject from fields [3:6]; anchored date at field 6. |
| 10 | 18071 | `2023.2422` | 17 | 14 | Reconstructed subject from fields [3:7]; anchored date at field 7. |
| 11 | 20201 | `2022.6073` | 15 | 14 | Reconstructed subject from fields [3:5]; anchored date at field 5. |
| 12 | 21711 | `2022.3330` | 15 | 14 | Reconstructed subject from fields [3:5]; anchored date at field 5. |
| 13 | 21840 | `2022.3085` | 15 | 14 | Reconstructed subject from fields [3:5]; anchored date at field 5. |
| 14 | 23440 | `2022.0520` | 16 | 14 | Reconstructed subject from fields [3:6]; anchored date at field 6. |
| 15 | 25544 | `2021.4513` | 15 | 14 | Reconstructed subject from fields [3:5]; anchored date at field 5. |
| 16 | 26775 | `2021.2621` | 13 | 14 | Extracted embedded timestamp from subject token; realigned trailing 9 fields. |
| 17 | 28976 | `2020.5385` | 15 | 14 | Reconstructed subject from fields [3:5]; anchored date at field 5. |
