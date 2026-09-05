# 🌾 FasalDoc

### AI-Powered Crop Diagnosis & Voice Assistant for Pakistani Farmers

**FasalDoc** is an AI-powered agricultural assistant designed to help farmers identify crop diseases and receive practical treatment guidance using **crop images and Urdu voice/text interaction**.

The system combines **computer vision, multilingual AI, voice interaction, agricultural knowledge, and confidence-aware responses** into a simple farmer-friendly workflow.

> **PHOTO + URDU QUESTION → AI ANALYSIS → DIAGNOSIS → PRACTICAL ACTION → SPOKEN RESPONSE**

---

## 📌 Project Overview

Farmers often face crop diseases and pest problems without having immediate access to agricultural experts. Identifying a disease from symptoms can be difficult, especially when the farmer has limited access to reliable agricultural information.

FasalDoc aims to make basic crop diagnosis more accessible through an easy-to-use interface where a farmer can:

1. 📷 Capture or upload a crop image
2. 🎙️ Ask a question in Urdu
3. 🤖 Get AI-powered visual analysis
4. 🌱 Receive a possible crop/disease diagnosis
5. 📊 See the confidence level
6. 💊 Receive practical treatment and prevention guidance
7. 🔊 Hear the response through voice
8. 💬 Ask follow-up questions while maintaining context

---

# ✨ Key Features

## 🌱 AI Crop Diagnosis

FasalDoc analyzes uploaded crop images using a vision-capable Qwen model.

The AI can consider:

* Crop appearance
* Visible symptoms
* Leaf damage
* Disease indicators
* Pest-related damage
* Farmer's question

---

## 🎙️ Urdu Voice Interaction

The system is designed around voice-first interaction for farmers.

Supported flow:

**Farmer Voice → Speech-to-Text → AI Analysis → Urdu Response → Text-to-Speech**

This reduces dependence on typing and makes the system more accessible to users who prefer speaking Urdu.

---

## 🖼️ Image-Based Analysis

Users can upload or capture crop images.

Supported image formats include:

* JPEG
* PNG
* WEBP

The backend validates uploaded images before processing them.

---

## 📊 Confidence Transparency

FasalDoc provides a confidence value with the diagnosis.

This is important because agricultural image diagnosis is not always certain.

Instead of pretending to know the answer, the system is designed to communicate uncertainty when the available evidence is insufficient.

---

## 💬 Follow-Up Questions

After receiving a diagnosis, farmers can ask additional questions.

Example:

> "Is ka ilaj kya hai?"

followed by:

> "Kitni dafa spray karna chahiye?"

The backend maintains recent diagnosis context so follow-up questions can remain connected to the previous analysis.

---

## 🇵🇰 Local Agricultural Knowledge

The project includes a curated agricultural knowledge base containing information such as:

* Crop
* Disease
* Symptoms
* Causes
* Treatment
* Prevention
* Urdu terminology
* Image references
* Source information

The knowledge base is used as a reference for validating and improving agricultural responses.

---

## 🛡️ Uncertainty & Safety

FasalDoc is designed not to blindly provide a diagnosis when the visual evidence is insufficient.

Important test scenarios include:

* Clear disease image
* Blurry image
* Ambiguous image
* Pest damage
* Healthy plant
* Non-plant image
* Unknown/unsupported crop

For unclear cases, the preferred behavior is to request a clearer image or additional information rather than confidently guessing.

---

# 🏗️ System Architecture

```text
                    ┌──────────────────────┐
                    │      Farmer          │
                    │  Photo + Voice/Text  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   React Frontend     │
                    │ Camera / Microphone  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    FastAPI Backend   │
                    │ Validation / Routing │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Qwen AI Provider   │
                    │  Vision + Language   │
                    └──────────┬───────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
          Image Analysis   AI Advice      Voice Services
                │              │              │
                └──────────────┼──────────────┘
                               ▼
                    ┌──────────────────────┐
                    │ Diagnosis + Advice   │
                    │ Confidence + Context │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Urdu Text / Audio    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │       Farmer         │
                    └──────────────────────┘
```

---

# 🧩 Technology Stack

## Frontend

* React
* TypeScript
* Vite
* HTML/CSS
* Browser Camera APIs
* Browser Microphone APIs

## Backend

* Python
* FastAPI
* Uvicorn
* Pydantic

## AI

