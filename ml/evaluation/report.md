# FasalDoc — MobileNetV2 Held-Out Evaluation
_Generated: 2026-10-02T16:10:29.616853+00:00 · evaluated on 4210 test images in 4.2 min_

> **MobileNetV2 is the trained Data Science model.** Gemini is a separate
> generative advisory/explanation layer and is **not** the classifier.
> Every metric below is measured from real predictions on the held-out
> `data/ml_dataset/test` split — nothing is fabricated.

## 1. Model under evaluation
- File: `backend/ml_models/FasalDoc_MobileNetV2_final.keras` (the exact artifact the backend serves)
- Class mapping: `backend/ml_models/FasalDoc_class_mapping.json` — **16 classes**, argmax index == mapping index (verified)
- Architecture (read from the saved graph): Rescaling(1/127.5, offset=-1) -> MobileNetV2 backbone (ImageNet, frozen) -> GlobalAveragePooling2D -> Dropout(0.3) -> Dense(16, softmax)
- Backbone: MobileNetV2 (ImageNet pretrained, frozen, include_top=False) + Rescaling(1/127.5,-1) + GlobalAveragePooling2D
- Head: GlobalAveragePooling2D -> Dropout(0.3) -> Dense(16, softmax)
- Input: [None, 224, 224, 3] → Output: [None, 16] · 2,278,480 params
- Preprocessing: decode -> RGB -> bilinear resize 224x224 -> float32 0-255; model's own Rescaling(1/127.5,-1) maps to [-1,1]; mobilenet_v2.preprocess_input deliberately NOT applied
- Runtime: Python 3.11.16, TensorFlow 2.16.2, Keras 3.15.1, NumPy 1.26.4 (Darwin 21.6.0 x86_64, CPU-only)

## 2. Dataset & splits
- Source: `data/ml_dataset` (PlantVillage-derived, 16 selected classes)
- Train / Validation / Test images: 19,659 / 4,216 / 4,210
- Corrupt images skipped this run: 0
- Full provenance (seed 42, SHA-1 dedup, 0 cross-split leakage, per-class counts) is in `data/ml_dataset/DATASET_SPLIT_REPORT.md`.

### Test-set class distribution (imbalance)
| Class | Test images |
|---|---:|
| Orange___Haunglongbing_(Citrus_greening) | 826 |
| Tomato___Tomato_Yellow_Leaf_Curl_Virus | 803 |
| Tomato___Bacterial_spot | 319 |
| Tomato___Late_blight | 286 |
| Tomato___Septoria_leaf_spot | 265 |
| Tomato___Spider_mites Two-spotted_spider_mite | 251 |
| Tomato___healthy | 238 |
| Corn___Common_rust | 179 |
| Corn___healthy | 174 |
| Background_without_leaves | 171 |
| Potato___Early_blight | 150 |
| Potato___Late_blight | 150 |
| Tomato___Early_blight | 150 |
| Corn___Northern_Leaf_Blight | 148 |
| Corn___Cercospora_leaf_spot Gray_leaf_spot | 77 |
| Potato___healthy | 23 |

_Potato___healthy has only 23 held-out images — its per-class numbers are high-variance and must not be over-read._

## 3. Headline metrics (real, held out)
| Metric | Value |
|---|---:|
| Accuracy | 0.9570 |
| Macro Precision | 0.9376 |
| Macro Recall | 0.9410 |
| Macro F1 | 0.9388 |
| Weighted Precision | 0.9570 |
| Weighted Recall | 0.9570 |
| Weighted F1 | 0.9568 |

_Macro averages treat every class equally (important under imbalance); weighted averages honor each class's test support._

