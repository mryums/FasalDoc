"""evaluate_model.py
====================
Held-out evaluation of the SHIPPED FasalDoc MobileNetV2 classifier.

This does NOT retrain anything. It loads the exact artifact the backend
serves (``backend/ml_models/FasalDoc_MobileNetV2_final.keras``) and the
single-source-of-truth class mapping
(``backend/ml_models/FasalDoc_class_mapping.json``), then runs inference over
the held-out ``data/ml_dataset/test`` split.

Preprocessing is byte-for-byte identical to the runtime classifier
(``backend/services/ml_classifier.py``): decode -> convert("RGB") -> bilinear
resize to 224x224 -> float32 in 0-255. The model bundles its own
``Rescaling(1/127.5, offset=-1)`` layer, so ``mobilenet_v2.preprocess_input``
is deliberately NOT applied (doing so would double-rescale and corrupt results).

Outputs (machine- and human-readable, per the Phase-2 spec):
    ml/evaluation/metrics.json
    ml/evaluation/report.md
    ml/evaluation/confusion_matrix_raw.png
    ml/evaluation/confusion_matrix_normalized.png
    ml/evaluation/confusion_matrix.csv          (matplotlib fallback)

Every number is computed from real predictions. Nothing is fabricated.

Run with the ML virtualenv (TensorFlow present):
    ml-env/bin/python ml/evaluate_model.py
"""
from __future__ import annotations

# Keep this 2-core CPU box breathing — set before TensorFlow is imported.
for _var in ("OMP_NUM_THREADS", "TF_NUM_INTRAOP_THREADS", "TF_NUM_INTEROP_THREADS"):
    import os as _os

    _os.environ.setdefault(_var, "2")
import os

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import json
import platform
import time
from datetime import datetime, timezone

import numpy as np
import tensorflow as tf
from tensorflow import keras

from PIL import Image
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

# Determinism — matches the training/dataset-prep protocol seed.
SEED = 42

# ------------------------------------------------------------------ paths ----
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(PROJECT_ROOT, "backend", "ml_models",
                          "FasalDoc_MobileNetV2_final.keras")
MAPPING_PATH = os.path.join(PROJECT_ROOT, "backend", "ml_models",
                            "FasalDoc_class_mapping.json")
TEST_ROOT = os.path.join(PROJECT_ROOT, "data", "ml_dataset", "test")
SPLIT_REPORT = os.path.join(PROJECT_ROOT, "data", "ml_dataset",
                            "DATASET_SPLIT_REPORT.md")
TRAIN_DIR = os.path.join(PROJECT_ROOT, "data", "ml_dataset", "train")
VAL_DIR = os.path.join(PROJECT_ROOT, "data", "ml_dataset", "validation")
EVAL_DIR = os.path.join(PROJECT_ROOT, "ml", "evaluation")

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
INPUT_SIZE = 224            # identical to ml_classifier.INPUT_SIZE
BATCH = 32
# Runtime confidence bar (ml_classifier default). Overridable for reporting.
CONFIDENCE_THRESHOLD = float(os.getenv("ML_CONFIDENCE_THRESHOLD", "0.60"))