* Alibaba Cloud Model Studio
* Qwen Vision
* Qwen-Plus
* Qwen ASR
* Qwen TTS

## Data

* JSON
* CSV
* Excel
* Curated agricultural knowledge base
* Plant/crop image dataset

## Testing

* Pytest
* API testing
* Frontend build validation
* Manual end-to-end testing

## Deployment

The project is structured for cloud deployment and includes deployment configuration for the frontend/backend environment.

---

# 📁 Repository Structure

```text
FasalDoc/
│
├── backend/
│   ├── main.py
│   ├── models.py
│   │
│   ├── routes/
│   │   ├── diagnose.py
│   │   └── followup.py
│   │
│   ├── services/
│   │   ├── diagnosis_service.py
│   │   ├── ai_pipeline.py
│   │   └── qwen_provider.py
│   │
│   └── utils/
│       └── validators.py
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── App.tsx
│   │
│   ├── package.json
│   └── vite.config.*
│
├── data/
│   ├── knowledge_base.json
│   │
│   └── plant_disease_dataset/
│       ├── crop_knowledge.json
│       ├── image_mapping.csv
│       ├── crop_knowledge_enhanced.xlsx
│       ├── README.md
│       └── DATA_QUALITY_REPORT.*
│
├── documentation/
│   └── project documentation and reports
│
├── demo_backup/
│   └── demo backup resources
│
├── tests/
│   └── test_api.py
│
├── requirements.txt
├── vercel.json
├── .env.example
└── README.md
```

---

# ⚙️ Requirements

Before running FasalDoc locally, install:

* Python 3.10+
* Node.js 18+
* npm
* Git

For live Qwen inference:

* Alibaba Cloud Model Studio / DashScope access
* Valid `DASHSCOPE_API_KEY`

---

# 🚀 Installation

## 1. Clone the Repository

```bash
git clone https://github.com/mryums/FasalDoc.git
cd FasalDoc
```

---

# 🐍 Backend Setup

Create a Python virtual environment:

```bash
python3 -m venv .venv
```

Activate it on macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# 🔐 Environment Configuration

Create your environment configuration from the example file:

```bash
cp .env.example .env
```

Configure the required environment variables.

For live Qwen integration:

```text
DASHSCOPE_API_KEY=your_actual_api_key
```

### Security

**Never:**

* Commit API keys to GitHub
* Put API keys directly into frontend code
* Share API keys publicly
* Hard-code credentials into source files

API credentials should remain server-side and be provided through environment variables.

---

# ▶️ Run the Backend

From the repository root:

```bash
uvicorn backend.main:app --reload
```

The API will normally be available at:

```text
http://127.0.0.1:8000
```

FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

---

# 💻 Run the Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the development URL shown by Vite.

---

# 🔌 API Endpoints

## POST `/diagnose`

Analyzes a crop image and optionally receives a farmer question.

### Request

Multipart form:

```text
image: image file
question: optional farmer question
```

### Example

```text
POST /diagnose
Content-Type: multipart/form-data
```

### Response

```json
{
  "filename": "crop.jpg",
  "diagnosis": "Early Blight",
  "confidence": 0.70,
  "advice": "Remove affected leaves and follow appropriate treatment guidance.",
  "needs_expert": false
}
```

---

# 💬 POST `/ask-followup`

Answers a follow-up question using the recent diagnosis context.

### Request

```json
{
  "question": "Is ka ilaj kya hai?"
}
```

### Response

```json
{
  "question": "Is ka ilaj kya hai?",
  "answer": "..."
}
```

---

# 🤖 AI Provider Architecture

FasalDoc separates the diagnosis service from the underlying AI provider.

The backend supports:

```text
Diagnosis Service
       │
       ├── QwenDiagnosisProvider
       │
       └── MockDiagnosisProvider
```

This allows the application to continue running during development when live AI credentials are unavailable.

---

# 🧪 Mock Provider

If `DASHSCOPE_API_KEY` is not available, the backend can fall back to:

```text
MockDiagnosisProvider
```

This is useful for:

* Frontend development
* API testing
* UI demonstrations
* Offline testing
* Integration testing

However:

> **Mock results are not real AI predictions.**

They must not be presented as evidence of Qwen's diagnostic accuracy.

---

# 🧠 Live Qwen Provider

When a valid Alibaba Cloud Model Studio / DashScope API key is configured, FasalDoc can use the Qwen provider.

The AI pipeline supports:

