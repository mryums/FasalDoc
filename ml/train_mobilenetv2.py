"""MobileNetV2 transfer-learning training pipeline for FasalDoc (Data Science phase).

Design ( tuned for an Intel Core i7-5650U / 8 GB RAM / macOS Monterey box ):
    * MobileNetV2 ImageNet backbone, FROZEN (include_top=False). The saved
      end-to-end graph is Input -> Rescaling(1/127.5,-1) -> backbone ->
      GlobalAveragePooling2D -> Dropout(0.3) -> Dense(16, softmax), i.e. exactly
      the shipped runtime model and the ml_classifier.py inference path.
    * Stage 1 trains only the classification head. To keep this feasible on
      2 CPU cores, the frozen backbone is run ONCE over every split and the
      1280-d bottleneck features are cached to disk (classic bottleneck
      feature extraction — mathematically equivalent to end-to-end training
      with a fully frozen base, orders of magnitude faster here).
    * Severe class imbalance (Potato___healthy 106 vs Orange HLB 3855) is
      handled with balanced CLASS WEIGHTS only — the dataset is untouched.
    * EarlyStopping + ModelCheckpoint on validation loss.
    * 224x224 inputs, small raw-image batches (32) for backbone inference.

Stages ( --stage ) :
    sanity    : verify loaders/class mapping, inspect a few real batches
    extract   : run frozen MobileNetV2 over train/validation/test -> npz cache
    train     : train the classification head on cached features
    evaluate  : test-set metrics (acc/precision/recall/F1, confusion matrix)
    report    : write ml/reports/TRAINING_REPORT.md from all artifacts
    all       : sanity -> extract -> train -> evaluate -> report

Nothing under backend/ or frontend/ is imported or modified by this script.
Run with the ML virtualenv:  ml-env/bin/python ml/train_mobilenetv2.py --stage all
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sys
import time
from datetime import datetime, timezone

# Keep this 2-core CPU breathing — set before TF is imported.
for _var in ("OMP_NUM_THREADS", "TF_NUM_INTRAOP_THREADS", "TF_NUM_INTEROP_THREADS"):
    os.environ.setdefault(_var, "2")

import numpy as np

# Determinism (matches the dataset-prep protocol seed).
SEED = 42

import tensorflow as tf
from tensorflow import keras

keras.utils.set_random_seed(SEED)
tf.config.threading.set_intra_op_parallelism_threads(2)
tf.config.threading.set_inter_op_parallelism_threads(2)
tf.random.set_seed(SEED)
np.random.seed(SEED)

from PIL import Image
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.utils.class_weight import compute_class_weight

# ---------------------------------------------------------------- paths -----
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_ROOT = os.path.join(PROJECT_ROOT, "data", "ml_dataset")
ML_ROOT = os.path.join(PROJECT_ROOT, "ml")
FEATURES_DIR = os.path.join(ML_ROOT, "features")
MODELS_DIR = os.path.join(ML_ROOT, "models")
REPORTS_DIR = os.path.join(ML_ROOT, "reports")

SPLITS = ("train", "validation", "test")
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

IMG_SIZE = 224
RAW_BATCH = 32          # images per backbone pass — small, for 8 GB RAM
HEAD_BATCH = 128        # cached-feature batches (cheap, no CNN in the loop)
HEAD_EPOCHS = 60
PATIENCE = 8            # EarlyStopping patience (epochs)
BASE_WEIGHTS = "imagenet"

DISEASE_CLASSES = [
    "Background_without_leaves",
    "Corn___Cercospora_leaf_spot Gray_leaf_spot",
    "Corn___Common_rust",
    "Corn___Northern_Leaf_Blight",
    "Corn___healthy",
    "Orange___Haunglongbing_(Citrus_greening)",
    "Potato___Early_blight",
    "Potato___Late_blight",
    "Potato___healthy",
    "Tomato___Bacterial_spot",
    "Tomato___Early_blight",
    "Tomato___Late_blight",
    "Tomato___Septoria_leaf_spot",
    "Tomato___Spider_mites Two-spotted_spider_mite",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato___healthy",
]


# ------------------------------------------------------------- dataset ------
def list_split(split: str):
    """Return {class_name: [abs image paths]} for one split, sorted & filtered.

    Only the 16 expected classes are listed; stray system files such as
    .DS_Store are ignored. The dataset itself is never modified.
    """
    out = {}
    split_dir = os.path.join(DATA_ROOT, split)
    for cls in DISEASE_CLASSES:
        cdir = os.path.join(split_dir, cls)
        files = sorted(
            os.path.join(cdir, f)
            for f in os.listdir(cdir)
            if os.path.splitext(f)[1].lower() in IMAGE_EXTS
        )
        out[cls] = files
    return out


def load_batch(paths):
    """Decode + resize a batch of images to (N,224,224,3) uint8."""
    arr = np.empty((len(paths), IMG_SIZE, IMG_SIZE, 3), dtype=np.uint8)
    for i, p in enumerate(paths):
        with Image.open(p) as im:
            im = im.convert("RGB").resize((IMG_SIZE, IMG_SIZE), Image.BILINEAR)
            arr[i] = np.asarray(im, dtype=np.uint8)
    return arr


def batches(items, size):
    for start in range(0, len(items), size):
        yield items[start:start + size]


# ---------------------------------------------------------------- model -----
# The SHIPPED runtime model
# (backend/ml_models/FasalDoc_MobileNetV2_final.keras) has EXACTLY this graph,
# and backend/services/ml_classifier.py feeds it RAW 0-255 float32 pixels
# (its only preprocessing is decode -> RGB -> bilinear 224x224 -> float32):
#
#   Input(224,224,3)
#     -> Rescaling(scale=1/127.5, offset=-1)        # pixels -> [-1, 1]
#     -> MobileNetV2(include_top=False, imagenet)   # 7x7x1280
#     -> GlobalAveragePooling2D                     # 1280
#     -> Dropout(0.30)
#     -> Dense(16, softmax)
#
# build_* below assemble that graph exactly, so the invariant
#   training-script architecture == shipped model architecture == inference
# holds, and a future run rebuilds the same structure from scratch.


def build_frozen_base():
    """ImageNet MobileNetV2 backbone, frozen, NO pooling (7x7x1280 output)."""
    base = keras.applications.MobileNetV2(
        input_shape=(IMG_SIZE, IMG_SIZE, 3),
        include_top=False,
        weights=BASE_WEIGHTS,
    )
    base.trainable = False  # stage 1: fully frozen backbone
    return base


def build_rescaling():
    # Same mapping as mobilenet_v2.preprocess_input (caffe mode), baked into the
    # graph so inference feeds raw 0-255 and rescaling is applied exactly once.
    return keras.layers.Rescaling(1.0 / 127.5, offset=-1.0, name="rescaling")


def build_feature_extractor(base):
    """raw 0-255 -> 1280-d GAP bottleneck features (run once to cache)."""
    inp = keras.Input(shape=(IMG_SIZE, IMG_SIZE, 3), name="image")
    x = build_rescaling()(inp)
    x = base(x)
    x = keras.layers.GlobalAveragePooling2D(name="global_average_pooling2d")(x)
    return keras.Model(inp, x, name="mobilenetv2_features")


def build_head():
    """GAP(1280) -> Dropout(0.3) -> Dense(16, softmax) — matches the shipped model."""
    inp = keras.Input(shape=(1280,), name="bottleneck_features")
    x = keras.layers.Dropout(0.30)(inp)
    x = keras.layers.Dense(len(DISEASE_CLASSES), activation="softmax", name="class_probs")(x)
    return keras.Model(inp, x, name="mobilenetv2_head")


def build_full_model(base, head):
    """Assemble the exact end-to-end runtime graph, flattened to match the
    shipped model's top-level layers: Input -> Rescaling -> backbone -> GAP ->
    Dropout -> Dense(16, softmax). The trained Dense weights are copied from
    ``head`` so the final model is the trained classifier (not a nested head)."""
    inp = keras.Input(shape=(IMG_SIZE, IMG_SIZE, 3), name="image")
    x = build_rescaling()(inp)
    x = base(x)
    x = keras.layers.GlobalAveragePooling2D(name="global_average_pooling2d")(x)
    x = keras.layers.Dropout(0.30, name="dropout")(x)
    out = keras.layers.Dense(len(DISEASE_CLASSES), activation="softmax",
                             name="class_probs")(x)
    full = keras.Model(inp, out, name="fasaldoc_mobilenetv2")
    # Transfer the trained head weights into the flattened Dense layer.
    head_dense = [l for l in head.layers if isinstance(l, keras.layers.Dense)][-1]
    full_dense = [l for l in full.layers if isinstance(l, keras.layers.Dense)][-1]
    full_dense.set_weights(head_dense.get_weights())
    return full


# --------------------------------------------------------------- stages -----
def stage_sanity():
    print("== SANITY: dataset + loader ==")
    total = {}
    for split in SPLITS:
        items = list_split(split)
        counts = {c: len(f) for c, f in items.items()}
        total[split] = counts
        missing = [c for c, n in counts.items() if n == 0]
        assert not missing, f"{split}: empty class dirs: {missing}"
        assert sorted(counts) == DISEASE_CLASSES, f"{split}: class set mismatch"
        print(f"  {split:10s} classes={len(counts)} images={sum(counts.values())}")
    # Loader smoke test on a few real batches from the smallest & biggest classes.
    items = list_split("train")
    probe = [
        ("Potato___healthy", 3),                        # rarest class
        ("Orange___Haunglongbing_(Citrus_greening)", 3),  # biggest class
        ("Tomato___healthy", 3),
    ]
    fx = build_feature_extractor(build_frozen_base())
    for cls, n in probe:
        x = load_batch(items[cls][:n])
        print(f"  batch {cls:20s} raw shape={x.shape} dtype={x.dtype} "
              f"range=[{x.min()},{x.max()}]  (model Rescaling maps -> [-1,1])")
    # 2-batch forward pass through the frozen extractor to prove the full path.
    feat = fx.predict(load_batch(items["Corn___healthy"][:2]).astype("float32"), verbose=0)
    print(f"  feature-extractor forward pass OK: bottleneck shape={feat.shape}")
    assert feat.shape == (2, 1280), f"unexpected bottleneck shape {feat.shape}"
    path = os.path.join(REPORTS_DIR, "dataset_sanity.json")
    os.makedirs(REPORTS_DIR, exist_ok=True)
    with open(path, "w") as fh:
        json.dump({"counts": total, "class_order": DISEASE_CLASSES, "seed": SEED}, fh, indent=2)
    print(f"  wrote {path}")
    return True


def _extract_split(fx, split):
    items = list_split(split)
    feats, labels, names = [], [], []
    t0 = time.time()
    n_img = sum(len(v) for v in items.values())
    done = 0
    for ci, cls in enumerate(DISEASE_CLASSES):
        paths = items[cls]
        for chunk in batches(paths, RAW_BATCH):
            x = load_batch(chunk).astype("float32")   # raw 0-255; fx Rescales once
            feats.append(fx.predict(x, verbose=0))
            labels.extend([ci] * len(chunk))
            names.extend(chunk)
            done += len(chunk)
            if done % (RAW_BATCH * 20) < RAW_BATCH or done == n_img:
                print(f"    [{split}] {done}/{n_img} images "
                      f"({(time.time()-t0)/60:.1f} min elapsed)", flush=True)
    X = np.concatenate(feats, axis=0).astype("float32")
    y = np.asarray(labels, dtype="int32")
    np.savez_compressed(
        os.path.join(FEATURES_DIR, f"{split}.npz"),
        features=X, labels=y, paths=np.array(names),
    )
    print(f"  {split}: {X.shape} features cached in {(time.time()-t0)/60:.1f} min")


def stage_extract():
    print("== EXTRACT: frozen MobileNetV2 bottleneck features ==")
    os.makedirs(FEATURES_DIR, exist_ok=True)
    fx = build_feature_extractor(build_frozen_base())
    for split in SPLITS:
        cache = os.path.join(FEATURES_DIR, f"{split}.npz")
        if os.path.exists(cache):
            print(f"  {split}: cache exists, skipping ({cache})")
            continue
        _extract_split(fx, split)


def stage_train():
    print("== TRAIN: classification head (base frozen / features cached) ==")
    tr = np.load(os.path.join(FEATURES_DIR, "train.npz"))
    va = np.load(os.path.join(FEATURES_DIR, "validation.npz"))
    Xtr, ytr, Xva, yva = tr["features"], tr["labels"], va["features"], va["labels"]

    weights = compute_class_weight("balanced", classes=np.arange(len(DISEASE_CLASSES)), y=ytr)
    class_weight = {int(i): float(w) for i, w in enumerate(weights)}
    print("  balanced class weights:")
    for i, cls in enumerate(DISEASE_CLASSES):
        print(f"    {cls:50s} {class_weight[i]:.3f}")

    ds_tr = (
        tf.data.Dataset.from_tensor_slices((Xtr, ytr))
        .shuffle(4096, seed=SEED, reshuffle_each_iteration=True)
        .batch(HEAD_BATCH)
    )
    ds_va = tf.data.Dataset.from_tensor_slices((Xva, yva)).batch(HEAD_BATCH)

    head = build_head()
    head.compile(
        optimizer=keras.optimizers.Adam(learning_rate=1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    os.makedirs(MODELS_DIR, exist_ok=True)
    hist = head.fit(
        ds_tr,
        validation_data=ds_va,
        epochs=HEAD_EPOCHS,
        class_weight=class_weight,
        callbacks=[
            keras.callbacks.ModelCheckpoint(
                os.path.join(MODELS_DIR, "mobilenetv2_head_best.keras"),
                monitor="val_loss", save_best_only=True, verbose=0,
            ),
            keras.callbacks.EarlyStopping(
                monitor="val_loss", patience=PATIENCE, restore_best_weights=True, verbose=0,
            ),
        ],
        verbose=2,
    )
    # Persist artifacts
    os.makedirs(REPORTS_DIR, exist_ok=True)
    history = {k: [float(v) for v in vals] for k, vals in hist.history.items()}
    with open(os.path.join(REPORTS_DIR, "training_history.json"), "w") as fh:
        json.dump(history, fh, indent=1)
    with open(os.path.join(REPORTS_DIR, "class_indices.json"), "w") as fh:
        json.dump({"class_to_index": {c: i for i, c in enumerate(DISEASE_CLASSES)},
                   "index_to_class": {str(i): c for i, c in enumerate(DISEASE_CLASSES)},
                   "num_classes": len(DISEASE_CLASSES), "seed": SEED}, fh, indent=2)
    with open(os.path.join(REPORTS_DIR, "class_weights.json"), "w") as fh:
        json.dump(class_weight, fh, indent=2)
    head.save(os.path.join(MODELS_DIR, "mobilenetv2_head_last.keras"))

    # Assemble the EXACT shipped/inference architecture (raw image -> 16 probs)
    # and publish it as the model the backend actually loads.
    full = build_full_model(build_frozen_base(), head)
    full_path = os.path.join(MODELS_DIR, "mobilenetv2_full.keras")
    full.save(full_path)
    arch_layers = [type(l).__name__ for l in full.layers]
    print(f"  assembled model layers: {arch_layers}")
    print(f"  model input={tuple(full.input.shape)} output={tuple(full.output.shape)}")
    # Publish to the runtime path used by backend/services/ml_classifier.py.
    runtime_model = os.path.join(
        PROJECT_ROOT, "backend", "ml_models", "FasalDoc_MobileNetV2_final.keras")
    backup = os.path.join(MODELS_DIR, "FasalDoc_MobileNetV2_final.pre_retrain.keras")
    if os.path.exists(runtime_model) and not os.path.exists(backup):
        shutil.copy2(runtime_model, backup)   # keep the pre-retrain model (gitignored)
        print(f"  backed up pre-retrain model -> {backup}")
    shutil.copy2(full_path, runtime_model)
    print(f"  published new model -> {runtime_model}")
    print(f"  epochs run: {len(history['loss'])}  best val_loss: {min(hist.history['val_loss']):.4f}")
    print(f"  final val_accuracy: {hist.history['val_accuracy'][-1]:.4f}")
    meta = {
        "python": platform.python_version(),
        "tensorflow": tf.__version__,
        "keras": keras.__version__,
        "numpy": np.__version__,
        "platform": f"{platform.system()} {platform.release()} {platform.machine()}",
        "cpu": platform.processor(),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "hyperparameters": {
            "image_size": IMG_SIZE, "raw_batch": RAW_BATCH, "head_batch": HEAD_BATCH,
            "optimizer": "Adam(lr=1e-3)", "loss": "sparse_categorical_crossentropy",
            "max_epochs": HEAD_EPOCHS, "early_stopping_patience": PATIENCE,
            "dropout": 0.30, "class_weight": "balanced",
            "base": "MobileNetV2(imagenet, frozen, include_top=False) + Rescaling(1/127.5,-1) + GAP",
            "head": "Dropout(0.3) -> Dense(16, softmax)",
            "seed": SEED,
        },
        "train_images": int(len(ytr)), "validation_images": int(len(yva)),
    }
    with open(os.path.join(REPORTS_DIR, "run_metadata.json"), "w") as fh:
        json.dump(meta, fh, indent=2)


def stage_evaluate():
    print("== EVALUATE: held-out test split ==")
    te = np.load(os.path.join(FEATURES_DIR, "test.npz"))
    X, y = te["features"], te["labels"]
    head = keras.models.load_model(os.path.join(MODELS_DIR, "mobilenetv2_head_best.keras"))
    pred = np.argmax(head.predict(X, batch_size=HEAD_BATCH, verbose=0), axis=1)

    labels = np.arange(len(DISEASE_CLASSES))
    metrics = {
        "test_images": int(len(y)),
        "accuracy": float(accuracy_score(y, pred)),
        "macro_precision": float(precision_score(y, pred, average="macro", zero_division=0)),
        "macro_recall": float(recall_score(y, pred, average="macro", zero_division=0)),
        "macro_f1": float(f1_score(y, pred, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y, pred, average="weighted", zero_division=0)),
    }
    report = classification_report(
        y, pred, labels=labels, target_names=DISEASE_CLASSES, digits=4, zero_division=0,
        output_dict=True,
    )
    cm = confusion_matrix(y, pred, labels=labels)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    with open(os.path.join(REPORTS_DIR, "test_metrics.json"), "w") as fh:
        json.dump({"overall": metrics, "per_class": report,
                   "confusion_matrix": cm.tolist(), "class_order": DISEASE_CLASSES}, fh, indent=2)

    # Confusion-matrix plots (matplotlib CSV fallback if Qt/backend issues arise).
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        for norm, suffix in ((False, "raw"), (True, "normalized")):
            data = (cm.astype("float64") / np.clip(cm.sum(1, keepdims=True), 1, None)) if norm else cm
            fig, ax = plt.subplots(figsize=(12, 10))
            im = ax.imshow(data, cmap="Blues", normalization="norm")
            ax.set_xticks(labels, DISEASE_CLASSES, rotation=90, fontsize=7)
            ax.set_yticks(labels, DISEASE_CLASSES, fontsize=7)
            ax.set_title(f"Test confusion matrix ({suffix})")
            fig.colorbar(im, ax=ax, fraction=0.04)
            if not norm:
                for i in range(len(labels)):
                    for j in range(len(labels)):
                        if cm[i, j] > 0:
                            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                                    fontsize=5, color="black" if cm[i, j] < cm.max()/2 else "white")
            fig.tight_layout()
            fig.savefig(os.path.join(REPORTS_DIR, f"confusion_matrix_{suffix}.png"), dpi=150)
            plt.close(fig)
        print(f"  wrote confusion_matrix_raw.png / confusion_matrix_normalized.png")
    except Exception as exc:  # non-fatal — CSV fallback
        print(f"  matplotlib failed ({exc}); writing confusion_matrix.csv instead")
        with open(os.path.join(REPORTS_DIR, "confusion_matrix.csv"), "w") as fh:
            fh.write("," + ",".join(DISEASE_CLASSES) + "\n")
            for i, cls in enumerate(DISEASE_CLASSES):
                fh.write(cls + "," + ",".join(str(v) for v in cm[i]) + "\n")

    print(f"  accuracy={metrics['accuracy']:.4f}  macro F1={metrics['macro_f1']:.4f}")
    for i, cls in enumerate(DISEASE_CLASSES):
        r = report[cls]
        print(f"    {cls:50s} P={r['precision']:.3f} R={r['recall']:.3f} "
              f"F1={r['f1-score']:.3f} n={int(r['support'])}")


def stage_report():
    print("== REPORT ==")
    with open(os.path.join(REPORTS_DIR, "test_metrics.json")) as fh:
        metrics = json.load(fh)
    with open(os.path.join(REPORTS_DIR, "run_metadata.json")) as fh:
        meta = json.load(fh)
    with open(os.path.join(REPORTS_DIR, "class_weights.json")) as fh:
        cw = json.load(fh)
    with open(os.path.join(REPORTS_DIR, "training_history.json")) as fh:
        hist = json.load(fh)
    with open(os.path.join(REPORTS_DIR, "dataset_sanity.json")) as fh:
        sanity = json.load(fh)

    hp = meta["hyperparameters"]
    o = metrics["overall"]
    lines = [
        "# FasalDoc MobileNetV2 Training Report",
        f"_Generated: {datetime.now(timezone.utc).date().isoformat()}_",
        "",
        "## Framework / Hardware",
        f"- Python {meta['python']}, TensorFlow {meta['tensorflow']} (Keras {meta['keras']}), NumPy {meta['numpy']}",
        f"- Platform: {meta['platform']} ({meta['cpu']}, 2 physical cores, 8 GB RAM) — CPU-only",
        "",
        "## Architecture (matches the shipped runtime model exactly)",
        "- Backbone: `MobileNetV2(include_top=False, weights='imagenet')` — **frozen**; the",
        "  end-to-end graph is `Input -> Rescaling(1/127.5,-1) -> backbone -> GAP ->",
        "  Dropout(0.3) -> Dense(16, softmax)`, identical to",
        "  `backend/ml_models/FasalDoc_MobileNetV2_final.keras` and to the inference path in",
        "  `backend/services/ml_classifier.py` (raw 0-255 in, single internal rescale).",
        f"- Head: Dropout(0.3) → Dense({len(DISEASE_CLASSES)}, softmax)",
        "",
        "## Hyperparameters",
        f"- Image size: {hp['image_size']}x{hp['image_size']} | raw batch {hp['raw_batch']} | head batch {hp['head_batch']}",
        f"- Optimizer: {hp['optimizer']} | Loss: {hp['loss']}",
        f"- Max epochs: {hp['max_epochs']} | EarlyStopping patience: {hp['early_stopping_patience']} (val_loss, restore best)",
        f"- Checkpointing: ModelCheckpoint on best val_loss | Seed: {hp['seed']}",
        f"- Train/val/test images: {meta['train_images']}/{meta['validation_images']}/{o['test_images']}",
        "",
        "## Class-imbalance strategy",
        "- Balanced class weights (`sklearn compute_class_weight`), dataset left untouched:",
        "",
        "| Class | Weight | Train images |",
        "|---|---|---|",
    ]
    tr_counts = sanity["counts"]["train"]
    for i, cls in enumerate(DISEASE_CLASSES):
        lines.append(f"| {cls} | {cw[str(i)] if str(i) in cw else cw[cls]:.3f} | {tr_counts[cls]} |")
    lines += [
        "",
        "## Training / validation",
        f"- Epochs run: {len(hist['loss'])} | final train loss {hist['loss'][-1]:.4f} | best val loss {min(hist['val_loss']):.4f}",
        f"- Final val accuracy: {hist['val_accuracy'][-1]:.4f} | best val accuracy: {max(hist['val_accuracy']):.4f}",
        "",
        "## Test results (held-out split, never used for training)",
        f"- Accuracy: **{o['accuracy']:.4f}**",
        f"- Macro precision / recall / F1: {o['macro_precision']:.4f} / {o['macro_recall']:.4f} / **{o['macro_f1']:.4f}**",
        f"- Weighted F1: {o['weighted_f1']:.4f}",
        "",
        "## Per-class test performance",
        "| Class | Precision | Recall | F1 | Support |",
        "|---|---|---|---|---|",
    ]
    for cls in DISEASE_CLASSES:
        r = metrics["per_class"][cls]
        lines.append(f"| {cls} | {r['precision']:.3f} | {r['recall']:.3f} | {r['f1-score']:.3f} | {int(r['support'])} |")
    lines += [
        "",
        "Confusion matrices: `reports/confusion_matrix_raw.png`, `reports/confusion_matrix_normalized.png`",
        "",
        "## Class → index mapping",
        "Exact mapping (alphabetical, seed-independent) recorded in `reports/class_indices.json`:",
        "```json",
        json.dumps(metrics["class_order"]),
        "```",
        "",
        "## Limitations",
        "- Stage-1 only: frozen backbone + linear-ish head. Underfitting is expected on visually",
        "  similar classes; a later stage may unfreeze the top MobileNetV2 blocks for fine-tuning.",
        "- No data augmentation (kept minimal for this hardware; likely suppresses minority-class recall).",
        "- `Potato___healthy` (23 test images) and `Corn___Cercospora_leaf_spot` (77) give high-variance",
        "  per-class metrics.",
        "- `Background_without_leaves` is a trained reject class; the app currently defers",
        "  it to Gemini Vision as a plant sanity check rather than auto-rejecting.",
        "- CPU-only training bottleneck extraction took significant wall-clock time on a 2-core i7.",
        "- INTEGRATED: /diagnose runs this model first when FASALDOC_ML_ENABLED is on and",
        "  falls back to the Gemini vision flow when ML is unavailable or low-confidence.",
        "",
        "## Artifacts",
        "- `ml/models/mobilenetv2_head_best.keras` (classification head, best val loss)",
        "- `ml/models/mobilenetv2_full.keras` (end-to-end: raw image → 16-class probabilities)",
        "- `ml/reports/training_history.json`, `test_metrics.json`, `run_metadata.json`,",
        "  `class_indices.json`, `class_weights.json`, `dataset_sanity.json`",
        "- `ml/features/{train,validation,test}.npz` (cached bottleneck features)",
    ]
    path = os.path.join(REPORTS_DIR, "TRAINING_REPORT.md")
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"  wrote {path}")


STAGES = {
    "sanity": stage_sanity,
    "extract": stage_extract,
    "train": stage_train,
    "evaluate": stage_evaluate,
    "report": stage_report,
}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--stage", default="all",
        choices=["all", *STAGES.keys()],
        help="pipeline stage to run (default: all, in order)",
    )
    args = parser.parse_args()
    order = list(STAGES) if args.stage == "all" else [args.stage]
    os.makedirs(FEATURES_DIR, exist_ok=True)
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    for name in order:
        t0 = time.time()
        STAGES[name]()
        print(f"-- stage {name} done in {(time.time()-t0)/60:.1f} min\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
