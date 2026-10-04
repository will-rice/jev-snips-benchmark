"""Evaluate Jev zero-shot on the SNIPS test set."""

import argparse
import logging
from pathlib import Path

import wandb
from dotenv import load_dotenv
from tqdm.contrib.concurrent import thread_map
from typesafe_sdk import TypeSafeClient

from jevsnips.config import (
    DATASET_REPO,
    DATASET_REVISION,
    MAX_WORKERS,
    MODEL,
    RESULTS_DIR,
    SPLIT,
    WANDB_PROJECT,
)
from jevsnips.data import load_slot_schema, load_utterances
from jevsnips.jev import predict
from jevsnips.metrics import evaluate


def main() -> None:
    """Predict every utterance, save the records, and log the metrics."""
    logging.basicConfig(level=logging.INFO)
    for noisy in ("httpx2", "typesafe_sdk"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--limit", type=int, help="Evaluate only the first N utterances."
    )
    args = parser.parse_args()
    path = results_path(args.limit)
    load_dotenv()

    schema = load_slot_schema()
    utterances = load_utterances(SPLIT)[: args.limit]
    run = wandb.init(
        project=WANDB_PROJECT,
        config={
            "model": MODEL,
            "dataset": DATASET_REPO,
            "revision": DATASET_REVISION,
            "split": SPLIT,
            "utterances": len(utterances),
        },
    )
    with TypeSafeClient() as client:
        predictions = thread_map(
            lambda utterance: predict(client, utterance, schema),
            utterances,
            max_workers=MAX_WORKERS,
        )

    RESULTS_DIR.mkdir(exist_ok=True)
    path.write_text(
        "".join(prediction.model_dump_json() + "\n" for prediction in predictions)
    )

    summary = evaluate(predictions) | {
        "intent/input_tokens": sum(p.intent_input_tokens for p in predictions),
        "token/input_tokens": sum(p.token.input_tokens for p in predictions),
        "span/input_tokens": sum(p.span.input_tokens for p in predictions),
    }
    versions = sorted({prediction.model for prediction in predictions})
    run.summary.update(summary | {"model_versions": versions})
    run.finish()
    for name, value in summary.items():
        logging.info("%s: %s", name, value)
    logging.info("Model versions: %s", versions)
    logging.info("Wrote %d predictions to %s", len(predictions), path)


def results_path(limit: int | None) -> Path:
    """Return where a run saves its predictions.

    A limited run gets its own file so it cannot overwrite a full run.

    Raises:
        ValueError: If the limit is not positive.
    """
    if limit is None:
        return RESULTS_DIR / f"{SPLIT}.jsonl"
    if limit < 1:
        raise ValueError(f"--limit must be positive, got {limit}")
    return RESULTS_DIR / f"{SPLIT}-first{limit}.jsonl"


if __name__ == "__main__":
    main()