```text
Image
  ↓
Qwen Vision
  ↓
Visual Analysis
  ↓
Qwen Language Model
  ↓
Diagnosis + Advice
  ↓
Urdu Response
```

Additional voice capabilities include:

```text
Voice
  ↓
Speech-to-Text
  ↓
Farmer Question
  ↓
AI
  ↓
Text-to-Speech
  ↓
Spoken Response
```

---

# 🗣️ Voice Pipeline

FasalDoc is designed for voice-first interaction.

```text
Farmer speaks Urdu
        ↓
Speech-to-Text
        ↓
Question text
        ↓
Image + Question
        ↓
AI analysis
        ↓
Urdu answer
        ↓
Text-to-Speech
        ↓
Farmer hears answer
```

---

# 🌾 Dataset & Knowledge Base

The project contains a curated agricultural dataset and knowledge base.

Primary knowledge file:

```text
data/knowledge_base.json
```

Additional M4 data resources include:

```text
data/plant_disease_dataset/crop_knowledge.json
data/plant_disease_dataset/image_mapping.csv
data/plant_disease_dataset/crop_knowledge_enhanced.xlsx
```

The dataset includes information covering crop conditions, symptoms, causes, treatments, prevention, and related image references.

The dataset combines existing agricultural image resources with curated/local agricultural information.

---

# 🧪 Testing

The project includes automated backend tests.

Run:

```bash
pytest -q
```

The expected test suite should validate:

* API health
* Diagnosis endpoint
* Follow-up endpoint
* Validation
* Image handling
* Provider selection
* Diagnosis response structure
* Follow-up behavior

---

# 🔍 Recommended Manual Test Cases

Before a demo, test:

### 1. Clear disease image

Expected:

* Relevant diagnosis
* Reasonable confidence
* Relevant treatment

### 2. Different disease/crop

Expected:

* Response changes according to image
* No fixed diagnosis for unrelated images

### 3. Blurry image

Expected:

* Uncertainty
* Request for clearer image when appropriate

### 4. Non-plant image

Expected:

* No fabricated plant diagnosis

### 5. Pest damage

Expected:

* Possible pest-related identification
* Practical action

### 6. Healthy crop

Expected:

* No unnecessary disease claim

### 7. Urdu question

Example:

```text
اس پودے کو کیا بیماری ہے؟
```

Expected:

* Understandable response
* Relevant agricultural terminology

### 8. Follow-up

Example:

```text
Is ka ilaj kya hai?
```

Expected:

* Previous diagnosis context is maintained.

---

# 📊 Testing Philosophy

The goal of testing is not simply to maximize the number of "correct" diagnoses.

The system should be:

### Accurate

When sufficient visual evidence exists.

### Honest

When the AI is uncertain.

### Practical

Recommendations should be understandable and actionable.

### Safe

The system should avoid confidently inventing diagnoses.

### Accessible

Farmers should be able to interact using simple Urdu voice/text.

---

# 👥 Team Responsibilities

## M1 — AI / Prompting

Responsible for:

* Qwen integration
* Vision analysis
* AI prompts
* Diagnosis generation
* Recommendation generation
* Voice AI pipeline

---

## M2 — Backend / API

Responsible for:

* FastAPI server
* API routes
* Request validation
* Frontend/backend integration
* Diagnosis service
* Follow-up context
* AI provider adapter

---

## M3 — Frontend / UX

Responsible for:

* Mobile-first interface
* Camera interaction
* Microphone interaction
* Image upload
* Question input
* Diagnosis display
* Confidence display
* Urdu interface
* Follow-up UI

---

## M4 — Data / Research / Validation

Responsible for:

* Crop/disease knowledge
* Agricultural research
* Dataset organization
* Urdu agricultural terminology
* Treatment information
* Image validation
* AI output validation
* Testing and validation reports

---

## M5 — Cloud / Integration / Deployment

Responsible for:

* Alibaba Cloud setup
* Model Studio configuration
* API credentials/environment
* OSS
* Deployment
* Infrastructure
* End-to-end integration
* Demo reliability

---

# 🔒 Security

Sensitive credentials must never be committed to the repository.

Use environment variables:

```text
DASHSCOPE_API_KEY
```

Add local environment files to `.gitignore`.

Do not place secrets in:

* React code
* GitHub repository
* Screenshots
* README
* Public documentation

---

# ⚠️ Current Limitations

FasalDoc is a hackathon MVP and has several limitations.

