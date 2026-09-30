# SENTRA-FS Local FDA Data Profile Report

## 1. File Summary
| File Name | File Size (Bytes) | Row Count | Encoding | Delimiter |
|---|---|---|---|---|
| `REFUSAL_ENTRY_2019_2023.csv` | 16,689,107 | 76,819 | utf-8 | `','` |
| `REFUSAL_ENTRY_2024-Aug2026.csv` | 18,655,445 | 89,517 | utf-8 | `','` |
| `ACT_SECTION_CHARGES.csv` | 100,514 | 322 | N/A | N/A |

## 2. Schema Comparison (REFUSAL_ENTRY files)
- **Are schemas identical?:** `YES`

## 3. Detailed Profile: `REFUSAL_ENTRY_2019_2023.csv`
- **Total Rows:** 76,819
- **Duplicate Full Rows:** 0

### Columns & Missing Value Analysis
| Column Name | Inferred Type | Missing Count | Missing % | Unique Values |
|---|---|---|---|---|
| `MFG_FIRM_FEI_NUM` | string/text | 0 | 0.0% | 24,485 |
| `LGL_NAME` | string/text | 1 | 0.0% | 23,502 |
| `LINE1_ADRS` | string/text | 1 | 0.0% | 23,472 |
| `LINE2_ADRS` | string/text | 43,737 | 56.94% | 8,201 |
| `CITY_NAME` | string/text | 0 | 0.0% | 9,001 |
| `PROVINCE_STATE` | string/text | 22,162 | 28.85% | 2,138 |
| `ISO_CNTRY_CODE` | string/text | 0 | 0.0% | 168 |
| `PRODUCT_CODE` | string/text | 1 | 0.0% | 13,557 |
| `REFUSAL_DATE` | string/text | 0 | 0.0% | 1,412 |
| `DISTRICT` | string/text | 0 | 0.0% | 5 |
| `ENTRY_NUM` | string/text | 0 | 0.0% | 41,102 |
| `RFRNC_DOC_ID` | string/text | 0 | 0.0% | 382 |
| `LINE_NUM` | string/text | 0 | 0.0% | 145 |
| `LINE_SFX_ID` | string/text | 72,616 | 94.53% | 80 |
| `FDA_SAMPLE_ANALYSIS` | string/text | 0 | 0.0% | 2 |
| `PRIVATE_LAB_ANALYSIS` | string/text | 0 | 0.0% | 2 |
| `REFUSAL_CHARGES` | string/text | 0 | 0.0% | 3,059 |
| `PRDCT_CODE_DESC_TEXT` | string/text | 1 | 0.0% | 5,172 |

### Date Fields & Ranges
- `REFUSAL_DATE`: Min `2019-01-02` to Max `2023-12-30`

