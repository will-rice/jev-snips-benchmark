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
    questions = token_questions(("play", "abba"), "PlayMusic", slots, "Not a slot.")
    assert questions["token_1"].criteria == {
        "artist": "The musician or band.",
        "none": "Not a slot.",
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
