# 🌱 FasalDoc — AI-Powered Crop Health Assistant

> **Apni Fasal Ki Awaaz Mein Baat Karein**

FasalDoc is a farmer-focused crop health assistance system designed for small and medium-scale farmers in Pakistan. The application uses a plant image, an optional farmer question, AI-based crop diagnosis, and a local agricultural knowledge base to provide simple and actionable guidance.

FasalDoc is designed around an important principle:

> **When the system is not confident, it should not pretend to know.**

Instead, uncertain cases are routed toward safer AI fallback and/or expert guidance.

---

## 🎯 Problem

Farmers may face difficulty identifying crop diseases quickly, especially when:

* professional agricultural advice is not immediately available;
* disease symptoms look similar;
* technical agricultural information is difficult to understand;
* advice is not available in the farmer's preferred language;
* an AI model is overly confident about an image outside its training scope.

FasalDoc addresses these issues through a photo-first, multilingual, AI-assisted workflow.

---

## 💡 Solution

The current system combines:

* **Gemini Vision** for multimodal crop-image analysis
* **Local RAG / Knowledge Base** for agriculture-specific grounding
* **Urdu, Roman Urdu, and English** response support
* **Confidence-based safety handling**
* **Expert escalation** for uncertain cases
* **Gemini model failover** for transient cloud/model failures
* a planned/active **MobileNetV2 Data Science layer** for supported disease classes

The intended architecture is:

```text
                FasalDoc
                   │
          Leaf Image + Question
                   │
                   ▼
          ML / Gemini Analysis
                   │
          ┌────────┴────────┐
          │                 │
     ML accepted       Low confidence /
     prediction        unsupported/OOD
          │                 │
          │                 ▼
          │           Gemini Vision
          │                 │
          └────────┬────────┘
                   ▼
          Local Knowledge Base
                 (RAG)
                   │
                   ▼
            Gemini Advisory
                   │
          ┌────────┼────────┐
          ▼        ▼        ▼
        Urdu     Roman     English
                   │
                   ▼
            Farmer-friendly
              advice
                   │
                   ▼
             Expert guidance
             when required
```

---

# 🧠 AI Architecture

## Gemini Vision

Gemini receives the uploaded crop image together with the farmer's optional question.

It can analyze:

* visible crop symptoms;
* possible disease;
* confidence;
* whether the image appears to contain a plant/crop;
* farmer-specific context from the question.

The current Gemini implementation uses a multimodal request containing both image data and text.

---

## 🔎 RAG / Local Agriculture Knowledge

FasalDoc does not rely only on a general-purpose language model.

A local agricultural knowledge base is used to ground advice with relevant information such as:

* symptoms;
* likely causes;
* low-cost treatment;
* prevention;
* when to consult an expert.

The existing knowledge-base retrieval logic is reused by the Gemini provider.

The intended flow is:

```text
Diagnosis
   ↓
Retrieve relevant local knowledge
   ↓
Provide retrieved knowledge to Gemini
   ↓
Generate farmer-friendly advice
```

This allows the generative AI layer to explain a diagnosis using project-specific agricultural information instead of relying entirely on unconstrained model knowledge.

---

# 🌍 Multilingual Support

FasalDoc supports three response languages:

| Language   | Code  | Output      |
| ---------- | ----- | ----------- |
| English    | `en`  | English     |
| Urdu       | `ur`  | Urdu script |
| Roman Urdu | `rom` | Roman Urdu  |

The application enforces the selected language across the final response.

### Language invariant

```text
en  → English
ur  → Urdu script
rom → Roman Urdu
```

The backend performs final language validation before returning the response.

This prevents common model behavior such as:

* Roman Urdu being returned when English was requested;
* English sentences appearing inside an Urdu response;
* Urdu script appearing in Roman Urdu mode;
* unrelated Unicode scripts appearing in localized output.

---

# 🛡️ Safety and Confidence Handling

FasalDoc is intentionally conservative.

When confidence is low, the system should not confidently provide a specific disease diagnosis.

The project uses a confidence threshold and expert escalation so that uncertain cases can be referred to a local agriculture expert.

Conceptually:

```text
High confidence
      ↓
Specific guidance

Low confidence
      ↓
Uncertain / safer response
      ↓
Expert guidance
```

This is especially important because farmers may act directly on the advice displayed by the application.

---

# 🔄 Gemini Model Failover

The Gemini integration supports a fallback model chain for transient provider failures.

Transient conditions such as:

* rate limits;
* temporary service unavailability;
* timeouts;
* temporary network failures;