### Sample Records (First 3)
```json
[
  {
    "MFG_FIRM_FEI_NUM": "2000047005",
    "LGL_NAME": "KFI Inc.",
    "LINE1_ADRS": "6295 Kestrel Rd",
    "LINE2_ADRS": NaN,
    "CITY_NAME": "Mississauga",
    "PROVINCE_STATE": "Ontario",
    "ISO_CNTRY_CODE": "CA",
    "PRODUCT_CODE": "29YHI99",
    "REFUSAL_DATE": "22-Dec-21",
    "DISTRICT": "DNBI",
    "ENTRY_NUM": "300-2485535-5",
    "RFRNC_DOC_ID": "11",
    "LINE_NUM": "1",
    "LINE_SFX_ID": NaN,
    "FDA_SAMPLE_ANALYSIS": "No",
    "PRIVATE_LAB_ANALYSIS": "No",
    "REFUSAL_CHARGES": "83",
    "PRDCT_CODE_DESC_TEXT": "SOFT DRINKS AND WATERS NOT MENTIONED ELSEWHERE, N.E.C."
  },
  {
    "MFG_FIRM_FEI_NUM": "3015442400",
    "LGL_NAME": "Dada Vision SARLU",
    "LINE1_ADRS": "Rn 4 - Amparihingidro - Antanimalandy",
    "LINE2_ADRS": NaN,
    "CITY_NAME": "Majunga, Boeny",
    "PROVINCE_STATE": "MG-NOTA",
    "ISO_CNTRY_CODE": "MG",
    "PRODUCT_CODE": "24AGT50",
    "REFUSAL_DATE": "31-Mar-22",
    "DISTRICT": "DNBI",
    "ENTRY_NUM": "300-2522558-3",
    "RFRNC_DOC_ID": "171",
    "LINE_NUM": "2",
    "LINE_SFX_ID": NaN,
    "FDA_SAMPLE_ANALYSIS": "Yes",
    "PRIVATE_LAB_ANALYSIS": "No",
    "REFUSAL_CHARGES": "241",
    "PRDCT_CODE_DESC_TEXT": "BLACKEYE PEAS"
  },
  {
    "MFG_FIRM_FEI_NUM": "3010614994",
    "LGL_NAME": "Montes de Molina SPA",
    "LINE1_ADRS": "Vina El Carmen Lote 2 A",
    "LINE2_ADRS": NaN,
    "CITY_NAME": "Molina",
    "PROVINCE_STATE": "Septima Region del Maule",
    "ISO_CNTRY_CODE": "CL",
    "PRODUCT_CODE": "20AGD13",
    "REFUSAL_DATE": "02-May-23",
    "DISTRICT": "DNBI",
    "ENTRY_NUM": "300-4257156-4",
    "RFRNC_DOC_ID": "11",
    "LINE_NUM": "1",
    "LINE_SFX_ID": NaN,
    "FDA_SAMPLE_ANALYSIS": "Yes",
    "PRIVATE_LAB_ANALYSIS": "No",
    "REFUSAL_CHARGES": "241",
    "PRDCT_CODE_DESC_TEXT": "RASPBERRIES, RED  (BERRY)"
  }
]
```

## 3. Detailed Profile: `REFUSAL_ENTRY_2024-Aug2026.csv`
- **Total Rows:** 89,517
- **Duplicate Full Rows:** 0

### Columns & Missing Value Analysis
| Column Name | Inferred Type | Missing Count | Missing % | Unique Values |
|---|---|---|---|---|
| `MFG_FIRM_FEI_NUM` | string/text | 0 | 0.0% | 18,186 |
| `LGL_NAME` | string/text | 0 | 0.0% | 17,134 |
| `LINE1_ADRS` | string/text | 2 | 0.0% | 17,569 |
| `LINE2_ADRS` | string/text | 57,576 | 64.32% | 5,621 |
| `CITY_NAME` | string/text | 0 | 0.0% | 7,064 |
| `PROVINCE_STATE` | string/text | 23,530 | 26.29% | 1,804 |
| `ISO_CNTRY_CODE` | string/text | 0 | 0.0% | 151 |
| `PRODUCT_CODE` | string/text | 0 | 0.0% | 11,921 |
| `REFUSAL_DATE` | string/text | 0 | 0.0% | 772 |
| `DISTRICT` | string/text | 0 | 0.0% | 5 |
| `ENTRY_NUM` | string/text | 0 | 0.0% | 36,226 |
| `RFRNC_DOC_ID` | string/text | 0 | 0.0% | 1,489 |
| `LINE_NUM` | string/text | 0 | 0.0% | 111 |
| `LINE_SFX_ID` | string/text | 85,252 | 95.24% | 62 |
| `FDA_SAMPLE_ANALYSIS` | string/text | 0 | 0.0% | 2 |
| `PRIVATE_LAB_ANALYSIS` | string/text | 0 | 0.0% | 2 |
| `REFUSAL_CHARGES` | string/text | 0 | 0.0% | 2,489 |
| `PRDCT_CODE_DESC_TEXT` | string/text | 0 | 0.0% | 4,305 |

### Date Fields & Ranges
- `REFUSAL_DATE`: Min `2024-01-02` to Max `2026-08-26`

