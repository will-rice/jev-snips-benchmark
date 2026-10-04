"""Constants for the Jev SNIPS benchmark."""

from pathlib import Path

DATASET_REPO = "bkonkle/snips-joint-intent"
DATASET_REVISION = "3d6aa45aa00bbe841eebc5873c5a4fa8914328bc"
SPLIT = "test"
SCHEMA_SPLIT = "train"
MODEL = "jev-latest"
MAX_WORKERS = 8
RUNS = 3
MAX_GAP = 2
NONE = "none"
RESULTS_DIR = Path("results")
