# Data Quality Report — Pakistan Crop Disease Knowledge Base

**Generated:** 2026-08-30 · **Version:** 1.0
**Source:** `crop_knowledge_data.xlsx` (sheet "Crop Knowledge", 49 rows, 12 crops) + 116 reference photos
**Outputs:** `crop_knowledge_enhanced.xlsx` (3 sheets), `crop_knowledge.json`, `image_mapping.csv`, `images/` (116 normalised photos)

---

## 1. Summary of Changes

| Aspect | Before | After |
|---|---|---|
| Columns / fields | 6 (Crop, Disease, Symptoms, Basic Advice, Source, URL) | 28 (IDs, bilingual names, type, causal agent, aliases, description, symptoms, causes, treatment, prevention — each in EN + UR — image mapping, source, confidence, notes) |
| Disease entries | 49 | 50 diseases + 12 "Healthy" entries = 62 (Onion Powdery Mildew added because 2 photos of it existed) |
| Urdu content | None | Every user-facing field fully translated into natural Urdu |
| Images | 116 files, inconsistent names/extensions | 116 files in `images/{plant}/{plant}_{disease}_{nn}.{ext}`, all mapped to IDs |
| IDs | None | Plants `PL001–PL012`, diseases `DS001–DS050`, healthy `DS051–DS062`, images `IMG001–IMG116` |

**Row-level corrections (all documented in the "Quality Log" sheet of the Excel):**

- **Mojibake fixed** — 7 rows contained a corrupted character (likely an en-dash), e.g. *"No cure once infected [�] remove..."*. All rewritten cleanly.
- **Source-name typos fixed** — "planttix" → Plantix; "UthaStateUniversity" / "UtahState-University" → Utah State University; "SASKATCHEWAN Pulse Growers" → Saskatchewan Pulse Growers; "Wordpress" → La Riceman (WordPress blog).
- **Disease-name spelling fixed** — "Alternaria leaf Spot" → "Alternaria Leaf Spot"; "Styler End Rot" → "Stylar End Rot".
- **Mango "Die Back" renamed to "Sooty Mold"** — the original row's symptoms (black soot-like coating growing on insect honeydew) describe **sooty mold**, not dieback (which is progressive twig death from the tip inward). The user's own photos are named `Mango_Sooty_Mold`, confirming the intent. "Die back" kept as an alias; flagged for manual confirmation.
- **Treatment vs. prevention split** — the single "Basic Advice" column mixed both; now separated into `treatment` (act now) and `prevention` (long-term), each in EN + UR.
- **Cotton source URLs** — 3 rows had URLs ending in a placeholder note ("TBD - no confirmed dataset found..."). Trimmed to the valid Cotton Incorporated URL; the caveat is preserved in `confidence_notes`.
- **No content was discarded** — original symptoms/advice judged correct were preserved (often re-worded for clarity), not replaced.

## 2. Improvements

- **Descriptions added** for all 50 diseases (none existed): 2–3 plain-language sentences on what the disease is and how serious it typically is for a Pakistani farmer.
- **Causes/causal agents added** for all 50 diseases (none existed): the pathogen in Latin plus a plain-language explanation of the conditions that favour it.
- **Prevention lists added** for all 50 diseases (extracted from the mixed advice and standard agronomy).
- **Urdu translations written as meaning-based, natural Pakistani Urdu** — not word-for-word. Scientific pathogen names (e.g. *Alternaria solani*) stay in Latin script inside Urdu text, which is how Pakistani agricultural literature does it. Chemical advice in Urdu always ends with the label/local-guidance caution.
- **12 "Healthy" entries added** so the website can respond sensibly when the classifier predicts "healthy" instead of returning an empty result.
- **Image filenames normalised** — spaces (`Cotton_Ascochyta Blight_01.jpg`), parentheses (`Chilli_Anthracnose (Fruit Rot)_01.webp`), mixed case (`Gray_leaf_spot`, `leaf_Smut`), the `Styler_End_Root` typo, and `.jfif`/`.JPG` extensions all converted to a consistent lowercase `plant_disease_nn` scheme (`.jfif`/`.JPG` → `.jpg`; `.webp`/`.png` kept — all browser-compatible).
- **Responsible-advice guardrail applied everywhere**: no invented pesticides or dosages; chemicals mentioned only generically (e.g. "copper-based fungicide", "mancozeb-based", "tricyclazole is commonly used for rice blast") and always paired with *"follow the product label and local agricultural guidance"* — in both languages. The JSON `meta.disclaimer` / `meta.disclaimer_ur` states that predictions are never 100% certain.

## 3. Missing Information

| Item | Status | Recommendation |
|---|---|---|
| Photo for **Onion Downy Mildew** | No reference photo in the collected set (disease itself kept from the original sheet) | Add 1–2 photos, e.g. from a university extension collection |
| Direct source URL for **Onion Downy Mildew** | Current URL is a search-results page, not an article | Replace with a direct extension page |
| **Cotton disease sources** | Original sheet itself noted "TBD - no confirmed dataset found" | Verify against CABI or Cotton Incorporated pages |
| Urdu content in **original sheet** | Entirely absent | Now supplied (this deliverable) — recommend review by a native-speaker editor |
| Yield-loss / severity ratings | Not in original data, not invented | Could be added later from CABI datasheets if wanted |

