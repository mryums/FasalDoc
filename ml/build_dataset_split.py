"""build_dataset_split.py
=========================
Reproducible 16-class data-preparation pipeline for FasalDoc (Phase-2 PHASE C).

This is the deterministic builder that ``data/ml_dataset/DATASET_SPLIT_REPORT.md``
referenced but that was never committed to the repo. It reads the raw New
PlantVillage images under::

    data/plantvillage_raw/Plant_leave_diseases_dataset_without_augmentation/

and produces a stratified train/validation/test split of EXACTLY the 16
project classes (matching ``backend/ml_models/FasalDoc_class_mapping.json``).

Guarantees / requirements implemented:
    1.  Reads the intended 16 classes only (hard error on any other folder).
    2.  Validates labels against the single-source-of-truth mapping.
    3.  Detects corrupted images (PIL verify) and excludes them.
    4.  Detects exact duplicates via SHA-1 content hashing.
    5.  Prevents data leakage: every duplicate group is kept ENTIRELY within a
        single split, so no identical image appears in two splits.
    6.  Deterministic splitting: seeded RNG (seed 42), per class.
    7.  Stratified 70 / 15 / 15 by class.
    8.  Reports class distribution.
    9.  Surfaces class imbalance in the manifest (does not silently resample).
    12. Saves a machine-readable manifest (``ml/dataset_manifest.json``).

SAFETY: this script NEVER writes into ``data/plantvillage_raw`` (read only) and
NEVER overwrites the existing ``data/ml_dataset`` split unless you explicitly
pass ``--build <dir>`` to a fresh directory. The default mode is read-only
verification + manifest generation of the on-disk ``data/ml_dataset``.

Augmentation note (honesty): the *shipped* model was trained WITHOUT image
augmentation (see ``ml/evaluation/report.md``). This builder only prepares
splits; it does not fabricate or augment images. Any augmentation is a
training-time concern, kept separate from the immutable split here.

Usage:
    ml-env/bin/python ml/build_dataset_split.py                 # verify + manifest
    ml-env/bin/python ml/build_dataset_split.py --build /tmp/x  # also copy a fresh split
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import shutil
from collections import defaultdict
from datetime import datetime, timezone

from PIL import Image

# ----------------------------------------------------------------- config ----
SEED = 42
RATIOS = (0.70, 0.15, 0.15)          # train / validation / test
SPLIT_NAMES = ("train", "validation", "test")
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_ROOT = os.path.join(
    PROJECT_ROOT, "data", "plantvillage_raw",
    "Plant_leave_diseases_dataset_without_augmentation",
)
EXISTING_DATASET = os.path.join(PROJECT_ROOT, "data", "ml_dataset")
MAPPING_PATH = os.path.join(
    PROJECT_ROOT, "backend", "ml_models", "FasalDoc_class_mapping.json"
)
MANIFEST_PATH = os.path.join(PROJECT_ROOT, "ml", "dataset_manifest.json")

# The 16 classes are defined ONCE, in the mapping; never hardcode a second list.
def load_class_names():
    with open(MAPPING_PATH, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    ordered = sorted(raw.items(), key=lambda kv: int(kv[0]))
    idxs = [int(k) for k, _ in ordered]
    names = [v for _, v in ordered]
    if idxs != list(range(16)):
        raise RuntimeError(f"mapping must be 16 contiguous classes, got {idxs}")
    return names


def sha1_file(path, chunk=1 << 20):
    h = hashlib.sha1()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def list_images(class_dir):
    return sorted(
        os.path.join(class_dir, f)
        for f in os.listdir(class_dir)
        if os.path.splitext(f)[1].lower() in IMAGE_EXTS
    )


def validate_and_group(paths):
    """Return (corrupt_paths, groups) where groups maps sha1 -> [paths].

    A 'group' is all files with identical content (dedup unit). Corrupt files
    (fail PIL verify) are dropped and reported.
    """
    corrupt, groups = [], defaultdict(list)
    for p in paths:
        try:
            with Image.open(p) as im:
                im.verify()
        except Exception:
            corrupt.append(p)
            continue
        groups[sha1_file(p)].append(p)
    return corrupt, groups


def build_class_split(group_sizes, seed_tag):
    """group_sizes: list of (sha1, size). Return {split: [sha1,...]}.

    Deterministic: sort by sha1 then shuffle with a class-seeded RNG, then fill
    train/validation to their rounded image targets keeping each group whole;
    the remainder is the test split.
    """
    n_total = sum(sz for _, sz in group_sizes)
    target = {
        "train": int(round(n_total * RATIOS[0])),
        "validation": int(round(n_total * RATIOS[1])),
    }
    rng = random.Random(seed_tag)
    items = sorted(group_sizes)          # deterministic base order (sha1)
    rng.shuffle(items)
    assign = {s: [] for s in SPLIT_NAMES}
    filled = {s: 0 for s in SPLIT_NAMES}
    order_splits = ["train", "validation", "test"]
    s_i = 0
    for sha1, sz in items:
        # advance to the next split once the current one has met its target
        while s_i < 2 and filled[order_splits[s_i]] >= target[order_splits[s_i]]:
            s_i += 1
        sp = order_splits[s_i]
        assign[sp].append(sha1)
        filled[sp] += sz
    return assign, filled, n_total


# ------------------------------------------------------------- builder -------
def plan_and_report(class_names):
    """Compute the deterministic planned split for every class from raw.

    The raw New PlantVillage source contains MORE than the 16 target classes;
    per the spec we READ ONLY the intended 16 and ignore the rest. Returns
    (planned, stats) with per-class train/val/test image counts,
    duplicate-group and corrupt information. Read-only (no copying).
    """
    missing = [c for c in class_names
               if not os.path.isdir(os.path.join(SRC_ROOT, c))]
    if missing:
        raise RuntimeError(f"raw source is missing required classes: {missing}")
    planned, stats = {}, {}
    for cls in class_names:
        cdir = os.path.join(SRC_ROOT, cls)
        paths = list_images(cdir)
        corrupt, groups = validate_and_group(paths)
        group_sizes = [(sha1, len(members)) for sha1, members in groups.items()]
        assign, filled, n_total = build_class_split(group_sizes, f"{SEED}:{cls}")
        planned[cls] = {s: assign[s] for s in SPLIT_NAMES}
        dup_groups = {k: v for k, v in groups.items() if len(v) > 1}
        stats[cls] = {
            "raw_images": len(paths),
            "corrupt": len(corrupt),
            "unique_sha1": len(groups),
            "duplicate_groups": len(dup_groups),
            "extra_copies": sum(len(v) - 1 for v in dup_groups.values()),
            "train": filled["train"], "validation": filled["validation"],
            "test": filled["test"],
        }
    return planned, stats


# -------------------------------------------------- existing-split verify ----
def verify_existing(class_names):
    """Independently verify the on-disk data/ml_dataset split.

    Confirms: (a) per-class/per-split counts, (b) NO sha1 appears in more than
    one split (no cross-split leakage/duplication), (c) any corrupt images.
    Read-only.
    """
    per_class = {c: {s: 0 for s in SPLIT_NAMES} for c in class_names}
    hash_to_splits = defaultdict(set)
    corrupt_total = 0
    for split in SPLIT_NAMES:
        sdir = os.path.join(EXISTING_DATASET, split)
        if not os.path.isdir(sdir):
            raise RuntimeError(f"missing split dir: {sdir}")
        folders = sorted(os.listdir(sdir))
        unexpected = [f for f in folders if f not in class_names]
        if unexpected:
            raise RuntimeError(f"{split}: folders outside the 16 classes: {unexpected}")
        for cls in folders:
            for p in list_images(os.path.join(sdir, cls)):
                try:
                    with Image.open(p) as im:
                        im.verify()
                except Exception:
                    corrupt_total += 1
                    continue
                per_class[cls][split] += 1
                hash_to_splits[sha1_file(p)].add(split)
    cross_split_dupes = {h: s for h, s in hash_to_splits.items() if len(s) > 1}
    return per_class, cross_split_dupes, corrupt_total


def write_manifest(class_names, planned_stats, existing_per_class,
                   cross_split_dupes, corrupt_existing, planned_totals):
    per_class = {}
    for cls in class_names:
        e = existing_per_class[cls]
        p = planned_stats[cls]
        per_class[cls] = {
            "crop": cls.split("___")[0],
            "raw_images": p["raw_images"],
            "existing_split": e,
            "existing_total": sum(e.values()),
            "builder_planned_split": {
                "train": p["train"], "validation": p["validation"], "test": p["test"]},
            "duplicate_groups_in_raw": p["duplicate_groups"],
            "corrupt_in_raw": p["corrupt"],
        }
    totals = {s: sum(existing_per_class[c][s] for c in class_names)
              for s in SPLIT_NAMES}
    manifest = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "FasalDoc Phase-2 16-class image-classification split manifest",
        "source": os.path.relpath(SRC_ROOT, PROJECT_ROOT),
        "dataset": os.path.relpath(EXISTING_DATASET, PROJECT_ROOT),
        "single_source_of_truth": os.path.relpath(MAPPING_PATH, PROJECT_ROOT),
        "num_classes": len(class_names),
        "seed": SEED,
        "split_ratios": dict(zip(SPLIT_NAMES, RATIOS)),
        "duplicate_policy": "SHA-1 content hash; every duplicate group kept "
                            "entirely within one split",
        "class_order": class_names,
        "totals_existing": totals,
        "total_existing_images": sum(totals.values()),
        "totals_builder_planned": planned_totals,
        "cross_split_duplicate_sha1": len(cross_split_dupes),
        "corrupt_images_in_existing_split": corrupt_existing,
        "augmentation": "none (documented; the shipped model was trained "
                        "without augmentation)",
        "per_class": per_class,
    }
    with open(MANIFEST_PATH, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    return manifest


def do_build(class_names, planned, out_dir):
    """Copy the deterministic planned split into out_dir (fresh). Never touches
    data/ml_dataset. Refuses a non-empty target."""
    if os.path.isdir(out_dir) and os.listdir(out_dir):
        raise RuntimeError(f"refusing to build into non-empty dir: {out_dir}")
    for split in SPLIT_NAMES:
        for cls in class_names:
            os.makedirs(os.path.join(out_dir, split, cls), exist_ok=True)
    src_index = {}
    for cls in class_names:
        for p in list_images(os.path.join(SRC_ROOT, cls)):
            src_index[p] = cls
    for cls in class_names:
        # rebuild absolute paths from sha1 groups by scanning raw again
        groups = defaultdict(list)
        for p in list_images(os.path.join(SRC_ROOT, cls)):
            groups[sha1_file(p)].append(p)
        for split in SPLIT_NAMES:
            for sha1 in planned[cls][split]:
                for member in groups[sha1]:
                    dst = os.path.join(out_dir, split, cls, os.path.basename(member))
                    shutil.copy2(member, dst)
    print(f"  built fresh split under {out_dir}")


def main():
    ap = argparse.ArgumentParser(description="FasalDoc 16-class split builder")
    ap.add_argument("--build", metavar="DIR", nargs="?", const="__AUTO__",
                    help="also copy the deterministic split into DIR (a fresh "
                         "directory; never overwrites data/ml_dataset)")
    args = ap.parse_args()

    class_names = load_class_names()
    print("== FasalDoc reproducible data-prep (Phase-2 PHASE C) ==")
    print(f"  {len(class_names)} classes (from mapping), seed {SEED}, "
          f"ratios {RATIOS}")

    planned, planned_stats = plan_and_report(class_names)
    planned_totals = {
        s: sum(planned_stats[c][s] for c in class_names) for s in SPLIT_NAMES
    }

    existing_per_class, cross_split_dupes, corrupt_existing = verify_existing(class_names)
    existing_totals = {
        s: sum(existing_per_class[c][s] for c in class_names) for s in SPLIT_NAMES
    }

    print("\n  per-class: EXISTING on-disk split  vs  BUILDER deterministic plan")
    mismatch = 0
    for cls in class_names:
        e, p = existing_per_class[cls], planned_stats[cls]
        tag = "" if (e["train"], e["validation"], e["test"]) == \
            (p["train"], p["validation"], p["test"]) else "  <-- differs"
        if tag:
            mismatch += 1
        print(f"    {cls:50s} "
              f"ex {e['train']:5d}/{e['validation']:4d}/{e['test']:4d}  "
              f"plan {p['train']:5d}/{p['validation']:4d}/{p['test']:4d}{tag}")

    print(f"\n  existing totals : {existing_totals} "
          f"(sum {sum(existing_totals.values())})")
    print(f"  builder totals  : {planned_totals} "
          f"(sum {sum(planned_totals.values())})")
    print(f"  cross-split duplicate SHA-1s in existing split : {len(cross_split_dupes)}")
    print(f"  corrupt images in existing split : {corrupt_existing}")
    print(f"  per-class count mismatches (existing vs builder) : {mismatch}")

    manifest = write_manifest(class_names, planned_stats, existing_per_class,
                              cross_split_dupes, corrupt_existing, planned_totals)
    print(f"\n  wrote {os.path.relpath(MANIFEST_PATH, PROJECT_ROOT)}")

    if args.build:
        out_dir = os.path.join(PROJECT_ROOT, "ml", "_split_build") \
            if args.build == "__AUTO__" else args.build
        print(f"\n== BUILD -> {out_dir} ==")
        do_build(class_names, planned, out_dir)


if __name__ == "__main__":
    main()
