"""Tests for the pydantic models."""

import pytest
from pydantic import ValidationError

from jevsnips.models import Prediction, SlotPrediction, Utterance


def test_utterance_rejects_misaligned_tokens_and_tags() -> None:
    """An utterance cannot have a different number of tokens and tags."""
    with pytest.raises(ValidationError, match="2 tokens but 1 tags"):
        Utterance(tokens=("play", "music"), intent="PlayMusic", tags=("O",))


def test_prediction_rejects_tags_of_the_wrong_length() -> None:
    """The slot tags must cover every token of the utterance."""
    utterance = Utterance(tokens=("play", "music"), intent="PlayMusic", tags=("O", "O"))
    short = SlotPrediction(tags=("O",), probabilities={}, input_tokens=1)
    with pytest.raises(ValidationError, match="1 slot tags for 2 tokens"):
        Prediction(
            utterance=utterance,
            condition="names",
            intent="PlayMusic",
            intent_probabilities={"PlayMusic": 1.0},
            intent_input_tokens=1,
            slots=short,
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
        slots=SlotPrediction(
            tags=("O", "B-artist"),
            probabilities={"token_0": {"artist": 0.1, "none": 0.9}},
            input_tokens=500,
        ),
        model="jev-1.13.0",
    )
    assert Prediction.model_validate_json(prediction.model_dump_json()) == prediction


def test_prediction_parse_is_a_snips_style_result() -> None:
    """A record carries the intent and slot values in the Snips NLU shape."""
    tokens = ("weather", "in", "new", "york", "tonight")
    tags = ("O", "O", "B-city", "I-city", "B-timeRange")
    prediction = Prediction(
        utterance=Utterance(tokens=tokens, intent="GetWeather", tags=tags),
        condition="descriptions",
        intent="GetWeather",
        intent_probabilities={"GetWeather": 0.95, "PlayMusic": 0.05},
        intent_input_tokens=1,
        slots=SlotPrediction(tags=tags, probabilities={}, input_tokens=1),
        model="jev-1.13.0",
    )
    assert prediction.model_dump(mode="json", by_alias=True)["parse"] == {
        "intent": {"intentName": "GetWeather", "probability": 0.95},
        "slots": [
            {"value": "new york", "entity": "city", "slotName": "city"},
            {"value": "tonight", "entity": "timeRange", "slotName": "timeRange"},
        ],
    }


def test_slot_prediction_omits_options_given_no_probability() -> None:
    """A span question has up to 255 options, nearly all scored 0.00."""
    slots = SlotPrediction(
        tags=("O",),
        probabilities={"artist": {"abba": 0.9, "play": 0.0, "none": 0.1}},
        input_tokens=1,
    )
    assert slots.probabilities == {"artist": {"abba": 0.9, "none": 0.1}}