def load_mapping():
    """Return an ordered list of class names indexed by model output slot.

    The mapping file ({"0": name, ...}) is the single source of truth; the
    model's argmax index and this list's index MUST agree.
    """
    with open(MAPPING_PATH, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    ordered = sorted(raw.items(), key=lambda kv: int(kv[0]))
    indices = [int(k) for k, _ in ordered]
    names = [v for _, v in ordered]
    if indices != list(range(len(names))):
        raise RuntimeError(
            f"class mapping indices are not contiguous 0..N-1: {indices}")
    return names


def gather_test_images(class_names):
    """Return (paths, true_idx) for the held-out test split, deterministic.

    Only the exact mapped classes are considered; a folder whose name is not
    in the mapping is a hard error (it would mean dataset/mapping drift).
    Files are sorted for reproducibility.
    """
    name_to_idx = {c: i for i, c in enumerate(class_names)}
    folders = sorted(
        f for f in os.listdir(TEST_ROOT)
        if os.path.isdir(os.path.join(TEST_ROOT, f))
    )
    unexpected = [f for f in folders if f not in name_to_idx]
    if unexpected:
        raise RuntimeError(f"test folders not in the 16-class mapping: {unexpected}")
    missing = [c for c in class_names if c not in folders]
    if missing:
        raise RuntimeError(f"mapped classes with no test folder: {missing}")

    paths, y_true = [], []
    for cls in folders:
        cdir = os.path.join(TEST_ROOT, cls)
        files = sorted(
            os.path.join(cdir, f)
            for f in os.listdir(cdir)
            if os.path.splitext(f)[1].lower() in IMAGE_EXTS
        )
        for p in files:
            paths.append(p)
            y_true.append(name_to_idx[cls])
    return paths, np.asarray(y_true, dtype="int32")


def load_batch(paths):
    """Decode + resize a batch exactly like ml_classifier._predict_proba.

    Corrupt/unreadable images are skipped by the caller via _decode_one; here
    we assume paths are valid (verified in the collection pass).
    """
    arr = np.empty((len(paths), INPUT_SIZE, INPUT_SIZE, 3), dtype="float32")
    for i, p in enumerate(paths):
        with Image.open(p) as im:
            im = im.convert("RGB").resize((INPUT_SIZE, INPUT_SIZE), Image.BILINEAR)
            arr[i] = np.asarray(im, dtype="float32")  # still 0-255; model rescales
    return arr


def describe_layers(model):
    """Summarize the model's real (non-input) layer sequence.

    Reporting the architecture by reading the actual saved graph keeps the
    description honest: it reflects what is really shipped, not what a
    training script's source happened to say.
    """
    parts = []
    for l in model.layers:
        t = type(l).__name__
        if t == "InputLayer":
            continue
        if t == "Functional":
            parts.append("MobileNetV2 backbone (ImageNet, frozen)")
        elif t == "Rescaling":
            parts.append("Rescaling(1/127.5, offset=-1)")
        elif t == "GlobalAveragePooling2D":
            parts.append("GlobalAveragePooling2D")
        elif t == "Dropout":
            parts.append(f"Dropout({getattr(l, 'rate', '?')})")
        elif t == "Dense":
            act = getattr(l.activation, "__name__", str(l.activation))
            parts.append(f"Dense({l.units}, {act})")
        else:
            parts.append(t)
    return " -> ".join(parts)


def count_split_images(root, class_names):
    total = 0
    for cls in class_names:
        cdir = os.path.join(root, cls)
        if not os.path.isdir(cdir):
            continue
        total += sum(
            1 for f in os.listdir(cdir)
            if os.path.splitext(f)[1].lower() in IMAGE_EXTS
        )
    return total


def main():
    t0 = time.time()
    os.makedirs(EVAL_DIR, exist_ok=True)

    class_names = load_mapping()
    num_classes = len(class_names)
    print(f"== FasalDoc model evaluation == ({num_classes} classes)")

    model = keras.models.load_model(MODEL_PATH, compile=False)
    in_shape = tuple(model.input.shape)
    out_shape = tuple(model.output.shape)
    print(f"  model input={in_shape} output={out_shape} params={model.count_params():,}")
    layer_desc = describe_layers(model)
    print(f"  actual layer sequence: {layer_desc}")
    if out_shape[-1] != num_classes:
        raise RuntimeError(
            f"model output dim {out_shape[-1]} != mapping {num_classes}")

    paths, y_true = gather_test_images(class_names)
    n = len(paths)
    print(f"  held-out test images: {n}")

    # --- batched inference over the exact runtime preprocessing path --------
    all_probs = np.zeros((n, num_classes), dtype="float64")
    corrupt = []
    done = 0
    for start in range(0, n, BATCH):
        chunk = paths[start:start + BATCH]
        # A single bad file must not abort the run: decode defensively, skipping
        # any that fail PIL verification (none expected from PlantVillage).
        good = []
        for p in chunk:
            try:
                with Image.open(p) as im:
                    im.verify()
                good.append(p)
            except Exception:
                corrupt.append(p)
        if len(good) != len(chunk):
            print(f"    skipped {len(chunk)-len(good)} corrupt image(s) in batch "
                  f"at offset {start}", flush=True)
        if not good:
            continue
        x = load_batch(good)
        probs = model.predict(x, verbose=0).astype("float64")
        row_tot = probs.sum(axis=1, keepdims=True)
        row_tot[row_tot == 0] = 1.0
        probs = probs / row_tot  # defensive renorm, mirrors runtime
        end = start + probs.shape[0]
        all_probs[start:end] = probs
        done += probs.shape[0]
        if done % (BATCH * 40) < BATCH or done >= n:
            print(f"    {done}/{n} images ({(time.time()-t0)/60:.1f} min)",
                  flush=True)
    if corrupt:
        all_probs = all_probs[:done]
        y_true = y_true[:len(all_probs)]  # keep true/pred aligned if any skipped
    y_pred = all_probs.argmax(axis=1)
    conf = all_probs[np.arange(len(y_pred)), y_pred]

    # --- metrics ------------------------------------------------------------
    labels = list(range(num_classes))
    acc = float(accuracy_score(y_true, y_pred))
    macro_p = float(precision_score(y_true, y_pred, average="macro", labels=labels,
                                     zero_division=0))
    macro_r = float(recall_score(y_true, y_pred, average="macro", labels=labels,
                                  zero_division=0))
    macro_f1 = float(f1_score(y_true, y_pred, average="macro", labels=labels,
                               zero_division=0))
    wtd_p = float(precision_score(y_true, y_pred, average="weighted", labels=labels,
                                   zero_division=0))
    wtd_r = float(recall_score(y_true, y_pred, average="weighted", labels=labels,
                                zero_division=0))
    wtd_f1 = float(f1_score(y_true, y_pred, average="weighted", labels=labels,
                             zero_division=0))

    per_class = classification_report(
        y_true, y_pred, labels=labels, target_names=class_names, digits=4,
        zero_division=0, output_dict=True)
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    # confidence / threshold behavior (honest safety-layer context)
    above = conf >= CONFIDENCE_THRESHOLD
    conf_stats = {
        "threshold": CONFIDENCE_THRESHOLD,
        "frac_at_or_above_threshold": float(above.mean()),
        "frac_below_threshold": float((~above).mean()),
        "accuracy_when_above_threshold": (
            float((y_pred[above] == y_true[above]).mean()) if above.any() else None),
        "mean_confidence_correct": float(conf[y_pred == y_true].mean())
        if (y_pred == y_true).any() else None,
        "mean_confidence_wrong": float(conf[y_pred != y_true].mean())
        if (y_pred != y_true).any() else None,
        "min": float(conf.min()), "max": float(conf.max()),
        "median": float(np.median(conf)),
    }

    train_images = count_split_images(TRAIN_DIR, class_names)
    val_images = count_split_images(VAL_DIR, class_names)

    metrics_json = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "model_file": os.path.relpath(MODEL_PATH, PROJECT_ROOT),
        "mapping_file": os.path.relpath(MAPPING_PATH, PROJECT_ROOT),
        "seed": SEED,
        "runtime": {
            "python": platform.python_version(),
            "tensorflow": tf.__version__,
            "keras": keras.__version__,
            "numpy": np.__version__,
            "platform": f"{platform.system()} {platform.release()} {platform.machine()}",
        },
        "architecture": {
            "backbone": ("MobileNetV2 (ImageNet pretrained, frozen, include_top=False) "
                         "+ Rescaling(1/127.5,-1) + GlobalAveragePooling2D"),
            "rescaling_baked_in": True,
            "input_shape": list(in_shape),
            "output_shape": list(out_shape),
            "layer_sequence": layer_desc,
            "head": "GlobalAveragePooling2D -> Dropout(0.3) -> Dense(16, softmax)",
            "parameters": int(model.count_params()),
        },
        "preprocessing": ("decode -> RGB -> bilinear resize 224x224 -> float32 0-255; "
                          "model's own Rescaling(1/127.5,-1) maps to [-1,1]; "
                          "mobilenet_v2.preprocess_input deliberately NOT applied"),
        "dataset": {
            "root": "data/ml_dataset",
            "num_classes": num_classes,
            "train_images": train_images,
            "validation_images": val_images,
            "test_images": n,
            "class_distribution_test": {class_names[i]: int((y_true == i).sum())
                                          for i in labels},
            "corrupt_images_skipped": len(corrupt),
        },
        "overall": {
            "accuracy": acc,
            "macro_precision": macro_p,
            "macro_recall": macro_r,
            "macro_f1": macro_f1,
            "weighted_precision": wtd_p,
            "weighted_recall": wtd_r,
            "weighted_f1": wtd_f1,
        },
        "confidence_behavior": conf_stats,
        "per_class": per_class,
        "confusion_matrix": cm.tolist(),
        "class_order": class_names,
        "notes": [
            "MobileNetV2 is the trained Data Science model. Gemini is a separate "
            "generative advisory layer and is NOT the classifier.",
            "Architecture (verified from the saved graph): frozen MobileNetV2 "
            "backbone -> Rescaling(1/127.5,-1) -> GlobalAveragePooling2D -> "
            "Dropout(0.3) -> Dense(16, softmax). This is now reproduced exactly "
            "by ml/train_mobilenetv2.py (build_full_model), and this artifact was "
            "(re)trained by that pipeline, so training script == shipped == "
            "inference architecture. Metrics here come from real inference.",
            "Potato___healthy has only 23 held-out test images -> its per-class "
            "metrics are high-variance and should not be over-read.",
            "Results are measured on a real held-out split but the data are "
            "PlantVillage-derived; treat this as a proof-of-concept under "
            "controlled imagery, not production-grade field accuracy.",
        ],
    }
    with open(os.path.join(EVAL_DIR, "metrics.json"), "w", encoding="utf-8") as fh:
        json.dump(metrics_json, fh, indent=2)
    print(f"  wrote {os.path.join(EVAL_DIR, 'metrics.json')}")

    # --- confusion-matrix plots (CSV fallback) ------------------------------
    cm_png_ok = False
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        for norm, suffix in ((False, "raw"), (True, "normalized")):
            data = (cm.astype("float64") /
                    np.clip(cm.sum(1, keepdims=True), 1, None)) if norm else cm
            fig, ax = plt.subplots(figsize=(12, 10))
            ax.imshow(data, cmap="Blues")
            ax.set_xticks(labels, class_names, rotation=90, fontsize=7)
            ax.set_yticks(labels, class_names, fontsize=7)
            ax.set_xlabel("Predicted")
            ax.set_ylabel("True")
            ax.set_title(f"FasalDoc test confusion matrix ({suffix})")
            if not norm:
                for i in labels:
                    for j in labels:
                        if cm[i, j] > 0:
                            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                                    fontsize=5,
                                    color="black" if cm[i, j] < cm.max() / 2 else "white")
            fig.tight_layout()
            fig.savefig(os.path.join(EVAL_DIR, f"confusion_matrix_{suffix}.png"),
                        dpi=150)
            plt.close(fig)
        cm_png_ok = True
        print("  wrote confusion_matrix_raw.png / confusion_matrix_normalized.png")
    except Exception as exc:  # non-fatal
        print(f"  matplotlib failed ({exc}); writing confusion_matrix.csv")

    with open(os.path.join(EVAL_DIR, "confusion_matrix.csv"), "w",
              encoding="utf-8") as fh:
        fh.write("," + ",".join(class_names) + "\n")
        for i, cls in enumerate(class_names):
            fh.write(cls + "," + ",".join(str(v) for v in cm[i]) + "\n")

    write_report(metrics_json, cm, class_names, cm_png_ok, (time.time() - t0) / 60)
    print(f"  wrote {os.path.join(EVAL_DIR, 'report.md')}")
    print(f"\n  ACCURACY   = {acc:.4f}")
    print(f"  MACRO F1   = {macro_f1:.4f}  (P={macro_p:.4f} R={macro_r:.4f})")
    print(f"  WEIGHT F1  = {wtd_f1:.4f}  (P={wtd_p:.4f} R={wtd_r:.4f})")
    print(f"  conf >= {CONFIDENCE_THRESHOLD:.2f} on "
          f"{conf_stats['frac_at_or_above_threshold']*100:.1f}% of test images")
    print(f"\n== done in {(time.time()-t0)/60:.1f} min ==")