## 4. Per-class report
| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| Background_without_leaves | 1.0000 | 0.9825 | 0.9912 | 171 |
| Corn___Cercospora_leaf_spot Gray_leaf_spot | 0.7927 | 0.8442 | 0.8176 | 77 |
| Corn___Common_rust | 0.9944 | 1.0000 | 0.9972 | 179 |
| Corn___Northern_Leaf_Blight | 0.9161 | 0.8851 | 0.9003 | 148 |
| Corn___healthy | 1.0000 | 1.0000 | 1.0000 | 174 |
| Orange___Haunglongbing_(Citrus_greening) | 1.0000 | 0.9939 | 0.9970 | 826 |
| Potato___Early_blight | 0.9867 | 0.9867 | 0.9867 | 150 |
| Potato___Late_blight | 0.9726 | 0.9467 | 0.9595 | 150 |
| Potato___healthy | 0.9200 | 1.0000 | 0.9583 | 23 |
| Tomato___Bacterial_spot | 0.9399 | 0.9310 | 0.9354 | 319 |
| Tomato___Early_blight | 0.8321 | 0.7267 | 0.7758 | 150 |
| Tomato___Late_blight | 0.9364 | 0.9266 | 0.9315 | 286 |
| Tomato___Septoria_leaf_spot | 0.8800 | 0.9132 | 0.8963 | 265 |
| Tomato___Spider_mites Two-spotted_spider_mite | 0.9122 | 0.9522 | 0.9318 | 251 |
| Tomato___Tomato_Yellow_Leaf_Curl_Virus | 0.9863 | 0.9875 | 0.9869 | 803 |
| Tomato___healthy | 0.9320 | 0.9790 | 0.9549 | 238 |

### Weakest classes (factual, not hidden)
- **Tomato___Early_blight** — F1 0.7758 (P 0.8321 / R 0.7267, n=150)
- **Corn___Cercospora_leaf_spot Gray_leaf_spot** — F1 0.8176 (P 0.7927 / R 0.8442, n=77)
- **Tomato___Septoria_leaf_spot** — F1 0.8963 (P 0.8800 / R 0.9132, n=265)

## 5. Confusion matrix
- Machine-readable CSV: `ml/evaluation/confusion_matrix.csv` (rows = true class, columns = predicted class, order == `class_names`)
- Images: `ml/evaluation/confusion_matrix_raw.png` and `confusion_matrix_normalized.png`

## 6. Confidence / rejection behavior (safety layer context)
- Runtime threshold: **0.60** (`ML_CONFIDENCE_THRESHOLD`, default 0.60)
- 97.6% of test images reach the threshold; the rest are routed to Gemini Vision for a second opinion.
- Accuracy on the above-threshold subset: 0.9659
- Mean confidence when correct: 0.9744 · when wrong: 0.7323
- Confidence range: [0.3093, 1.0000], median 0.9999

_This is a softmax confidence **heuristic**, not mathematical OOD detection. Unsupported crops can still receive a high softmax score, so the backend additionally runs a Gemini crop-identity check before trusting a confident ML call (see the integration report)._

## 7. Model / training configuration (what is verifiable)
- **Verified from the saved graph**: frozen MobileNetV2 ImageNet backbone (include_top=False) + Rescaling(1/127.5,-1) + GlobalAveragePooling2D + Dropout(0.3) + Dense(16, softmax); 2,278,480 trainable+non-trainable params; 224x224x3 float input.
- Reproduced by `ml/train_mobilenetv2.py` (frozen backbone, Adam lr=1e-3, sparse_categorical_crossentropy, EarlyStopping patience 8 + ModelCheckpoint on val_loss, seed 42, **balanced class weights**, **no augmentation**).
- **Reproducibility (fixed)**: the training script's `build_full_model` now assembles byte-for-byte the shipped graph (same 6 top-level layers, same parameter count, same 16-class output). The earlier `Dense(512)` head that diverged from the artifact has been removed, and this model was rebuilt from that corrected pipeline, so the exact recipe IS reconstructable from the repository. We report the architecture we can observe and evaluate the model we actually ship.
- Class imbalance is handled with balanced class weights (dataset left untouched), matching the documented strategy.

## 8. Limitations (honest)
- Data are PlantVillage **laboratory** imagery (single leaf, clean background); real Pakistani field photos differ → expect lower accuracy in production.
- **Severe class imbalance** (Potato___healthy 152 vs Orange HLB 5,507); the smallest classes' metrics are high-variance.
- Frozen-backbone bottleneck learning cannot adapt low/mid-level features to crop-disease texture the way full fine-tuning can.
- Accuracy alone is misleading here; **macro F1 is the honest headline**.
- Treat these results as a **proof-of-concept**, not production-grade.

## 9. Reproducibility
- Seed recorded: 42; splits fixed by `DATASET_SPLIT_REPORT.md` (seed 42, SHA-1 dedup).
- Rerun with: `ml-env/bin/python ml/evaluate_model.py`
- This script evaluates the shipped model directly over raw test images using the runtime preprocessing, so metrics match what the app serves.
