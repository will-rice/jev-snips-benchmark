"""Score predictions with the standard SNIPS metrics."""

from collections.abc import Mapping, Sequence
from statistics import mean

from seqeval.metrics import f1_score

from jevsnips.models import Prediction


def evaluate(predictions: Sequence[Prediction]) -> dict[str, float]:
    """Compute intent accuracy and, per slot scheme, slot F1 and frame accuracy.

    Slot F1 is span-level micro F1 (conlleval). A frame is correct when
    the intent and every tag match the gold utterance.

    Args:
        predictions: One prediction per evaluated utterance.

    Returns:
        Metric names to values in [0, 1].

    Raises:
        ValueError: If there are no predictions.
    """
    if not predictions:
        raise ValueError("No predictions to evaluate")
    gold_tags = [list(prediction.utterance.tags) for prediction in predictions]
    intent_correct = [
        prediction.intent == prediction.utterance.intent for prediction in predictions
    ]
    metrics = {"intent_accuracy": sum(intent_correct) / len(predictions)}
    schemes = {
        "token": [list(prediction.token.tags) for prediction in predictions],
        "span": [list(prediction.span.tags) for prediction in predictions],
    }
    for scheme, tags in schemes.items():
        metrics[f"{scheme}/slot_f1"] = float(f1_score(gold_tags, tags))
        metrics[f"{scheme}/frame_accuracy"] = sum(
            correct and gold == predicted
            for correct, gold, predicted in zip(
                intent_correct, gold_tags, tags, strict=True
            )
        ) / len(predictions)
    return metrics


def summarize(
    runs: Sequence[Mapping[str, float]],
) -> dict[str, tuple[float, float, float]]:
    """Reduce repeated runs to each metric's mean, minimum, and maximum."""
    return {
        name: (
            mean(run[name] for run in runs),
            min(run[name] for run in runs),
            max(run[name] for run in runs),
        )
        for name in runs[0]
    }
