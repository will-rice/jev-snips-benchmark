"""Tests for the slot-extraction patterns taken from the Jev docs."""

from collections.abc import Mapping

import pytest
from typesafe_sdk import Choice, Noul, SystemOneResponse

from jevsnips.config import MAX_OPTIONS
from jevsnips.data import load_slot_schema
from jevsnips.patterns import (
    NONE_OF_THESE,
    candidate_spans,
    decode_extraction,
    decode_function,
    extraction_request,
    function_request,
)
from jevsnips.spec import SLOT_SPEC

TOKENS = ("play", "abba", "now")
SPANS = ["play", "abba", "now", "play abba", "abba now", "play abba now"]


def response(answers: Mapping[str, Mapping[str, object]]) -> SystemOneResponse:
    """Build the response Jev would return for the given answers."""
    return SystemOneResponse.model_validate(
        {"model": "jev", "usage": {"input_tokens": 1}, "answers": answers}
    )


def choice(span: str, probability: float) -> dict[str, object]:
    """Build a Choice answer that picked the span with the probability."""
    return {
        "type": "choice",
        "choice": span,
        "confidence": probability,
        "probabilities": {span: probability},
    }


def test_spec_has_a_question_pair_for_every_slot_of_every_intent() -> None:
    """Each slot the schema offers has a definition and both questions."""
    assert {intent: sorted(slots) for intent, slots in SLOT_SPEC.items()} == (
        load_slot_schema()
    )
    assert all(
        set(pair) == {"definition", "question", "stated"}
        for slots in SLOT_SPEC.values()
        for pair in slots.values()
    )


def test_candidate_spans_are_every_run_of_words_shortest_first() -> None:
    """Code supplies the candidates: each run of consecutive words."""
    assert candidate_spans(TOKENS) == {
        "play": (0, 1),
        "abba": (1, 2),
        "now": (2, 3),
        "play abba": (0, 2),
        "abba now": (1, 3),
        "play abba now": (0, 3),
    }


def test_candidate_spans_keep_the_first_position_of_a_repeated_text() -> None:
    """An option can appear once, so a repeated text maps to its first run."""
    assert candidate_spans(("a", "b", "a"))["a"] == (0, 1)


def test_candidate_spans_drop_the_longest_runs_to_fit_the_option_limit() -> None:
    """A long utterance keeps every short run and leaves room for none."""
    tokens = tuple(f"w{index}" for index in range(30))
    spans = candidate_spans(tokens)
    assert len(spans) <= MAX_OPTIONS - 1
    assert all(token in spans for token in tokens)
    assert max(end - start for start, end in spans.values()) == 9


def test_candidate_spans_reject_an_utterance_containing_the_none_option() -> None:
    """The word none could not be told apart from the no-value option."""
    with pytest.raises(ValueError, match="none"):
        candidate_spans(("none", "of", "them"))


def test_extraction_request_asks_one_span_question_per_slot_with_none() -> None:
    """The extraction cookbook: pick the value among found spans, or none."""
    state, questions = extraction_request(TOKENS, "PlayMusic")
    assert state == "play abba now"
    assert list(questions) == list(SLOT_SPEC["PlayMusic"])
    artist = questions["artist"]
    assert isinstance(artist, Choice)
    assert artist.instructions == (
        "The intent is PlayMusic. Which span of the utterance is the artist? "
        f"{SLOT_SPEC['PlayMusic']['artist']['definition']} "
        "Answer none if the utterance has no artist."
    )
    assert artist.criteria == dict.fromkeys(SPANS) | {"none": NONE_OF_THESE}


def test_function_request_asks_a_value_and_a_stated_question_per_slot() -> None:
    """The function-calling cookbook: a value Choice and a stated Noul."""
    state, questions = function_request(TOKENS, "PlayMusic")
    assert state == "play abba now"
    assert len(questions) == 2 * len(SLOT_SPEC["PlayMusic"])
    value, stated = questions["artist"], questions["artist?"]
    assert isinstance(value, Choice)
    assert value.instructions == (
        f"{SLOT_SPEC['PlayMusic']['artist']['question']} "
        f"{SLOT_SPEC['PlayMusic']['artist']['definition']}"
    )
    assert value.criteria == dict.fromkeys(SPANS)
    assert isinstance(stated, Noul)
    assert stated.instructions == SLOT_SPEC["PlayMusic"]["artist"]["stated"]


def test_decode_extraction_tags_each_picked_span_and_skips_none() -> None:
    """A slot answered none fills nothing; a picked span becomes BIO tags."""
    answers = {"artist": choice("abba now", 0.9), "track": choice("none", 0.8)}
    assert decode_extraction(TOKENS, response(answers)) == (
        "O",
        "B-artist",
        "I-artist",
    )


def test_decode_extraction_gives_an_overlap_to_the_more_probable_slot() -> None:
    """Two slots claiming the same word: the more probable pick keeps it."""
    answers = {"artist": choice("abba", 0.6), "track": choice("abba now", 0.7)}
    assert decode_extraction(TOKENS, response(answers)) == (
        "O",
        "B-track",
        "I-track",
    )


def test_decode_function_fills_only_the_slots_that_are_stated() -> None:
    """A value is used only when its stated question says yes."""
    answers = {
        "artist": choice("abba", 0.9),
        "artist?": {"type": "noul", "noul": 0.8},
        "track": choice("now", 0.9),
        "track?": {"type": "noul", "noul": 0.4},
    }
    assert decode_function(TOKENS, response(answers)) == ("O", "B-artist", "O")


def test_decode_function_ranks_an_overlap_by_its_least_certain_judgement() -> None:
    """The cookbook's confidence is the weaker of stated and value."""
    answers = {
        "artist": choice("abba", 0.95),
        "artist?": {"type": "noul", "noul": 0.55},
        "track": choice("abba now", 0.7),
        "track?": {"type": "noul", "noul": 0.9},
    }
    assert decode_function(TOKENS, response(answers)) == (
        "O",
        "B-track",
        "I-track",
    )


def test_decode_function_fills_a_slot_stated_at_exactly_the_threshold() -> None:
    """Probabilities have two decimals, so 0.50 occurs and counts as stated."""
    answers = {
        "artist": choice("abba", 0.9),
        "artist?": {"type": "noul", "noul": 0.5},
    }
    assert decode_function(TOKENS, response(answers)) == ("O", "B-artist", "O")


def test_decode_function_lets_a_weak_value_lose_to_a_stronger_pair() -> None:
    """A confident stated answer does not carry an unsure value."""
    answers = {
        "artist": choice("abba", 0.6),
        "artist?": {"type": "noul", "noul": 0.9},
        "track": choice("abba now", 0.7),
        "track?": {"type": "noul", "noul": 0.7},
    }
    assert decode_function(TOKENS, response(answers)) == (
        "O",
        "B-track",
        "I-track",
    )


def test_decode_extraction_breaks_a_tie_by_slot_name() -> None:
    """Equal scores are common at two decimals; the later name wins."""
    answers = {"track": choice("abba", 1.0), "artist": choice("abba now", 1.0)}
    assert decode_extraction(TOKENS, response(answers)) == ("O", "B-track", "O")
