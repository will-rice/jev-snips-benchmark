"""Tests for benchmark metrics on hand-built predictions."""

import pytest

from jevsnips.metrics import evaluate, summarize
from jevsnips.models import Prediction, SlotPrediction, Utterance


def prediction(
    utterance: Utterance,
    intent: str,
    token_tags: tuple[str, ...],
    span_tags: tuple[str, ...],
) -> Prediction:
    """Build a prediction with only the fields metrics read."""
    return Prediction(
        utterance=utterance,
        condition="names",
        intent=intent,
        intent_probabilities={intent: 1.0},
        intent_input_tokens=1,
        token=SlotPrediction(tags=token_tags, probabilities={}, input_tokens=1),
        span=SlotPrediction(tags=span_tags, probabilities={}, input_tokens=1),
        model="jev-1.13.0",
    )


def test_evaluate_scores_intent_slots_and_frames_per_scheme() -> None:
    """Four gold spans over two utterances give hand-computed scores."""
    play = Utterance(
        tokens=("play", "sabrina", "salerno"),
        intent="PlayMusic",
        tags=("O", "B-artist", "I-artist"),
    )
    rate = Utterance(
        tokens=("rate", "this", "book", "five"),
        intent="RateBook",
        tags=("O", "B-object_select", "B-object_type", "B-rating_value"),
    )
    metrics = evaluate(
        [
            prediction(play, "PlayMusic", play.tags, ("O", "B-artist", "O")),
            prediction(
                rate, "SearchCreativeWork", ("O", "O", "B-object_type", "O"), rate.tags
            ),
        ]
    )
    assert metrics["intent_accuracy"] == 0.5
    # Token: 2 predicted spans, both correct, of 4 gold: P=1, R=0.5.
    assert metrics["token/slot_f1"] == pytest.approx(2 / 3)
    assert metrics["token/frame_accuracy"] == 0.5
    # Span: 4 predicted spans, 3 correct, of 4 gold: P=R=0.75.
    assert metrics["span/slot_f1"] == pytest.approx(0.75)
    # The exact span tags belong to the utterance with the wrong intent.
    assert metrics["span/frame_accuracy"] == 0.0


def test_evaluate_rejects_an_empty_run() -> None:
    """Scoring nothing is an error, not a division by zero."""
    with pytest.raises(ValueError, match="No predictions"):
        evaluate([])


def test_summarize_gives_mean_and_range_per_metric() -> None:
    """Repeated runs reduce to mean, minimum, and maximum."""
    runs = [{"slot_f1": 0.4}, {"slot_f1": 0.5}, {"slot_f1": 0.6}]
    mean, low, high = summarize(runs)["slot_f1"]
    assert mean == pytest.approx(0.5)
    assert (low, high) == (0.4, 0.6)