### Sample Records (First 3)
```json
[
  {
    "MFG_FIRM_FEI_NUM": "3015259023",
    "LGL_NAME": "GANDHI SPICES PVT LTD",
    "LINE1_ADRS": "Near Honest Hotel Provi",
    "LINE2_ADRS": NaN,
    "CITY_NAME": "Rajkot",
    "PROVINCE_STATE": NaN,
    "ISO_CNTRY_CODE": "IN",
    "PRODUCT_CODE": "07YGT99",
    "REFUSAL_DATE": "15-Jan-25",
    "DISTRICT": "DWCI",
    "ENTRY_NUM": "K80-2162679-2",
    "RFRNC_DOC_ID": "231",
    "LINE_NUM": "5",
    "LINE_SFX_ID": NaN,
    "FDA_SAMPLE_ANALYSIS": "Yes",
    "PRIVATE_LAB_ANALYSIS": "No",
    "REFUSAL_CHARGES": "11, 274",
    "PRDCT_CODE_DESC_TEXT": "SNACK FOODS NOT ELSEWHERE MENTIONED, N.E.C."
  },
  {
    "MFG_FIRM_FEI_NUM": "3021885604",
    "LGL_NAME": "Abozar Barik Zai Trading",
    "LINE1_ADRS": "Temor Shahi Ghafoori Market",
    "LINE2_ADRS": NaN,
    "CITY_NAME": "Kabul",
    "PROVINCE_STATE": "Kabul",
    "ISO_CNTRY_CODE": "AF",
    "PRODUCT_CODE": "33GGT99",
    "REFUSAL_DATE": "11-Jan-24",
    "DISTRICT": "DWCI",
    "ENTRY_NUM": "K80-9034518-3",
    "RFRNC_DOC_ID": "11",
    "LINE_NUM": "1",
    "LINE_SFX_ID": "A",
    "FDA_SAMPLE_ANALYSIS": "No",
    "PRIVATE_LAB_ANALYSIS": "No",
    "REFUSAL_CHARGES": "253, 321, 324, 473, 482",
    "PRDCT_CODE_DESC_TEXT": "SOFT CANDY WITH NUTS OR NUT PRODUCTS, N.E.C.  (WITHOUT CHOCOLATE)"
  },
  {
    "MFG_FIRM_FEI_NUM": "3023144653",
    "LGL_NAME": "EL Paradis Cosmetic",
    "LINE1_ADRS": "29 Industrie Cosmetique, Autoroute Du Nord, Km",
    "LINE2_ADRS": NaN,
    "CITY_NAME": "Abidjan",
    "PROVINCE_STATE": NaN,
    "ISO_CNTRY_CODE": "CI",
    "PRODUCT_CODE": "53JK01",
    "REFUSAL_DATE": "09-Dec-24",
    "DISTRICT": "DNEI",
    "ENTRY_NUM": "KL1-0283935-6",
    "RFRNC_DOC_ID": "11",
    "LINE_NUM": "1",
    "LINE_SFX_ID": "A",
    "FDA_SAMPLE_ANALYSIS": "No",
    "PRIVATE_LAB_ANALYSIS": "No",
    "REFUSAL_CHARGES": "75",
    "PRDCT_CODE_DESC_TEXT": "BATH SOAPS AND DETERGENTS (NOT ANTIPERSPIRANT) (PERSONAL CLEANLINESS)"
  }
]
```

## 4. ACT_SECTION_CHARGES Profile
- **Row Count:** 322
- **Columns (4):** `['ASC_ID', 'CHRG_CODE', 'CHRG_STMNT_TEXT', 'SCTN_NAME']`

## 5. Important Data-Quality Observations
- In `REFUSAL_ENTRY_2019_2023.csv`, the following fields have >30% missing values: `['LINE2_ADRS', 'LINE_SFX_ID']`
- In `REFUSAL_ENTRY_2024-Aug2026.csv`, the following fields have >30% missing values: `['LINE2_ADRS', 'LINE_SFX_ID']`
- Delimiter and character encodings handled cleanly across read operations.
- Datasets maintain historical partition integrity without unhandled parse corruptions.