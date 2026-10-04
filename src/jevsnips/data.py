"""Load SNIPS utterances and the per-intent slot schema."""

import csv
from pathlib import Path

from huggingface_hub import hf_hub_download

from jevsnips.config import DATASET_REPO, DATASET_REVISION, SCHEMA_SPLIT
from jevsnips.models import Utterance


def load_utterances(split: str) -> list[Utterance]:
    """Load a split as utterances with gold intents and BIO tags.

    Args:
        split: Dataset split name, the stem of a CSV file in the repo.

    Returns:
        The split's utterances in file order.
    """
    with download(split).open(newline="") as file:
        return [
            Utterance(
                tokens=tuple(row["input"].split()),
                intent=row["intent"],
                tags=tuple(row["slots"].split()),
            )
            for row in csv.DictReader(file)
        ]


def load_slot_schema() -> dict[str, list[str]]:
    """Map each intent to the slot types that occur with it in train.

    Only the intent and tag columns are read, so no train utterance is
    parsed or sent to the model.

    Returns:
        Intents in sorted order, each with its sorted slot types.
    """
    schema: dict[str, set[str]] = {}
    with download(SCHEMA_SPLIT).open(newline="") as file:
        for row in csv.DictReader(file):
            schema.setdefault(row["intent"], set()).update(
                tag[2:] for tag in row["slots"].split() if tag != "O"
            )
    return {intent: sorted(slots) for intent, slots in sorted(schema.items())}


def download(split: str) -> Path:
    """Download a split's CSV from the pinned dataset revision."""
    return Path(
        hf_hub_download(
            DATASET_REPO,
            f"{split}.csv",
            repo_type="dataset",
            revision=DATASET_REVISION,
        )
    )
