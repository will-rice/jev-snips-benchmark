"""Compare the saved runs of every condition."""

import logging
from typing import get_args

from seqeval.metrics import classification_report

from jevsnips.config import RUNS
from jevsnips.metrics import evaluate, summarize
from jevsnips.models import Condition, Prediction
from jevsnips.scripts.run import results_path


def main() -> None:
    """Log each condition's metrics, overall, intent-matched, and per slot."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    conditions = get_args(Condition)
    runs = {
        condition: [
            [
                Prediction.model_validate_json(line)
                for line in results_path(condition, run, None).read_text().splitlines()
            ]
            for run in range(1, RUNS + 1)
        ]
        for condition in conditions
    }

    for condition in conditions:
        logging.info("== %s: all utterances ==", condition)
        log_summary([evaluate(predictions) for predictions in runs[condition]])

    # Describing intents changes the predicted intent and so the slots offered.
    # Restricting to utterances every condition got right isolates the slots.
    for condition in conditions:
        logging.info("== %s: utterances with the intent right everywhere ==", condition)
        log_summary(
            [
                evaluate(
                    [
                        prediction
                        for index, prediction in enumerate(runs[condition][run])
                        if all(
                            runs[other][run][index].intent
                            == runs[other][run][index].utterance.intent
                            for other in conditions
                        )
                    ]
                )
                for run in range(RUNS)
            ]
        )

    logging.info("== slot F1 per slot type ==")
    per_slot = {
        condition: summarize([slot_f1(predictions) for predictions in runs[condition]])
        for condition in conditions
    }
    for slot in sorted(per_slot[conditions[0]]):
        logging.info(
            "%-28s %s",
            slot,
            "  ".join(
                f"{condition} {per_slot[condition][slot][0]:.3f}"
                for condition in conditions
            ),
        )


def log_summary(metrics: list[dict[str, float]]) -> None:
    """Log each metric's mean and range over runs."""
    for name, (mean, low, high) in summarize(metrics).items():
        logging.info("%-22s mean %.4f, range %.4f to %.4f", name, mean, low, high)


def slot_f1(predictions: list[Prediction]) -> dict[str, float]:
    """Return span-level F1 for each slot type."""
    report = classification_report(
        [list(prediction.utterance.tags) for prediction in predictions],
        [list(prediction.slots.tags) for prediction in predictions],
        output_dict=True,
        zero_division=0,
    )
    return {
        slot: scores["f1-score"]
        for slot, scores in report.items()
        if not slot.endswith(" avg")
    }


if __name__ == "__main__":
    main()
