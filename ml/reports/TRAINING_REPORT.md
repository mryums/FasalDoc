# FasalDoc MobileNetV2 Training Report
_Generated: 2026-10-02_

## Framework / Hardware
- Python 3.11.16, TensorFlow 2.16.2 (Keras 3.15.1), NumPy 1.26.4
- Platform: Darwin 21.6.0 x86_64 (i386, 2 physical cores, 8 GB RAM) — CPU-only

## Architecture (matches the shipped runtime model exactly)
- Backbone: `MobileNetV2(include_top=False, weights='imagenet')` — **frozen**; the
  end-to-end graph is `Input -> Rescaling(1/127.5,-1) -> backbone -> GAP ->
  Dropout(0.3) -> Dense(16, softmax)`, identical to
  `backend/ml_models/FasalDoc_MobileNetV2_final.keras` and to the inference path in
  `backend/services/ml_classifier.py` (raw 0-255 in, single internal rescale).
- Head: Dropout(0.3) → Dense(16, softmax)

## Hyperparameters
- Image size: 224x224 | raw batch 32 | head batch 128
- Optimizer: Adam(lr=1e-3) | Loss: sparse_categorical_crossentropy
- Max epochs: 60 | EarlyStopping patience: 8 (val_loss, restore best)
- Checkpointing: ModelCheckpoint on best val_loss | Seed: 42
- Train/val/test images: 19659/4216/4210

## Class-imbalance strategy
- Balanced class weights (`sklearn compute_class_weight`), dataset left untouched:

| Class | Weight | Train images |
|---|---|---|
| Background_without_leaves | 1.536 | 800 |
| Corn___Cercospora_leaf_spot Gray_leaf_spot | 3.423 | 359 |
| Corn___Common_rust | 1.473 | 834 |
| Corn___Northern_Leaf_Blight | 1.783 | 689 |
| Corn___healthy | 1.509 | 814 |
| Orange___Haunglongbing_(Citrus_greening) | 0.319 | 3855 |
| Potato___Early_blight | 1.755 | 700 |
| Potato___Late_blight | 1.755 | 700 |
| Potato___healthy | 11.591 | 106 |
| Tomato___Bacterial_spot | 0.825 | 1489 |
| Tomato___Early_blight | 1.755 | 700 |
| Tomato___Late_blight | 0.920 | 1336 |
| Tomato___Septoria_leaf_spot | 0.991 | 1240 |
| Tomato___Spider_mites Two-spotted_spider_mite | 1.047 | 1173 |
| Tomato___Tomato_Yellow_Leaf_Curl_Virus | 0.328 | 3750 |
| Tomato___healthy | 1.103 | 1114 |

## Training / validation
- Epochs run: 51 | final train loss 0.1000 | best val loss 0.1190
- Final val accuracy: 0.9625 | best val accuracy: 0.9625

## Test results (held-out split, never used for training)
- Accuracy: **0.9570**
- Macro precision / recall / F1: 0.9376 / 0.9410 / **0.9388**
- Weighted F1: 0.9568

## Per-class test performance
| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Background_without_leaves | 1.000 | 0.982 | 0.991 | 171 |
| Corn___Cercospora_leaf_spot Gray_leaf_spot | 0.793 | 0.844 | 0.818 | 77 |
| Corn___Common_rust | 0.994 | 1.000 | 0.997 | 179 |
| Corn___Northern_Leaf_Blight | 0.916 | 0.885 | 0.900 | 148 |
| Corn___healthy | 1.000 | 1.000 | 1.000 | 174 |
| Orange___Haunglongbing_(Citrus_greening) | 1.000 | 0.994 | 0.997 | 826 |
| Potato___Early_blight | 0.987 | 0.987 | 0.987 | 150 |
| Potato___Late_blight | 0.973 | 0.947 | 0.959 | 150 |
| Potato___healthy | 0.920 | 1.000 | 0.958 | 23 |
| Tomato___Bacterial_spot | 0.940 | 0.931 | 0.935 | 319 |
| Tomato___Early_blight | 0.832 | 0.727 | 0.776 | 150 |
| Tomato___Late_blight | 0.936 | 0.927 | 0.931 | 286 |
| Tomato___Septoria_leaf_spot | 0.880 | 0.913 | 0.896 | 265 |
| Tomato___Spider_mites Two-spotted_spider_mite | 0.912 | 0.952 | 0.932 | 251 |
| Tomato___Tomato_Yellow_Leaf_Curl_Virus | 0.986 | 0.988 | 0.987 | 803 |
| Tomato___healthy | 0.932 | 0.979 | 0.955 | 238 |

Confusion matrices: `reports/confusion_matrix_raw.png`, `reports/confusion_matrix_normalized.png`

## Class → index mapping
Exact mapping (alphabetical, seed-independent) recorded in `reports/class_indices.json`:
```json
["Background_without_leaves", "Corn___Cercospora_leaf_spot Gray_leaf_spot", "Corn___Common_rust", "Corn___Northern_Leaf_Blight", "Corn___healthy", "Orange___Haunglongbing_(Citrus_greening)", "Potato___Early_blight", "Potato___Late_blight", "Potato___healthy", "Tomato___Bacterial_spot", "Tomato___Early_blight", "Tomato___Late_blight", "Tomato___Septoria_leaf_spot", "Tomato___Spider_mites Two-spotted_spider_mite", "Tomato___Tomato_Yellow_Leaf_Curl_Virus", "Tomato___healthy"]
```

## Limitations
- Stage-1 only: frozen backbone + linear-ish head. Underfitting is expected on visually
  similar classes; a later stage may unfreeze the top MobileNetV2 blocks for fine-tuning.
- No data augmentation (kept minimal for this hardware; likely suppresses minority-class recall).
- `Potato___healthy` (23 test images) and `Corn___Cercospora_leaf_spot` (77) give high-variance
  per-class metrics.
- `Background_without_leaves` is a trained reject class; the app currently defers
  it to Gemini Vision as a plant sanity check rather than auto-rejecting.
- CPU-only training bottleneck extraction took significant wall-clock time on a 2-core i7.
- INTEGRATED: /diagnose runs this model first when FASALDOC_ML_ENABLED is on and
  falls back to the Gemini vision flow when ML is unavailable or low-confidence.

## Artifacts
- `ml/models/mobilenetv2_head_best.keras` (classification head, best val loss)
- `ml/models/mobilenetv2_full.keras` (end-to-end: raw image → 16-class probabilities)
- `ml/reports/training_history.json`, `test_metrics.json`, `run_metadata.json`,
  `class_indices.json`, `class_weights.json`, `dataset_sanity.json`
- `ml/features/{train,validation,test}.npz` (cached bottleneck features)