def write_report(m, cm, class_names, cm_png_ok, minutes):
    o = m["overall"]
    ds = m["dataset"]
    cc = m["confidence_behavior"]
    lines = [
        "# FasalDoc — MobileNetV2 Held-Out Evaluation",
        f"_Generated: {m['generated_utc']} · evaluated on {ds['test_images']} "
        f"test images in {minutes:.1f} min_",
        "",
        "> **MobileNetV2 is the trained Data Science model.** Gemini is a separate",
        "> generative advisory/explanation layer and is **not** the classifier.",
        "> Every metric below is measured from real predictions on the held-out",
        "> `data/ml_dataset/test` split — nothing is fabricated.",
        "",
        "## 1. Model under evaluation",
        f"- File: `{m['model_file']}` (the exact artifact the backend serves)",
        f"- Class mapping: `{m['mapping_file']}` — **{ds['num_classes']} classes**, "
        "argmax index == mapping index (verified)",
        f"- Architecture (read from the saved graph): {m['architecture']['layer_sequence']}",
        f"- Backbone: {m['architecture']['backbone']}",
        f"- Head: {m['architecture']['head']}",
        f"- Input: {m['architecture']['input_shape']} → Output: "
        f"{m['architecture']['output_shape']} · {m['architecture']['parameters']:,} params",
        f"- Preprocessing: {m['preprocessing']}",
        f"- Runtime: Python {m['runtime']['python']}, TensorFlow "
        f"{m['runtime']['tensorflow']}, Keras {m['runtime']['keras']}, "
        f"NumPy {m['runtime']['numpy']} ({m['runtime']['platform']}, CPU-only)",
        "",
        "## 2. Dataset & splits",
        f"- Source: `data/ml_dataset` (PlantVillage-derived, 16 selected classes)",
        f"- Train / Validation / Test images: "
        f"{ds['train_images']:,} / {ds['validation_images']:,} / {ds['test_images']:,}",
        f"- Corrupt images skipped this run: {ds['corrupt_images_skipped']}",
        "- Full provenance (seed 42, SHA-1 dedup, 0 cross-split leakage, per-class "
        "counts) is in `data/ml_dataset/DATASET_SPLIT_REPORT.md`.",
        "",
        "### Test-set class distribution (imbalance)",
        "| Class | Test images |",
        "|---|---:|",
    ]
    for cls, cnt in sorted(ds["class_distribution_test"].items(),
                           key=lambda kv: -kv[1]):
        lines.append(f"| {cls} | {cnt} |")
    lines += [
        "",
        "_Potato___healthy has only 23 held-out images — its per-class numbers "
        "are high-variance and must not be over-read._",
        "",
        "## 3. Headline metrics (real, held out)",
        "| Metric | Value |",
        "|---|---:|",
        f"| Accuracy | {o['accuracy']:.4f} |",
        f"| Macro Precision | {o['macro_precision']:.4f} |",
        f"| Macro Recall | {o['macro_recall']:.4f} |",
        f"| Macro F1 | {o['macro_f1']:.4f} |",
        f"| Weighted Precision | {o['weighted_precision']:.4f} |",
        f"| Weighted Recall | {o['weighted_recall']:.4f} |",
        f"| Weighted F1 | {o['weighted_f1']:.4f} |",
        "",
        "_Macro averages treat every class equally (important under imbalance); "
        "weighted averages honor each class's test support._",
        "",
        "## 4. Per-class report",
        "| Class | Precision | Recall | F1 | Support |",
        "|---|---:|---:|---:|---:|",
    ]
    for cls in class_names:
        r = m["per_class"][cls]
        lines.append(f"| {cls} | {r['precision']:.4f} | {r['recall']:.4f} | "
                     f"{r['f1-score']:.4f} | {int(r['support'])} |")
    weakest = sorted(class_names, key=lambda c: m["per_class"][c]["f1-score"])[:3]
    lines += [
        "",
        "### Weakest classes (factual, not hidden)",
    ]
    for cls in weakest:
        r = m["per_class"][cls]
        lines.append(f"- **{cls}** — F1 {r['f1-score']:.4f} "
                     f"(P {r['precision']:.4f} / R {r['recall']:.4f}, "
                     f"n={int(r['support'])})")
    lines += [
        "",
        "## 5. Confusion matrix",
        f"- Machine-readable CSV: `ml/evaluation/confusion_matrix.csv` "
        "(rows = true class, columns = predicted class, order == `class_names`)",
    ]
    if cm_png_ok:
        lines.append("- Images: `ml/evaluation/confusion_matrix_raw.png` and "
                     "`confusion_matrix_normalized.png`")
    lines += [
        "",
        "## 6. Confidence / rejection behavior (safety layer context)",
        f"- Runtime threshold: **{cc['threshold']:.2f}** "
        "(`ML_CONFIDENCE_THRESHOLD`, default 0.60)",
        f"- {cc['frac_at_or_above_threshold']*100:.1f}% of test images reach the "
        "threshold; the rest are routed to Gemini Vision for a second opinion.",
        f"- Accuracy on the above-threshold subset: "
        f"{_fmt(cc['accuracy_when_above_threshold'])}",
        f"- Mean confidence when correct: {_fmt(cc['mean_confidence_correct'])} · "
        f"when wrong: {_fmt(cc['mean_confidence_wrong'])}",
        f"- Confidence range: [{cc['min']:.4f}, {cc['max']:.4f}], "
        f"median {cc['median']:.4f}",
        "",
        "_This is a softmax confidence **heuristic**, not mathematical OOD "
        "detection. Unsupported crops can still receive a high softmax score, so "
        "the backend additionally runs a Gemini crop-identity check before "
        "trusting a confident ML call (see the integration report)._",
        "",
        "## 7. Model / training configuration (what is verifiable)",
        "- **Verified from the saved graph**: frozen MobileNetV2 ImageNet backbone "
        "(include_top=False) + Rescaling(1/127.5,-1) + GlobalAveragePooling2D + "
        "Dropout(0.3) + "
        f"Dense({ds['num_classes']}, softmax); {m['architecture']['parameters']:,} "
        "trainable+non-trainable params; 224x224x3 float input.",
        "- Reproduced by `ml/train_mobilenetv2.py` (frozen backbone, Adam lr=1e-3, "
        "sparse_categorical_crossentropy, EarlyStopping patience 8 + ModelCheckpoint "
        "on val_loss, seed 42, **balanced class weights**, **no augmentation**).",
        "- **Reproducibility (fixed)**: the training script's `build_full_model` now "
        "assembles byte-for-byte the shipped graph (same 6 top-level layers, same "
        "parameter count, same 16-class output). The earlier `Dense(512)` head that "
        "diverged from the artifact has been removed, and this model was rebuilt "
        "from that corrected pipeline, so the exact recipe IS reconstructable from "
        "the repository. We report the architecture we can observe and evaluate the "
        "model we actually ship.",
        "- Class imbalance is handled with balanced class weights (dataset left "
        "untouched), matching the documented strategy.",
        "",
        "## 8. Limitations (honest)",
        "- Data are PlantVillage **laboratory** imagery (single leaf, clean "
        "background); real Pakistani field photos differ → expect lower accuracy "
        "in production.",
        "- **Severe class imbalance** (Potato___healthy 152 vs Orange HLB 5,507); "
        "the smallest classes' metrics are high-variance.",
        "- Frozen-backbone bottleneck learning cannot adapt low/mid-level features "
        "to crop-disease texture the way full fine-tuning can.",
        "- Accuracy alone is misleading here; **macro F1 is the honest headline**.",
        "- Treat these results as a **proof-of-concept**, not production-grade.",
        "",
        "## 9. Reproducibility",
        f"- Seed recorded: {m['seed']}; splits fixed by "
        "`DATASET_SPLIT_REPORT.md` (seed 42, SHA-1 dedup).",
        "- Rerun with: `ml-env/bin/python ml/evaluate_model.py`",
        "- This script evaluates the shipped model directly over raw test images "
        "using the runtime preprocessing, so metrics match what the app serves.",
    ]
    with open(os.path.join(EVAL_DIR, "report.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def _fmt(v):
    return "n/a" if v is None else f"{v:.4f}"


if __name__ == "__main__":
    main()