### AI Accuracy

Image-based diagnosis can be affected by:

* Image quality
* Lighting
* Camera angle
* Similar-looking diseases
* Unseen crop varieties
* Limited training/reference data

### Agricultural Coverage

The knowledge base does not cover every possible crop, disease, pest, or regional condition.

### Internet/API Dependency

Live Qwen functionality requires access to the Alibaba Cloud Model Studio/DashScope service and a valid API credential.

### Mock Mode

Without a valid API key, the backend may use the mock provider for development/testing.

### Expert Validation

AI-generated agricultural guidance should not be treated as a guaranteed replacement for professional agricultural advice, particularly for serious crop-loss situations or chemical treatment decisions.

---

# 🚧 Future Improvements

Potential future development includes:

* Larger Pakistan-specific crop dataset
* More locally collected field images
* Improved disease classification
* More agricultural regions and crops
* Better Urdu agricultural terminology
* Improved voice recognition in noisy environments
* Multi-image diagnosis
* Persistent farmer sessions
* Expert escalation
* More localized recommendations
* Cloud object storage for images/audio
* Production monitoring
* Offline/low-connectivity support
* More comprehensive treatment safety guidance

---

# 🎬 Demo Scenarios

FasalDoc is designed around three primary demonstration scenarios.

## Scenario 1 — Clear Diagnosis

```text
Crop Image
    ↓
Clear symptoms
    ↓
AI identifies likely disease
    ↓
Confidence shown
    ↓
Treatment provided
    ↓
Urdu response
```

---

## Scenario 2 — Unclear Image

```text
Poor-quality image
    ↓
Insufficient visual evidence
    ↓
Low confidence / uncertainty
    ↓
Farmer asked for clearer image
```

The system should **not pretend to know**.

---

## Scenario 3 — Pest Damage

```text
Damaged crop leaf
    ↓
Visible pest-related symptoms
    ↓
Likely pest/damage identification
    ↓
Practical action
    ↓
Farmer can ask follow-up questions
```

---

# 🏆 Project Differentiation

FasalDoc focuses on several features together rather than treating crop diagnosis as a simple image classifier.

### Computer Vision

Understands crop images and visible symptoms.

### Urdu Voice

Designed around the farmer's natural language.

### Voice-First Interaction

Reduces dependence on typing.

### Confidence Transparency

Communicates uncertainty instead of always forcing an answer.

### Local Knowledge

Uses curated agricultural information relevant to local farming contexts.

### Practical Recommendations

Focuses on what the farmer can actually do after receiving the diagnosis.

---

# 📈 Project Goal

The long-term goal of FasalDoc is to make basic agricultural assistance:

**Accessible → Understandable → Localized → Practical → Voice-first**

for farmers who may not have immediate access to agricultural experts.

---

# 🛠️ Development Status

| Component             | Status                                |
| --------------------- | ------------------------------------- |
| Frontend              | ✅ Implemented                         |
| Camera/Image Upload   | ✅ Implemented                         |
| Voice Input UI        | ✅ Implemented                         |
| FastAPI Backend       | ✅ Implemented                         |
| Diagnosis API         | ✅ Implemented                         |
| Follow-up API         | ✅ Implemented                         |
| Qwen Provider Adapter | ✅ Implemented                         |
| AI Pipeline           | ✅ Implemented                         |
| Knowledge Base        | ✅ Implemented                         |
| Dataset Organization  | ✅ Implemented                         |
| Backend Tests         | ✅ Passing                             |
| Frontend Build        | ✅ Passing                             |
| Mock Fallback         | ✅ Implemented                         |
| Live Qwen Inference   | ⚠️ Requires valid Alibaba credentials |
| Production Deployment | ⚠️ Requires final cloud configuration |

---

# 📋 Quick Start

```bash
# Clone
git clone https://github.com/mryums/FasalDoc.git
cd FasalDoc

# Backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run backend
uvicorn backend.main:app --reload

# New terminal
cd frontend
npm install
npm run dev
```

For live AI, configure:

```text
DASHSCOPE_API_KEY
```

before starting the backend.

---

# 📄 License

This project was developed as a hackathon project.

Add an official license here if the team decides to open-source the project under a specific license.

---

# 🌾 FasalDoc

### **See the crop. Understand the problem. Speak to get help.**

**PHOTO + VOICE → AI → DIAGNOSIS → ACTION**
