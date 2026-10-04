"""Tests for question building and answer decoding."""

import pytest
from typesafe_sdk import ChoiceAnswer, SystemOneResponse, Usage

from jevsnips.jev import (
    decode_spans,
    decode_tokens,
    input_tokens,
    intent_question,
    span_candidates,
    span_questions,
    token_questions,
)


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
    questions = token_questions(("play", "abba"), "PlayMusic", slots)
    assert list(questions) == ["token_0", "token_1"]
    assert questions["token_0"].criteria == {
        "artist": None,
        "track": None,
        "none": None,
    }
    assert "PlayMusic" in str(questions["token_0"].instructions)


def test_token_questions_mark_the_position_of_a_repeated_word() -> None:
    """A repeated word is disambiguated by bracketing one occurrence."""
    questions = token_questions(("play", "the", "the"), "PlayMusic", {"artist": None})
    assert '"play [the] the"' in str(questions["token_1"].instructions)
    assert '"play the [the]"' in str(questions["token_2"].instructions)


def test_span_candidates_map_text_to_its_first_occurrence() -> None:
    """Duplicate span texts collapse to the earliest position."""
    assert span_candidates(("a", "b", "a")) == {
        "a": (0, 1),
        "b": (1, 2),
        "a b": (0, 2),
        "b a": (1, 3),
        "a b a": (0, 3),
    }


def test_span_candidates_offer_every_span_up_to_22_tokens() -> None:
    """All 253 spans of a 22-token utterance fit with the none option."""
    tokens = tuple(f"w{i}" for i in range(22))
    candidates = span_candidates(tokens)
    assert len(candidates) == 253
    assert " ".join(tokens) in candidates


def test_span_candidates_cap_length_to_fit_the_option_limit() -> None:
    """A 24-token utterance offers spans of at most 14 words."""
    candidates = span_candidates(tuple(f"w{i}" for i in range(24)))
    assert len(candidates) + 1 <= 255
    assert max(end - start for start, end in candidates.values()) == 14


def test_span_candidates_reject_a_token_equal_to_the_none_option() -> None:
    """A token named none would collide with the none option."""
    with pytest.raises(ValueError, match="collides"):
        span_candidates(("play", "none"))


def test_span_questions_ask_once_per_slot_over_spans_plus_none() -> None:
    """Each slot type gets one question whose options are spans."""
    slots = {"artist": None, "track": None}
    questions = span_questions(("play", "abba"), "PlayMusic", slots)
    assert list(questions) == ["artist", "track"]
    assert list(questions["artist"].criteria) == ["play", "abba", "play abba", "none"]
    assert questions["artist"].instructions == (
        "The intent is PlayMusic. Which span of the utterance is the artist? "
        "Answer none if the utterance has no artist."
    )


def test_token_questions_carry_slot_descriptions_when_given() -> None:
    """A described slot passes its description as the option's criteria."""
    slots = {"artist": "The musician or band."}
    questions = token_questions(("play", "abba"), "PlayMusic", slots)
    assert questions["token_1"].criteria == {
        "artist": "The musician or band.",
        "none": None,
    }


def test_span_questions_put_the_slot_description_in_the_instructions() -> None:
    """Span options are spans, so the description goes in the question."""
    slots = {"artist": "The musician or band."}
    questions = span_questions(("play", "abba"), "PlayMusic", slots)
    assert questions["artist"].instructions == (
        "The intent is PlayMusic. Which span of the utterance is the artist? "
        "The musician or band. Answer none if the utterance has no artist."
    )


def test_decode_tokens_merges_adjacent_equal_types() -> None:
    """A run of one type is a single span; a type change starts a new one."""
    choices = ["none", "artist", "artist", "track", "none"]
    assert decode_tokens(choices) == ("O", "B-artist", "I-artist", "B-track", "O")


def test_decode_spans_keeps_the_more_probable_of_two_overlapping_spans() -> None:
    """Overlapping proposals resolve in favour of the higher probability."""
    tokens = ("play", "sabrina", "salerno", "now")
    answers = {
        "artist": ChoiceAnswer(
            choice="sabrina salerno",
            confidence=0.9,
            probabilities={"sabrina salerno": 0.9, "none": 0.1},
        ),
        "track": ChoiceAnswer(
            choice="salerno now",
            confidence=0.6,
            probabilities={"salerno now": 0.6, "none": 0.4},
        ),
        "year": ChoiceAnswer(
            choice="none", confidence=0.9, probabilities={"none": 1.0}
        ),
    }
    assert decode_spans(tokens, answers) == ("O", "B-artist", "I-artist", "O")


def test_input_tokens_raises_when_the_response_has_no_usage() -> None:
    """Missing usage is an error, not zero tokens."""
    response = SystemOneResponse(model="jev-1.13.0", usage=Usage(), answers={})
    with pytest.raises(ValueError, match="no input token usage"):
        input_tokens(response)
