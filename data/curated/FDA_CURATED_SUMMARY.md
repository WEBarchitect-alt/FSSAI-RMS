# SENTRA-FS Curated FDA Food Refusals Dataset Summary

## 1. Executive Validation & Integrity Audit
- **Input In-Scope Rows:** 62,937
- **Curated Rows Produced:** 62,937
- **Record Retention:** **100.0% (Zero Record Loss)**
- **Output CSV File:** `data\curated\fda_food_refusals_curated.csv`
- **Output File Size:** 17,806,828 bytes
- **Output SHA-256:** `035293bc9602a62e00cf67e1d95975e7174144c334c3e409f556490b12493c36`

## 2. Data Health & Traceability Checks
| Check Metric | Result | Status |
|---|---|---|
| Missing Dates | 0 | PASS |
| Missing Product Codes | 0 | PASS |
| Missing Country Codes | 0 | PASS |
| Duplicate Composite `REFUSAL_ID`s | 22,305 | NOTE: Preserved (Multi-line consignments) |
| Primary Charge Mapping Coverage | 0 / 62,937 (0.00%) | CHECK |
| Unmapped Charge Tokens Encountered | 0 | `[]` |

## 3. Defect Standard Linkage Audit (`DEFECT_STANDARD_STATUS`)
| Status Category | Count | Percentage | Description |
|---|---|---|---|
| `NOT_APPLICABLE` | 62,937 | 100.00% | Non-filth charge (Labeling, Pathogen, Additive, etc.) |

## 4. Statutory Violation Categories
| Primary Charge Category | Record Count | Percentage |
|---|---|---|
| `OTHER_REGULATORY_VIOLATION` | 62,937 | 100.00% |

## 5. First 3 Curated Records (Sample)
```json
[
  {
    "REFUSAL_ID": "300-2485535-5_6295KestrelRd_29YHI99_2021-12-22",
    "ENTRY_NUM": "300-2485535-5",
    "LINE_NUM": "6295 Kestrel Rd",
    "REFUSAL_DATE": "2021-12-22",
    "PRODUCT_CODE": "29YHI99",
    "INDUSTRY_CODE": "29",
    "FOOD_CLASS": "HUMAN_FOOD",
    "PRODUCT_DESC": "SOFT DRINKS AND WATERS NOT MENTIONED ELSEWHERE, N.E.C.",
    "COUNTRY_CODE": "CA",
    "COUNTRY_NAME": "",
    "MANUFACTURER_NAME": "KFI Inc.",
    "MANUFACTURER_CITY": "Mississauga",
    "PORT_OF_ENTRY": "",
    "PRIMARY_CHARGE_CODE": "83",
    "ALL_CHARGE_CODES": "83",
    "RAW_CHARGES": "83",
    "PRIMARY_ACT_SECTION": "",
    "PRIMARY_CHARGE_STATEMENT": "",
    "ALL_ACT_SECTIONS": "",
    "ALL_CHARGE_STATEMENTS": "",
    "CHARGE_CATEGORY": "OTHER_REGULATORY_VIOLATION",
    "DEFECT_STANDARD_STATUS": "NOT_APPLICABLE",
    "POTENTIAL_DEFECT_COMMODITIES": ""
  },
  {
    "REFUSAL_ID": "300-2522558-3_Rn4-Amparihingidro-Antanimalandy_24AGT50_2022-03-31",
    "ENTRY_NUM": "300-2522558-3",
    "LINE_NUM": "Rn 4 - Amparihingidro - Antanimalandy",
    "REFUSAL_DATE": "2022-03-31",
    "PRODUCT_CODE": "24AGT50",
    "INDUSTRY_CODE": "24",
    "FOOD_CLASS": "HUMAN_FOOD",
    "PRODUCT_DESC": "BLACKEYE PEAS",
    "COUNTRY_CODE": "MG",
    "COUNTRY_NAME": "",
    "MANUFACTURER_NAME": "Dada Vision SARLU",
    "MANUFACTURER_CITY": "Majunga, Boeny",
    "PORT_OF_ENTRY": "",
    "PRIMARY_CHARGE_CODE": "241",
    "ALL_CHARGE_CODES": "241",
    "RAW_CHARGES": "241",
    "PRIMARY_ACT_SECTION": "",
    "PRIMARY_CHARGE_STATEMENT": "",
    "ALL_ACT_SECTIONS": "",
    "ALL_CHARGE_STATEMENTS": "",
    "CHARGE_CATEGORY": "OTHER_REGULATORY_VIOLATION",
    "DEFECT_STANDARD_STATUS": "NOT_APPLICABLE",
    "POTENTIAL_DEFECT_COMMODITIES": ""
  },
  {
    "REFUSAL_ID": "300-4257156-4_VinaElCarmenLote2A_20AGD13_2023-05-02",
    "ENTRY_NUM": "300-4257156-4",
    "LINE_NUM": "Vina El Carmen Lote 2 A",
    "REFUSAL_DATE": "2023-05-02",
    "PRODUCT_CODE": "20AGD13",
    "INDUSTRY_CODE": "20",
    "FOOD_CLASS": "HUMAN_FOOD",
    "PRODUCT_DESC": "RASPBERRIES, RED  (BERRY)",
    "COUNTRY_CODE": "CL",
    "COUNTRY_NAME": "",
    "MANUFACTURER_NAME": "Montes de Molina SPA",
    "MANUFACTURER_CITY": "Molina",
    "PORT_OF_ENTRY": "",
    "PRIMARY_CHARGE_CODE": "241",
    "ALL_CHARGE_CODES": "241",
    "RAW_CHARGES": "241",
    "PRIMARY_ACT_SECTION": "",
    "PRIMARY_CHARGE_STATEMENT": "",
    "ALL_ACT_SECTIONS": "",
    "ALL_CHARGE_STATEMENTS": "",
    "CHARGE_CATEGORY": "OTHER_REGULATORY_VIOLATION",
    "DEFECT_STANDARD_STATUS": "NOT_APPLICABLE",
    "POTENTIAL_DEFECT_COMMODITIES": ""
  }
]
```