can trigger the next configured Gemini model.

Non-transient failures such as invalid credentials or invalid requests are not blindly retried across models.

The goal is to prevent the application from unnecessarily stopping when one Gemini model is temporarily unavailable.

---

# 🤖 Machine Learning / Data Science Layer

The project includes a MobileNetV2-based classification layer for the Data Science phase.

### Model concept

```text
Input Image
     ↓
MobileNetV2
     ↓
Global Average Pooling
     ↓
Dropout
     ↓
16-class Softmax
```

The classifier is intended to recognize exactly **16 project-defined classes**.

The ML model is not treated as an unrestricted universal crop classifier.

---

## 🚫 Unsupported Crops / OOD Handling

A normal softmax classifier always produces a class prediction even when an image belongs to a crop it has never seen.

For example:

```text
Wheat image
    ↓
Naive classifier
    ↓
"Corn Healthy" ❌
```

FasalDoc is designed to avoid this behavior.

Instead:

```text
Image
 ↓
MobileNetV2
 ↓
Confidence / supported-crop check
 ↓
Prediction rejected?
     │
     ├── Yes → Gemini Vision
     │
     └── No  → ML diagnosis accepted
```

This prevents the system from blindly forcing unsupported crops into one of the trained classes.

The OOD/rejection mechanism is described as a practical heuristic rather than a mathematically perfect open-set detector.

---

# 🔗 ML + Gemini + RAG

The ML layer and generative AI layer have separate responsibilities.

### MobileNetV2

The trained ML model is responsible for the disease classification for supported, accepted predictions.

### Gemini

Gemini is responsible for:

* visual fallback when ML is uncertain;
* handling unsupported/OOD cases;
* explaining accepted ML predictions;
* generating farmer-friendly advice;
* working with the local knowledge base.

### RAG

The local knowledge base grounds the generated advice with project-specific agricultural information.

Therefore:

```text
MobileNetV2 = trained Data Science classifier

Gemini = generative AI / vision / advisory layer

RAG = local agricultural grounding
```

---

# 🖥️ Application Flow

## Farmer Diagnosis

```text
1. Farmer uploads/takes a crop photo
             ↓
2. Optional question is provided
             ↓
3. Selected language is sent with the request
             ↓
4. ML classifier attempts prediction
             ↓
5. Confidence / OOD decision
             ↓
6. Gemini is used when fallback is required
             ↓
7. Relevant local knowledge is retrieved
             ↓
8. Gemini generates advice
             ↓
9. Final language/safety validation
             ↓
10. Result displayed to farmer
```

---

# 💻 Technology Stack

## Frontend

* React
* TypeScript
* Vite
* Mobile-first UI
* Browser camera/file input
* Language selection

## Backend

* Python
* FastAPI
* Uvicorn
* REST API
* CORS configuration

## AI

* Google Gemini
* Gemini Vision / multimodal generation
* Gemini model failover

## Data Science

* TensorFlow / Keras
* MobileNetV2
* NumPy
* scikit-learn
* Pillow
* transfer learning

## Knowledge

* Local agriculture knowledge base
* RAG-style retrieval and grounding

---

# 📁 Project Structure

```text
FasalDoc/
│
├── backend/
│   ├── main.py
│   ├── routes/
│   │   ├── diagnose.py
│   │   └── followup.py
│   ├── services/
│   │   ├── diagnosis_service.py
│   │   ├── gemini_provider.py
│   │   ├── ml_classifier.py
│   │   └── ...
│   └── ml_models/
│       ├── ...
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── data/
│   │   ├── i18n/
│   │   ├── pages/
│   │   ├── services/
│   │   └── ...
│   └── scripts/
│
├── ml/
│   ├── train_mobilenetv2.py
│   ├── evaluate_model.py
│   ├── build_dataset_split.py
│   ├── dataset_manifest.json
│   └── evaluation/
│
├── tests/
│   ├── test_gemini_provider.py
│   ├── test_gemini_failover.py
│   ├── test_language_localization.py
│   ├── test_frontend_contract.py
│   └── test_ml_integration.py
│
├── data/
│   └── ...
│
├── requirements.txt
└── README.md
```

---

# 🚀 Running the Application

## Backend

From the project root:

```bash
cd /Users/mac/Desktop/FasalDoc
source .venv/bin/activate
FASALDOC_ML_ENABLED=1 python -m uvicorn backend.main:app --reload --port 8000
```

Backend:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

---

## Frontend

Open another terminal:

```bash
cd /Users/mac/Desktop/FasalDoc/frontend
npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

# 🔧 Configuration

Create a `.env` file based on the project's environment template.

Important configuration includes:

```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=your_model_here

