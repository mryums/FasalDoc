"""ml_classifier.py
===================
MobileNetV2 image-classification service for FasalDoc (trained model,
NOT retrained here).

The saved model (``backend/ml_models/FasalDoc_MobileNetV2_final.keras``)
was trained with Keras 3 and already contains the full inference graph:

    Input (224, 224, 3) float32, raw 0-255 pixels
      -> Rescaling(scale=1/127.5, offset=-1)   # pixels -> [-1, 1]
      -> frozen MobileNetV2 backbone + pooling
      -> Dense(16, activation='softmax')

Because the ``Rescaling`` layer is part of the model, incoming images must
NOT be passed through ``mobilenet_v2.preprocess_input()`` again — doing so
would double-rescale the pixels and silently corrupt every prediction.
The ONLY preprocessing performed here is exactly what the training loader
did: decode -> convert("RGB") -> bilinear resize to 224x224 -> float32.

TensorFlow is imported lazily inside :meth:`MLClassifier._ensure_loaded`
so backends running in environments without TensorFlow (e.g. the Python
3.13 .venv on an Intel Mac, where no x86 TF wheel exists) simply see the
classifier as "unavailable" and the caller falls back to the existing
Gemini vision diagnosis path.

The model and the class mapping are each loaded exactly ONCE per process
(lazy, thread-safe singleton); per-request work is inference only.
"""
from __future__ import annotations

import io
import json
import logging
import os
import threading
from typing import Any, Dict, List, Optional

logger = logging.getLogger("fasaldoc.ml_classifier")

_ML_MODELS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "ml_models")
)
MODEL_PATH = os.path.join(_ML_MODELS_DIR, "FasalDoc_MobileNetV2_final.keras")
CLASS_MAPPING_PATH = os.path.join(_ML_MODELS_DIR, "FasalDoc_class_mapping.json")

# Must match the input shape the saved model was trained with.
INPUT_SIZE = 224

# The trained reject class for "no leaf / no plant in frame".
BACKGROUND_CLASS = "Background_without_leaves"

# Conservative safety threshold, mirroring the app-wide behavior
# (ai_pipeline.CONFIDENCE_THRESHOLD = 60, gemini_provider.CONFIDENCE_THRESHOLD
# = 0.60). Overridable via env for experimentation; 0.60 is the default.
CONFIDENCE_THRESHOLD = float(os.getenv("ML_CONFIDENCE_THRESHOLD", "0.60"))

# Result status values returned by MLClassifier.predict().
STATUS_OK = "ok"
STATUS_UNAVAILABLE = "unavailable"  # TF missing / model failed to load
STATUS_ERROR = "error"              # model loaded but this image failed


def ml_enabled() -> bool:
    """Ops kill-switch: FASALDOC_ML_ENABLED=0|false|off bypasses the
    classifier entirely so the backend behaves exactly like the previous
    Gemini-vision-only flow (also keeps unit tests hermetic by default)."""
    return os.getenv("FASALDOC_ML_ENABLED", "1").strip().lower() not in {
        "0", "false", "off", "no",
    }


def format_display_name(class_name: str) -> str:
    """Turn a raw PlantVillage-style label into a farmer-facing one.

    "Tomato___Early_blight"                  -> "Tomato Early Blight"
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus" -> "Tomato Yellow Leaf Curl Virus"
    "Corn___Spider_mites Two-spotted_spider_mite"
                                             -> "Corn Spider Mites Two Spotted Spider Mite"
    """
    words: List[str] = []
    for part in class_name.replace("___", "|").replace("_", " ").split("|"):
        for word in part.split():
            if word.lower() == "tomato" and words and words[-1].lower() == "tomato":
                continue  # collapse the duplicated crop prefix
            words.append(word.capitalize())
    return " ".join(words)