## 4. Items Needing Manual Verification

**Data entries (confidence ≠ high):**

| ID | Entry | Why | Confidence |
|---|---|---|---|
| DS045 | **Guava Fruit Scab** | Causal agent not confirmable from available sources; described as fungal | needs_verification |
| DS046 | **Guava Stylar End Rot** | Causal agent uncertain | needs_verification |
| DS033 | **Onion Powdery Mildew** | Newly added entry (photos existed but disease wasn't in the Excel); written from standard pathology knowledge | needs_verification |
| DS037 | **Mango "Sooty Mold"** (was "Die Back") | Renamed based on symptom analysis | needs_verification |
| DS019 | **Rice Leaf Smut** | Source is a personal WordPress blog (La Riceman) — informative but not authoritative | medium |
| DS028 | **Chili Anthracnose (Fruit Rot)** | Original sheet's URL was a Shutterstock image link, not the cited Frontiers article | medium |

**Images marked `needs_review` (5 of 116):**

| Image | Problem | Recommendation |
|---|---|---|
| `images/chili/chili_anthracnose_fruit_rot_01.webp` | Shows water-damaged leaves rather than fruit-rot symptoms, and carries a **Shutterstock watermark** | Replace with a royalty-free anthracnose fruit-rot photo |
| `images/onion/onion_basal_rot_01.jpg` | Photo shows **garlic**, not onion | Replace or relabel |
| `images/guava/guava_fruit_scab_01.webp` | Appears to be an anthracnose diagnostic collage (sunken lesions + *Colletotrichum* spores), not corky scab | Verify or replace |
| `images/wheat/wheat_powdery_mildew_01.jpg` | Wetter/standing-water setting atypical for wheat | Verify the crop shown |
| `images/citrus/citrus_greening_01.jpg` | Normal green fruit, no clear HLB symptoms (blotchy leaf mottle) | Verify or replace |

**Important caveat on image verification coverage:** only ~10% of photos (12 of 116) were visually spot-checked during this analysis. Most matched their labels well; the 5 problems above were found in that sample. **All 116 images should be reviewed before production use.**

## 5. Unclassifiable Images

**None.** All 116 photos were successfully mapped to a plant + disease (or healthy) class. The build script reported zero unmapped files. The closest cases were handled by explicit mapping rules:

- `Wheat_Brown_Rust_*` → leaf_rust (brown rust = leaf rust)
- `Wheat_Mildew_*` → powdery_mildew
- `Guava_Fungal_Rust_*` → rust
- `Guava_Styler_End_Root_*` → stylar_end_rot (typo corrected)
- `Citrus_Canker/Greening/Scab_*` → disambiguated from other spot diseases by folder context
- `Chilli_*` folder (spelling) → Chili plant

## 6. Diseases Needing Further Research

1. **Guava fruit scab vs. anthracnose** — available sources conflated the two; the causal organism for the scab entry needs confirmation from a plant pathology reference (CABI / academic paper).
2. **Guava stylar end rot** — causal agent uncertain in reachable sources.
3. **Onion powdery mildew** — new entry; confirm it is a distinct, regionally relevant onion disease in Pakistan (vs. confused with downy mildew).
4. **Mango sooty mold / dieback** — confirm the rename matches what the classifier will actually predict, and that the training photos indeed show sooty mold.
5. **Chili anthracnose** — replace the watermarked photo and re-link the correct Frontiers citation.
6. **Cotton diseases (3 rows)** — original author left source confirmation open ("TBD"); verify against an authoritative source.

## 7. Duplicates

- **No duplicate rows** existed in the original sheet (checked on Crop + Disease pairs).
- **Same-named diseases across crops are intentionally separate entries** (they are different host–pathogen combinations with different advice): Early Blight and Late Blight (Tomato & Potato), Powdery Mildew (Wheat, Chili, Onion, Mango), Anthracnose (Cotton, Mango, Guava), Ascochyta Blight (Cotton, Chickpea). Each has a unique `disease_id` and crop-specific content.
- **No duplicate image files**: all 116 paths are unique; each source file was copied exactly once.

## 8. Validation Results (automated)

`validate_outputs.py` — **all checks passed**:

- `crop_knowledge.json`: valid UTF-8 JSON, 12 plants, 62 disease entries (50 + 12 healthy), 116 images; all IDs unique; every bilingual field non-empty in both languages; EN/UR list lengths parallel; Urdu script present in every `ur` field; no mojibake; every image path exists on disk; image counts match `meta`.
- `image_mapping.csv`: 116 rows, UTF-8-SIG (opens correctly in Excel), IDs consistent with JSON.
- `crop_knowledge_enhanced.xlsx`: 3 sheets (Dataset 63×28, Image Mapping 117×11, Quality Log 22 documented issues), Urdu intact, no empty core fields.
- `images/`: 116 files, 12 plant folders, all filenames match the `plant_disease_nn.ext` scheme, no `.jfif`/`.jpeg`/`.JPG` extensions remain.

**Confidence distribution across 62 entries:** high 56 · medium 2 · needs_verification 4.
