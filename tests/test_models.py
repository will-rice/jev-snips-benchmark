"""Tests for the pydantic models."""

import pytest
from pydantic import ValidationError

from jevsnips.models import Prediction, SlotPrediction, Utterance


def test_utterance_rejects_misaligned_tokens_and_tags() -> None:
    """An utterance cannot have a different number of tokens and tags."""
    with pytest.raises(ValidationError, match="2 tokens but 1 tags"):
        Utterance(tokens=("play", "music"), intent="PlayMusic", tags=("O",))


def test_prediction_rejects_tags_of_the_wrong_length() -> None:
    """A scheme's tags must cover every token of the utterance."""
    utterance = Utterance(tokens=("play", "music"), intent="PlayMusic", tags=("O", "O"))
    short = SlotPrediction(tags=("O",), probabilities={}, input_tokens=1)
    full = SlotPrediction(tags=("O", "O"), probabilities={}, input_tokens=1)
    with pytest.raises(ValidationError, match="span has 1 tags for 2 tokens"):
        Prediction(
            utterance=utterance,
            condition="names",
            intent="PlayMusic",
            intent_probabilities={"PlayMusic": 1.0},
            intent_input_tokens=1,
            token=full,
            span=short,
            model="jev-1.13.0",
        )


def test_prediction_survives_a_json_round_trip() -> None:
    """A saved record reloads to an equal model."""
    prediction = Prediction(
        utterance=Utterance(
            tokens=("play", "abba"), intent="PlayMusic", tags=("O", "B-artist")
        ),
        condition="descriptions",
        intent="PlayMusic",
        intent_probabilities={"PlayMusic": 0.9, "RateBook": 0.1},
        intent_input_tokens=300,
        token=SlotPrediction(
            tags=("O", "B-artist"),
            probabilities={"token_0": {"artist": 0.1, "none": 0.9}},
            input_tokens=500,
        ),
        span=SlotPrediction(
            tags=("O", "B-artist"),
            probabilities={"artist": {"abba": 0.8, "none": 0.2}},
            input_tokens=700,
        ),
        model="jev-1.13.0",
    )
    assert Prediction.model_validate_json(prediction.model_dump_json()) == prediction
