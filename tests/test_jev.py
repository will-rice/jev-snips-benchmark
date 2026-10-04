"""Tests for question building and answer decoding."""

import pytest
from typesafe_sdk import SystemOneResponse, Usage

from jevsnips.jev import (
    decode_tokens,
    input_tokens,
    intent_question,
    labelled_examples,
    token_questions,
)
from jevsnips.models import Utterance


def test_intent_question_offers_each_intent_without_descriptions() -> None:
    """The intent question is zero-shot: names only."""
    question = intent_question({"PlayMusic": None, "RateBook": None})
    assert question.criteria == {"PlayMusic": None, "RateBook": None}


def test_intent_question_carries_descriptions_when_given() -> None:
    """A described intent passes its description as the option's criteria."""
    question = intent_question({"PlayMusic": "Play music."})
    assert question.criteria == {"PlayMusic": "Play music."}


def test_token_questions_offer_the_intents_slots_plus_none() -> None:
    """Each token gets one question over the given slots and none."""
    slots = {"artist": None, "track": None}
    questions = token_questions(("play", "abba"), "PlayMusic", slots, None)
    assert list(questions) == ["token_0", "token_1"]
    assert questions["token_0"].criteria == {
        "artist": None,
        "track": None,
        "none": None,
    }


def test_token_questions_identify_a_word_by_the_words_around_it() -> None:
    """A repeated word is told apart by what comes before and after it."""
    questions = token_questions(
        ("play", "the", "the"), "PlayMusic", {"artist": None}, None
    )
    question = (
        "Which slot does `word` fill in `utterance`? Answer none if it fills no slot."
    )
    assert questions["token_1"].instructions == {
        "intent": "PlayMusic",
        "words_before": "play",
        "word": "the",
        "words_after": "the",
        "question": question,
    }
    assert questions["token_2"].instructions == {
        "intent": "PlayMusic",
        "words_before": "play the",
        "word": "the",
        "words_after": "",
        "question": question,
    }


def test_token_questions_carry_slot_descriptions_when_given() -> None:
    """A described slot passes its description as the option's criteria."""
    slots = {"artist": "The musician or band."}
    questions = token_questions(("play", "abba"), "PlayMusic", slots, "Not a slot.")
    assert questions["token_1"].criteria == {
        "artist": "The musician or band.",
        "none": "Not a slot.",
    }


def test_decode_tokens_merges_adjacent_equal_types() -> None:
    """A run of one type is a single span; a type change starts a new one."""
    choices = ["none", "artist", "artist", "track", "none"]
    assert decode_tokens(choices) == ("O", "B-artist", "I-artist", "B-track", "O")


def test_decode_tokens_fills_a_short_gap_inside_one_slot() -> None:
    """Small words inside a title join the slot on both sides of them."""
    choices = ["object_name", "none", "none", "object_name"]
    assert decode_tokens(choices) == (
        "B-object_name",
        "I-object_name",
        "I-object_name",
        "I-object_name",
    )


def test_decode_tokens_leaves_a_long_gap_open() -> None:
    """Three unlabelled words separate two slots of the same type."""
    choices = ["city", "none", "none", "none", "city"]
    assert decode_tokens(choices) == ("B-city", "O", "O", "O", "B-city")


def test_decode_tokens_leaves_a_gap_between_different_types_open() -> None:
    """A gap is only filled when the same type is on both sides."""
    choices = ["artist", "none", "track"]
    assert decode_tokens(choices) == ("B-artist", "O", "B-track")


def test_input_tokens_raises_when_the_response_has_no_usage() -> None:
    """Missing usage is an error, not zero tokens."""
    response = SystemOneResponse(model="jev-1.13.0", usage=Usage(), answers={})
    with pytest.raises(ValueError, match="no input token usage"):
        input_tokens(response)


def test_decode_tokens_chains_fills_across_several_gaps() -> None:
    """Each filled word can anchor the next gap in the same slot."""
    choices = ["track", "none", "track", "none", "track", "none"]
    assert decode_tokens(choices) == (
        "B-track",
        "I-track",
        "I-track",
        "I-track",
        "I-track",
        "O",
    )


def test_labelled_examples_show_each_utterance_with_its_slot_values() -> None:
    """An example pairs the utterance text with its slots as whole values."""
    example = Utterance(
        tokens=("play", "the", "best", "of", "abba"),
        intent="PlayMusic",
        tags=("O", "B-album", "I-album", "I-album", "B-artist"),
    )
    assert labelled_examples([example]) == [
        {
            "utterance": "play the best of abba",
            "slots": [
                {"slot": "album", "value": "the best of"},
                {"slot": "artist", "value": "abba"},
            ],
        }
    ]
