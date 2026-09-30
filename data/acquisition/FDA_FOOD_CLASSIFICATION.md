# FDA Product Code Structure & Food Classification Methodology

## 1. Official Sources & Regulatory Authority
This classification is based directly on official US Food and Drug Administration (FDA) regulatory specifications:
- **FDA Product Code Builder Tutorial & Coding Guidelines:** Office of Regulatory Affairs (ORA), FDA.
- **FDA Regulatory Procedures Manual (RPM):** Chapter 9 (Import Operations and Actions), Section 9-2.
- **FDA Compliance Program Guidance Manual (CPGM):** Program 7303.844 (Imported Foods - General).
- **21 CFR Chapter I:** Subchapter B (Food for Human Consumption) and Subchapter E (Animal Drugs, Feeds, and Related Products).

---

## 2. FDA Product Code Structure (7 Characters)
The FDA 7-character alphanumeric Product Code is structured into five distinct hierarchical positions:

$$\text{Format: } \mathbf{II}\text{ - }\mathbf{C}\text{ - }\mathbf{S}\text{ - }\mathbf{P}\text{ - }\mathbf{U}$$

| Position | Length | Element Name | Description | Example (`21CCT03`) |
|---|---|---|---|---|
| **1–2** | 2 Digits | **Industry Code** | Broadest regulatory category / center jurisdiction. | `21` (Fruit / Fruit Products) |
| **3** | 1 Letter | **Class** | Subcategory or generic food group within the industry. | `C` (Berries) |
| **4** | 1 Letter | **Subclass** | Physical form, storage condition, or state (e.g., fresh, dried, frozen). | `C` (Frozen) |
| **5** | 1 Letter | **Process Indicator (PIC)** | Thermal process, packaging condition, or processing stage. | `T` (Commercially Sterile / Canned) |
| **6–7** | 2 Characters | **Product (Group)** | Specific individual commodity or end-use identity. | `03` (Strawberries) |

---

## 3. Industry Code Explanation (Positions 1–2)
The first two numeric positions define the FDA Product Industry. The FDA assigns code ranges to specific regulatory centers:
- **CFSAN / Human Food:** Codes `02` through `41`, `52`, and `54`.
- **CVM / Animal Feed & Pet Food:** Code `71` (Animal Drugs/Feeds) and Code `72` (Feeds/Feed Ingredients).
- **Cosmetics (CFSAN/OCAC):** Code `53` (e.g., `53JK01` = soaps, bath preparations).
- **Drugs (CDER):** Codes `56`, `60`–`68`.
- **Medical Devices (CDRH):** Codes `73`–`92`.
- **Tobacco (CTP):** Code `98`.
- **Biologics (CBER):** Code `57`–`59`.

---

## 4. Official Food Classification (CFSAN Human Food & CVM Feed)

### A. Primary Human Foods (CFSAN)
| Industry Code | Official FDA Industry Description | SENTRA-FS Scope |
|---|---|---|
| **02** | Whole Grain (Corn, Wheat, Rye, Oats, Barley, Sorghum) | Human Food |
| **03** | Bakery Products / Dough Mixes / Icings | Human Food |
| **04** | Macaroni and Noodle Products | Human Food |
| **05** | Cereal Preparations / Breakfast Foods | Human Food |
| **07** | Snack Food Items (Pretzels, Chips, Specialty Snacks) | Human Food |
| **09** | Milk / Butter / Dried Milk Products | Human Food |
| **12** | Cheese and Cheese Products | Human Food |
| **13** | Ice Cream and Related Frozen Products | Human Food |
| **14** | Imitation Milk Products | Human Food |
| **15** | Egg and Egg Products | Human Food |
| **16** | Fish and Seafood Products | Human Food |
| **17** | Meat and Poultry Products (FDA Jurisdiction: Game, Exotic, Non-amenable) | Human Food |
| **20** | Fruit and Fruit Products (Citrus) | Human Food |
| **21** | Fruit and Fruit Products (Non-Citrus / Berries / Tropical) | Human Food |
| **22** | Fruit and Fruit Products (Dried, Candied, Jams, Jellies) | Human Food |
| **23** | Nuts and Edible Seeds | Human Food |
| **24** | Vegetables and Vegetable Products (Raw / Fresh / Frozen) | Human Food |
| **25** | Vegetables and Vegetable Products (Canned / Processed / Pickled) | Human Food |
| **26** | Vegetable Oils (Crude, Refined, Shortenings) | Human Food |
| **27** | Dressings, Condiments, Sauces | Human Food |
| **28** | Spices, Flavors, and Seasonings | Human Food |
| **29** | Soft Drinks and Water | Human Food |
| **30** | Beverage Bases and Syrups | Human Food |
| **31** | Coffee and Tea | Human Food |
| **32** | Alcoholic Beverages (Malt, Wine, Spirits under FDA jurisdiction) | Human Food |
| **33** | Candy and Confectionery Products (With and Without Cocoa) | Human Food |
| **34** | Chocolate and Cocoa Products | Human Food |
| **35** | Gelatin, Rennet, Puddings, Pie Fillings | Human Food |
| **36** | Food Sweeteners (Sugar, Molasses, Honey, Syrups) | Human Food |
| **37** | Multiple Foods (Prepared Entrees, Frozen Dinners) | Human Food |
| **38** | Soups | Human Food |
| **39** | Baby Foods / Infant Formulas / Feeding Preparations | Human Food |
| **40** | Dietary Conventional Foods / Meal Replacements | Human Food |
| **41** | Dietary Specialities / Medical Foods | Human Food |

