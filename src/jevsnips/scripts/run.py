"""Evaluate Jev zero-shot on the SNIPS test set."""

import argparse
import logging
from pathlib import Path
from typing import get_args

from dotenv import load_dotenv
from tqdm.contrib.concurrent import thread_map
from typesafe_sdk import TypeSafeClient

from jevsnips.config import MAX_WORKERS, RESULTS_DIR, RUNS, SPLIT
from jevsnips.data import load_slot_schema, load_utterances
from jevsnips.jev import predict
from jevsnips.metrics import evaluate, summarize
from jevsnips.models import Condition


def main() -> None:
    """Run one condition several times, save each run, and log the metrics."""
    logging.basicConfig(level=logging.INFO)
    for noisy in ("httpx2", "typesafe_sdk"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "condition",
        choices=get_args(Condition),
        help="Offer labels by name only, or with descriptions.",
    )
    parser.add_argument(
        "--limit", type=int, help="Evaluate only the first N utterances."
    )
    args = parser.parse_args()
    paths = [
        results_path(args.condition, run, args.limit) for run in range(1, RUNS + 1)
    ]
    load_dotenv()

    schema = load_slot_schema()
    utterances = load_utterances(SPLIT)[: args.limit]
    RESULTS_DIR.mkdir(exist_ok=True)
    runs = []
    with TypeSafeClient() as client:
        for path in paths:
            predictions = thread_map(
                lambda utterance: predict(client, utterance, schema, args.condition),
                utterances,
                max_workers=MAX_WORKERS,
            )
            path.write_text(
                "".join(
                    prediction.model_dump_json(by_alias=True) + "\n"
                    for prediction in predictions
                )
            )
            versions = sorted({prediction.model for prediction in predictions})
            logging.info("Wrote %d predictions to %s", len(predictions), path)
            logging.info("Model versions: %s", versions)
            runs.append(
                evaluate(predictions)
                | {
                    "intent/input_tokens": sum(
                        p.intent_input_tokens for p in predictions
                    ),
                    "token/input_tokens": sum(
                        p.token.input_tokens for p in predictions
                    ),
                    "span/input_tokens": sum(p.span.input_tokens for p in predictions),
                }
            )

    for name, (mean, low, high) in summarize(runs).items():
        logging.info("%s: mean %.4f, range %.4f to %.4f", name, mean, low, high)


def results_path(condition: Condition, run: int, limit: int | None) -> Path:
    """Return where one run of a condition saves its predictions.

    A limited run gets its own file so it cannot overwrite a full run.

    Raises:
        ValueError: If the limit is not positive.
    """
    stem = f"{SPLIT}-{condition}-run{run}"
    if limit is None:
        return RESULTS_DIR / f"{stem}.jsonl"
    if limit < 1:
        raise ValueError(f"--limit must be positive, got {limit}")
    return RESULTS_DIR / f"{stem}-first{limit}.jsonl"


if __name__ == "__main__":
    main()
