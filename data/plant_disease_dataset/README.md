# Pakistan Crop Disease Knowledge Base — Dataset v1.0

Bilingual (English + اردو) plant-disease knowledge dataset for a plant-disease diagnosis website.
Covers **12 crops · 50 diseases · 12 "healthy" entries · 116 reference photos**, all usable for both
training-label review and result-page display.

## Files

| File | Purpose |
|---|---|
| `crop_knowledge.json` | Main dataset for the website (UTF-8, `JSON.parse` / `json.load` ready) |
| `crop_knowledge_enhanced.xlsx` | Human-editable master: **Dataset** (28 cols), **Image Mapping**, **Quality Log** (22 documented issues) |
| `image_mapping.csv` | Flat table: every original photo → image_id → plant → disease (UTF-8-SIG for Excel) |
| `images/{plant}/{plant}_{disease}_{nn}.{ext}` | 116 normalised photos; paths in the JSON are relative to this folder |
| `DATA_QUALITY_REPORT.md` | Changes, fixes, items needing manual verification, image review notes |

## JSON Schema

```jsonc
{
  "meta": {
    "dataset_name", "version", "generated_on",
    "languages": ["en", "ur"], "encoding": "UTF-8",
    "plant_count": 12, "disease_count": 50, "healthy_entries": 12, "image_count": 116,
    "disclaimer": "…", "disclaimer_ur": "…"          // show this on the site (see below)
  },
  "plants": [
    {
      "plant_id": "PL001",                            // stable ID (PL001–PL012)
      "name":       { "en": "Tomato", "ur": "ٹماٹر" },
      "scientific_name": "Solanum lycopersicum",
      "category":   { "en": "vegetable", "ur": "سبزی" },
      "aliases": ["tomato"],                          // extra search terms
      "diseases": [
        {
          "disease_id": "DS001",                      // stable ID (DS001–DS062)
          "name":       { "en": "…", "ur": "…" },
          "aliases": ["target spot"],                 // alternate names for search
          "type": "fungal",                           // fungal|bacterial|viral|pest|algal|physiological|healthy
          "causal_agent": "Alternaria solani",        // null for healthy entries
          "description":  { "en": "…", "ur": "…" },   // 2–3 sentence plain-language overview
          "symptoms":     { "en": ["…"], "ur": ["…"] },   // parallel arrays (same length, same order)
          "causes":       { "en": "…", "ur": "…" },
          "treatment":    { "en": ["…"], "ur": ["…"] },   // "what to do now"
          "prevention":   { "en": ["…"], "ur": ["…"] },   // "how to avoid next season"
          "images": [
            {
              "id": "IMG001",
              "path": "images/tomato/tomato_early_blight_01.jpg",  // relative to dataset root
              "label": "Tomato leaves showing dark, target-patterned early blight spots",
              "status": "available",                  // "needs_review" = don't use as a hero image
              "review_note": ""                      // present only when status = needs_review
            }
          ],
          "source": { "name": "…", "url": "…" },
          "confidence": "high",                       // high | medium | needs_verification (data quality)
          "confidence_notes": "…"                     // why; what was changed/flagged
        }
      ]
    }
  ]
}
```

**Conventions**

- Every user-facing text is a `{ "en": …, "ur": … }` object — render one side based on the language toggle.
- `symptoms` / `treatment` / `prevention` are **arrays of short strings** (ready-made bullet points); EN and UR arrays are parallel (index i in EN = index i in UR).
- `confidence` describes **dataset quality** (how well-sourced the entry is), *not* the model's prediction score. Don't show it as the diagnosis certainty.
- IDs are stable: use them as classifier class labels and as DB keys, so content edits never break links.

## Loading

```js
// JS — copy the whole folder into public/, then:
const kb = await fetch("crop_knowledge.json").then(r => r.json());
const index = {}; // class-name -> entry
for (const p of kb.plants)
  for (const d of p.diseases)
    index[`${p.name.en} - ${d.name.en}`] = { plant: p, disease: d };
```

```python
# Python
import json
kb = json.load(open("crop_knowledge.json", encoding="utf-8"))
```

## Website Display Suggestions

Suggested result page, matching the flow you described:

```
┌──────────────────────────────────────────────────────┐
│  🌿 Detection Result                     [EN | اردو] │
│                                                      │
│  [photo thumbnail]  Plant:    Tomato / ٹماٹر          │
│                     Disease:  Early Blight            │
│                                  ابتدائی جھلساؤ       │
│                     Model confidence: 87%   ⓘ        │
├──────────────────────────────────────────────────────┤
│  Symptoms / علامات                                    │
│  • Dark brown spots with concentric rings…           │
│  • گہرے بھورے دھبے جن میں گول حلقے…                  │
├──────────────────────────────────────────────────────┤
│  What You Should Do / آپ کو کیا کرنا چاہیے           │
│  • Pick off and destroy affected leaves…             │
│  • متاثرہ پتے توڑ کر تلف کر دیں…                     │
├──────────────────────────────────────────────────────┤
│  How to Prevent It / مستقبل میں بچاؤ                 │
│  • Rotate with non-solanaceous crops…                │
│  • ٹماٹر خاندان کی دوسری فصلوں سے برساتی تبادلہ…     │
├──────────────────────────────────────────────────────┤
│  ⚠ AI predictions are not 100% certain. Confirm      │
│    with your local agriculture extension office      │
│    before spraying. Follow product labels.           │
└──────────────────────────────────────────────────────┘
```

1. **Language toggle, not two pages.** Since every field is `{en, ur}`, one component reads `field[lang]`.
   On first load, default to Urdu if the browser/OS locale is `ur-*` or `pa-*`, else English.
   Render both scripts with `dir="rtl"` on Urdu containers; keep Latin pathogen names LTR inside Urdu text.
2. **Show the model's own confidence %** (from your classifier) prominently, but phrase it honestly:
   *"87% likely Early Blight — verify with a local expert before treatment."* Never show 100%.
3. **Map classifier output → entry** via `plant_id` + `disease_id` (or the `index` map above).
   When the model predicts "healthy", use the healthy entry (`type: "healthy"`) — it has a friendly
   bilingual message and a weekly-inspection tip instead of an empty page.
4. **Reference photo**: show the first image with `status: "available"`; skip `needs_review` images
   (5 photos are flagged — watermark, wrong crop, or unverified symptoms; see the Quality Report).
5. **Show `meta.disclaimer` / `disclaimer_ur`** in a fixed footer or collapsible banner on every result page.
   It covers both hackathon-prototype honesty and the follow-the-label pesticide rule.
6. **Search / browse**: build a client-side index over `plant.name`, `disease.name`, and `aliases`
   in both languages, so "target spot", "ٹماٹر", and "leaf rust" all find their pages.
7. **Treatment rendering**: `treatment` arrays are pre-sized for bullets — render one `<li>` per item,
   and consider styling the last item (usually the label/local-expert caution) as a highlighted note.
8. **Image serving**: `images/` uses lowercase, no-space, extension-normalised filenames — safe for
   URLs on Windows and Linux servers as-is; no rewriting needed.

## Attribution & Sources

Per-entry `source.name` / `source.url` are preserved from the original sheet (typos fixed, dead
placeholder URLs trimmed — details in `DATA_QUALITY_REPORT.md`). Reference photos are the user's
own collection; the 116 originals in `C:\Users\DELL\Downloads\demo photos` were **copied**, never moved or modified.