### B. Dietary Supplements & Food-Contact / Processing Commodities
| Industry Code | Official FDA Industry Description | Classification Analysis |
|---|---|---|
| **54** | **Dietary Supplements, Herbal Formulations, Botanicals** | Regulated as a category of food under DSHEA (21 U.S.C. 321(ff)). Must be classified as Food/Dietary Supplement in SENTRA-FS, flagged distinctly. |
| **52** | **Miscellaneous Food Related Items / Food Additives / Colors** | Contains direct food additives, direct food colors, processing enzymes, and food packaging materials. |

### C. Animal Feed & Pet Food (CVM)
| Industry Code | Official FDA Industry Description | Classification Analysis |
|---|---|---|
| **71** | Animal Drugs and Feeds | Mixed: Contains medicated feeds (drugs) and feed premixes. |
| **72** | Animal Feeds, Pet Foods, Forage, Grain By-products | Dedicated animal feed and commercial pet food. |

---

## 5. Non-Food Exclusions (Strictly Filtered Out)
The following Industry Codes represent non-food commodities and must be strictly excluded from the food-only corpus:

| Industry Code | FDA Description | Exclusion Ground |
|---|---|---|
| **53** | Cosmetics, Toiletries, Soaps, Fragrances | Regulated under FD&C Act Ch. VI (Cosmetics) |
| **56** | Antibiotics and Antibacterial Drugs | CDER Human Drugs |
| **60–68** | Human Pharmaceuticals / Biologics / Rx & OTC Drugs | CDER Human Drugs |
| **73–92** | Medical Devices / Diagnostic Products / Radiation Emitters | CDRH Medical Devices |
| **94** | Toxicological Devices / Laboratory Equipment | Laboratory Hardware / Non-Commodity |
| **95** | Electronic Products Subject to Radiation Control | Non-Food Consumer Electronics |
| **98** | Tobacco Products and Electronic Nicotine Delivery Systems | CTP Tobacco Regulation |

---

## 6. Critical Edge Cases & Filtering Pitfalls

1. **Industry Code `53` vs `54` Confusion:**
   - Code `53` includes cosmetic face creams, shampoos, soaps, and perfumes (Non-Food).
   - Code `54` includes vitamins, botanical capsules, and herbal extracts (Food under DSHEA).
   - *Rule:* Retain `54`, strictly drop `53`.

2. **Industry Code `52` (Food Additives vs Food Contact Surfaces):**
   - Code `52` contains chemical additives intended for ingestion (preservatives, acidulants, leavening agents) alongside sanitizers, lubricants, and empty food containers/wrappers.
   - *Rule:* Retain Code `52` in the initial ingestion, but add a downstream attribute (`FOOD_CONTACT_ONLY` vs `DIRECT_ADDITIVE`) if packaging materials are analyzed.

3. **Industry Code `71` (Animal Drugs and Feeds):**
   - Code `71` contains medicated feeds and veterinary pharmaceuticals. Mixing veterinary injectable antibiotics with animal food introduces bias.
   - *Rule:* Exclude Code `71` from primary food intake; retain Code `72` only if animal feed/pet food is within the explicit scope. For human food purity, restrict to Codes `02`–`41`, `52`, and `54`.

4. **USDA Meat & Poultry vs FDA Non-Amenable Meats (Code `17`):**
   - Cattle, swine, sheep, goats, and domestic poultry fall under USDA FSIS jurisdiction (not reported in FDA OASIS).
   - Code `17` in FDA data represents exotic meats, game animals (venison, bison, rabbit), and non-amenable species.
   - *Rule:* Retain Code `17` as valid FDA-regulated food.

5. **Dietary Supplements (Code `54`) Distorted Risk Signals:**
   - Dietary supplements frequently trigger refusals for labeling/structure-function claims (unapproved new drug charges) rather than chemical/microbiological contamination.
   - *Rule:* Must retain Code `54` as legally defined food, but tag records with category `DIETARY_SUPPLEMENT` so parameter and hazard aggregations can be analyzed independently of agricultural commodities.

---

## 7. Recommended Classification Rule for SENTRA-FS

To guarantee data purity and exclude industrial chemicals, cosmetics, devices, and pharmaceuticals:

$$\text{INDUSTRY\_CODE} = \text{SUBSTRING}(\text{PRODUCT\_CODE}, 1, 2)$$

### Classification Mapping:
1. **`HUMAN_FOOD` (Primary Target):**
   $$\text{INDUSTRY\_CODE} \in \{02, 03, 04, 05, 07, 09, 12, 13, 14, 15, 16, 17, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41\}$$

2. **`DIETARY_SUPPLEMENT` (Food Class under DSHEA):**
   $$\text{INDUSTRY\_CODE} \in \{54\}$$

3. **`FOOD_ADDITIVE_OR_CONTACT` (Food Associated):**
   $$\text{INDUSTRY\_CODE} \in \{52\}$$

4. **`ANIMAL_FEED` (Optional / Contextual):**
   $$\text{INDUSTRY\_CODE} \in \{72\}$$

5. **`NON_FOOD` (Filtered Out / Discarded):**
   $$\text{All other codes, including } \{53, 56, 60\dots68, 71, 73\dots92, 94, 95, 98\}$$

---

## 8. Confidence and Limitations
- **Confidence:** High. The 2-digit Industry Code is the universal top-level partition utilized internally by FDA OASIS and FDA Field Operations.
- **Limitations:**
  - A malformed or truncated `PRODUCT_CODE` (less than 2 characters or non-numeric first two characters) cannot be classified via Industry Code alone and must be logged as `UNCLASSIFIED_INVALID_CODE`.
  - Distinguishing direct food additives from non-edible food contact plastics within Industry `52` requires evaluating character position 3 (Class).