CORS_ALLOW_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174

FASALDOC_ML_ENABLED=1
```

Never commit API keys or secrets.

---

# 🧪 Testing

FasalDoc contains unit, integration, language, frontend-contract, and ML-related tests.

Examples:

```bash
python -m pytest -q
```

ML integration:

```bash
python -m pytest tests/test_ml_integration.py -q
```

Language localization:

```bash
python -m pytest tests/test_language_localization.py -q
```

Frontend contract:

```bash
python -m pytest tests/test_frontend_contract.py -q
```

The project also uses live diagnosis testing for the configured Gemini environment.

---

# 📊 Data Science Evaluation

The ML phase evaluates the classifier using:

* Accuracy
* Precision
* Recall
* F1-score
* Macro averages
* Weighted averages
* Per-class classification report
* Confusion matrix

The project also documents:

* dataset distribution;
* train/validation/test split;
* duplicate checking;
* data quality;
* model configuration;
* rejection/OOD limitations.

Metrics are intended to be reported from the held-out test set without manually modifying the results.

---

# 🔬 Reproducible Data Preparation

The ML dataset preparation includes a deterministic split process.

The preparation pipeline is designed to:

* use the exact project-defined 16 classes;
* detect corrupted images;
* check duplicate images;
* prevent cross-split duplicate leakage;
* use a fixed random seed;
* record dataset information in a machine-readable manifest.

The dataset manifest provides a reproducible record of the prepared dataset.

---

# ⚠️ Current Limitations

FasalDoc is a prototype/hackathon system and has important limitations.

### Dataset limitations

The quality of an ML classifier depends on the diversity and representativeness of its training data.

Strong held-out test performance on a curated dataset does not automatically prove equivalent performance on photographs taken in real agricultural fields.

### OOD limitations

The unsupported-crop rejection mechanism is a practical heuristic. It should not be described as a perfect mathematical open-set recognition system.

### Generative AI limitations

Gemini-generated advice can still contain mistakes. FasalDoc therefore uses:

* local knowledge grounding;
* language validation;
* confidence handling;
* expert escalation.

### Internet dependency

The Gemini-powered portions require network/API access.

---

# 🌾 Why FasalDoc?

FasalDoc focuses on the complete farmer interaction rather than only disease classification.

The goal is:

```text
See a problem
     ↓
Take a photo
     ↓
Ask naturally
     ↓
Get understandable guidance
     ↓
Know how confident the system is
     ↓
Get local/contextual advice
     ↓
Reach an expert when necessary
```

Its core focus is:

**AI + Data Science + Local Agriculture Knowledge + Language Accessibility**

for farmers in Pakistan.

---

# 🏆 Hackathon Focus

FasalDoc is designed around a real agricultural problem in Pakistan and combines:

* computer vision;
* machine learning;
* generative AI;
* RAG;
* multilingual interaction;
* confidence-aware decision making;
* fallback handling;
* practical farmer guidance.

The project separates the responsibilities of the technologies instead of treating all AI components as one black box.

---

# 🧑‍💻 Development Status

## AI Phase

**Completed**

Includes:

* Gemini Vision integration
* local RAG grounding
* Urdu support
* Roman Urdu support
* English support
* language validation
* confidence/safety handling
* Gemini model failover
* frontend/backend integration
* follow-up interaction

## ML / Data Science Phase

**Implemented and undergoing final reproducibility and end-to-end verification**

Includes:

* 16-class MobileNetV2 classifier
* reproducible dataset preparation
* model evaluation
* confusion matrix
* confidence-based rejection
* unsupported/OOD handling
* ML → Gemini fallback
* ML → RAG → Gemini advisory flow
* backend integration
* ML integration tests

Final model reproducibility and browser end-to-end verification are being completed before the ML phase is frozen.

---

# 📌 Key Design Principle

FasalDoc does not assume:

> **"AI said it, therefore it must be correct."**

Instead, the system is designed around:

```text
Prediction
   +
Confidence
   +
Knowledge grounding
   +
Fallback
   +
Human expert escalation
```

This makes the system more appropriate for a real-world agricultural assistance scenario where incorrect advice can have practical consequences.

---

# 👥 Project Purpose

FasalDoc was developed as a practical AI/Data Science project focused on applying modern machine learning and generative AI to a real agricultural problem in Pakistan.

The project demonstrates the integration of:

**MobileNetV2 + Gemini Vision + RAG + multilingual AI + safety-aware fallback**

within a single farmer-facing application.