class MLClassifier:
    """Lazily-loaded singleton wrapper around the trained MobileNetV2 model."""

    def __init__(
        self,
        model_path: str = MODEL_PATH,
        mapping_path: str = CLASS_MAPPING_PATH,
    ):
        self._model_path = model_path
        self._mapping_path = mapping_path
        self._model: Optional[Any] = None
        self._class_names: Optional[List[str]] = None
        self._lock = threading.Lock()
        self._status = "not_loaded"
        self._error: Optional[str] = None

    # -- loading ----------------------------------------------------------

    @property
    def status(self) -> str:
        return self._status

    @property
    def error(self) -> Optional[str]:
        return self._error

    def _ensure_loaded(self) -> bool:
        """Load model + class mapping once, on first use. Never raises."""
        if self._model is not None:
            return True
        if self._status == STATUS_UNAVAILABLE:
            return False
        with self._lock:
            if self._model is not None:  # another thread won the race
                return True
            try:
                if not os.path.exists(self._model_path):
                    raise FileNotFoundError(f"model file not found: {self._model_path}")
                if not os.path.exists(self._mapping_path):
                    raise FileNotFoundError(
                        f"class mapping not found: {self._mapping_path}"
                    )

                with open(self._mapping_path, "r", encoding="utf-8") as fh:
                    raw_mapping = json.load(fh)
                # {"0": "Class name", ...} -> ordered list indexed by int key.
                ordered = sorted(raw_mapping.items(), key=lambda kv: int(kv[0]))
                class_names = [name for _, name in ordered]

                # Keep the 2-core Intel Mac sane: cap TF threads BEFORE the
                # import (setting them afterwards has no effect).
                for _var in (
                    "OMP_NUM_THREADS",
                    "TF_NUM_INTRAOP_THREADS",
                    "TF_NUM_INTEROP_THREADS",
                ):
                    os.environ.setdefault(_var, "2")
                os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

                from tensorflow import keras  # lazy: absent in the py3.13 .venv

                logger.info("Loading MobileNetV2 from %s ...", self._model_path)
                # compiled=False: we only run inference, never re-train.
                model = keras.models.load_model(
                    self._model_path, compile=False
                )
                if model.count_params() == 0:
                    raise RuntimeError("loaded model has no weights")

                self._model = model
                self._class_names = class_names
                self._status = "ready"
                self._error = None
                logger.info(
                    "MobileNetV2 ready: %d classes, input %s",
                    len(class_names),
                    model.input.shape,
                )
                return True
            except Exception as exc:  # noqa: BLE001 - any load failure => fallback
                self._status = STATUS_UNAVAILABLE
                self._error = str(exc)
                logger.warning(
                    "MobileNetV2 unavailable (%s); callers should fall back "
                    "to the Gemini vision path.",
                    exc,
                )
                return False

    # -- inference ----------------------------------------------------------

    def predict(self, image_bytes: bytes) -> Dict[str, Any]:
        """Classify raw uploaded image bytes.

        Returns a dict shaped like:
            {
                "status": "ok" | "unavailable" | "error",
                "class_name": str | None,      # raw label from the mapping
                "display_name": str | None,    # farmer-facing label
                "confidence": float,           # softmax probability of argmax
                "threshold": float,            # confidence bar used app-wide
                "error": str | None,           # only set when status != ok
            }
        Never raises: callers treat "unavailable"/"error" as "fall back to
        the previous Gemini-only diagnosis flow".
        """
        result: Dict[str, Any] = {
            "status": STATUS_ERROR,
            "class_name": None,
            "display_name": None,
            "confidence": 0.0,
            "threshold": CONFIDENCE_THRESHOLD,
            "error": None,
        }
        if not ml_enabled():
            result["status"] = STATUS_UNAVAILABLE
            result["error"] = "MobileNetV2 disabled via FASALDOC_ML_ENABLED"
            return result
        if not self._ensure_loaded():
            result["status"] = STATUS_UNAVAILABLE
            result["error"] = self._error
            return result

        try:
            probs = self._predict_proba(image_bytes)
        except Exception as exc:  # noqa: BLE001 - bad/corrupt image bytes etc.
            logger.warning("MobileNetV2 prediction failed: %s", exc)
            result["error"] = f"MobileNetV2 prediction failed: {exc}"
            return result

        idx = int(probs.argmax())
        result.update(
            {
                "status": STATUS_OK,
                "class_name": self._class_names[idx],
                "display_name": format_display_name(self._class_names[idx]),
                "confidence": float(probs[idx]),
                "error": None,
            }
        )
        return result

    def _predict_proba(self, image_bytes: bytes):
        """Decode + resize + run the softmax model. Returns 1-D numpy probs."""
        import numpy as np
        from PIL import Image

        with Image.open(io.BytesIO(image_bytes)) as img:
            # Exactly the training loader: RGB convert + bilinear 224x224.
            img = img.convert("RGB").resize(
                (INPUT_SIZE, INPUT_SIZE), Image.BILINEAR
            )
            arr = np.asarray(img, dtype="float32")  # still 0-255; the model's
            # own Rescaling layer maps it to [-1, 1] — no preprocess_input!

        with self._lock:
            probs = self._model.predict(arr[None, ...], verbose=0)[0]

        probs = np.asarray(probs, dtype="float64")
        total = float(probs.sum())
        if total > 0:  # defensive renormalization of the softmax output
            probs = probs / total
        return probs


_classifier: Optional[MLClassifier] = None
_classifier_factory_lock = threading.Lock()


def get_classifier() -> MLClassifier:
    """Process-wide lazy singleton (model stays resident after first load)."""
    global _classifier
    if _classifier is None:
        with _classifier_factory_lock:
            if _classifier is None:
                _classifier = MLClassifier()
    return _classifier


def reset_classifier() -> None:
    """Drop the cached classifier. Intended for tests / runtime reconfig."""
    global _classifier
    _classifier = None
