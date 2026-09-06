# -*- coding: utf-8 -*-
"""Plant metadata shared by all disease records."""

PLANTS = {
    "Tomato": {
        "ur": "ٹماٹر", "sci": "Solanum lycopersicum", "category": "vegetable",
        "category_ur": "سبزی", "aliases": ["tomato"],
    },
    "Potato": {
        "ur": "آلو (بطاطہ)", "sci": "Solanum tuberosum", "category": "vegetable",
        "category_ur": "سبزی", "aliases": ["potato", "aloo"],
    },
    "Maize": {
        "ur": "مکئی", "sci": "Zea mays", "category": "cereal",
        "category_ur": "اناج", "aliases": ["corn", "maize"],
    },
    "Wheat": {
        "ur": "گندم", "sci": "Triticum aestivum", "category": "cereal",
        "category_ur": "اناج", "aliases": ["wheat"],
    },
    "Rice": {
        "ur": "دھان (چاول)", "sci": "Oryza sativa", "category": "cereal",
        "category_ur": "اناج", "aliases": ["rice", "paddy"],
    },
    "Cotton": {
        "ur": "کپاس", "sci": "Gossypium hirsutum", "category": "cash crop",
        "category_ur": "نقدی فصل", "aliases": ["cotton"],
    },
    "Chili": {
        "ur": "مرچ", "sci": "Capsicum annuum", "category": "vegetable",
        "category_ur": "سبزی", "aliases": ["chili", "chilli", "pepper"],
    },
    "Onion": {
        "ur": "پیاز", "sci": "Allium cepa", "category": "vegetable",
        "category_ur": "سبزی", "aliases": ["onion"],
    },
    "Mango": {
        "ur": "آم", "sci": "Mangifera indica", "category": "fruit",
        "category_ur": "پھل", "aliases": ["mango", "aam"],
    },
    "Citrus": {
        "ur": "سٹرس (مالٹا)", "sci": "Citrus spp.", "category": "fruit",
        "category_ur": "پھل", "aliases": ["citrus", "orange", "kinnow", "lemon", "malta"],
    },
    "Guava": {
        "ur": "امرود", "sci": "Psidium guajava", "category": "fruit",
        "category_ur": "پھل", "aliases": ["guava", "amrood"],
    },
    "Chickpea": {
        "ur": "چنا", "sci": "Cicer arietinum", "category": "legume",
        "category_ur": "دال دار فصل", "aliases": ["chickpea", "gram", "chana"],
    },
}

PLANT_SLUGS = {
    "Tomato": "tomato", "Potato": "potato", "Maize": "maize", "Wheat": "wheat",
    "Rice": "rice", "Cotton": "cotton", "Chili": "chili", "Onion": "onion",
    "Mango": "mango", "Citrus": "citrus", "Guava": "guava", "Chickpea": "chickpea",
}

# Original folder name inside "demo photos" -> canonical plant name
FOLDER_TO_PLANT = {
    "Tomato": "Tomato", "Potato": "Potato", "Maize": "Maize", "Wheat": "Wheat",
    "Rice": "Rice", "Cotton": "Cotton", "Chilli": "Chili", "Onion": "Onion",
    "Mango": "Mango", "Citrus": "Citrus", "Guava": "Guava", "Chickpea": "Chickpea",
}
