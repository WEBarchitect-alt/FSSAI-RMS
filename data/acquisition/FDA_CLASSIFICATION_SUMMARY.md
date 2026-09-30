# FDA Import Refusal Food Classification Summary

## 1. Source Files & Row Counts
| Source File | Row Count | File Size (Bytes) | SHA-256 (Post-Run Check) | Unchanged Verified |
|---|---|---|---|---|
| `REFUSAL_ENTRY_2019_2023.csv` | 76,819 | 16,689,107 | `5663194bab8787187d2d58a8aa295cfaf1eb5c637782895f659fbfce7be8f9dd` | YES |
| `REFUSAL_ENTRY_2024-Aug2026.csv` | 89,517 | 18,655,445 | `85679c8cc673c3210652848f17b5fcc26f8cfeea48d86320ce577c5d3d0ef628` | YES |

- **Total Combined Source Rows:** 166,336
- **Total Output Records in Classified CSV:** 166,336
- **Output CSV Path:** `data\acquisition\fda_refusals_classified.csv`
- **Date Range (REFUSAL_DATE):** `2019-01-02` to `2026-08-26`

## 2. Counts and Percentages by FOOD_CLASS
| FOOD_CLASS | Record Count | Percentage |
|---|---|---|
| `NON_FOOD` | 102,535 | 61.64% |
| `HUMAN_FOOD` | 54,645 | 32.85% |
| `DIETARY_SUPPLEMENT` | 8,292 | 4.99% |
| `FOOD_ADDITIVE_OR_CONTACT` | 516 | 0.31% |
| `ANIMAL_FEED` | 347 | 0.21% |
| `UNCLASSIFIED_INVALID_CODE` | 1 | 0.00% |

- **Total Invalid `PRODUCT_CODE` Count:** 1

## 3. Counts and Percentages by INDUSTRY_CODE (Top 30)
| INDUSTRY_CODE | Record Count | Percentage | Primary Association |
|---|---|---|---|
| `98` | 28,679 | 17.24% | NON_FOOD |
| `66` | 10,450 | 6.28% | NON_FOOD |
| `54` | 8,292 | 4.99% | DIETARY_SUPPLEMENT |
| `16` | 7,674 | 4.61% | HUMAN_FOOD |
| `62` | 7,161 | 4.31% | NON_FOOD |
| `53` | 6,950 | 4.18% | NON_FOOD |
| `61` | 6,426 | 3.86% | NON_FOOD |
| `07` | 6,351 | 3.82% | HUMAN_FOOD |
| `80` | 5,928 | 3.56% | NON_FOOD |
| `86` | 5,409 | 3.25% | NON_FOOD |
| `21` | 4,693 | 2.82% | HUMAN_FOOD |
| `24` | 4,316 | 2.59% | HUMAN_FOOD |
| `79` | 3,851 | 2.32% | NON_FOOD |
| `03` | 3,611 | 2.17% | HUMAN_FOOD |
| `33` | 3,561 | 2.14% | HUMAN_FOOD |
| `60` | 3,352 | 2.02% | NON_FOOD |
| `28` | 3,337 | 2.01% | HUMAN_FOOD |
| `25` | 2,699 | 1.62% | HUMAN_FOOD |
| `83` | 2,485 | 1.49% | NON_FOOD |
| `64` | 2,449 | 1.47% | NON_FOOD |
| `76` | 2,315 | 1.39% | NON_FOOD |
| `65` | 2,291 | 1.38% | NON_FOOD |
| `23` | 2,070 | 1.24% | HUMAN_FOOD |
| `37` | 2,050 | 1.23% | HUMAN_FOOD |
| `56` | 1,996 | 1.20% | NON_FOOD |
| `20` | 1,918 | 1.15% | HUMAN_FOOD |
| `02` | 1,705 | 1.03% | HUMAN_FOOD |
| `29` | 1,684 | 1.01% | HUMAN_FOOD |
| `74` | 1,344 | 0.81% | NON_FOOD |
| `78` | 1,322 | 0.79% | NON_FOOD |

## 4. Raw File Immutability Confirmation
- **Confirmation:** All source files in `data/raw/` were confirmed unmodified via pre- and post-execution SHA-256 integrity verification.
