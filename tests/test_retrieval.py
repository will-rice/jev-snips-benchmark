"""Tests for choosing few-shot examples by similarity to the utterance."""

from jevsnips.config import RETRIEVED_EXAMPLES
from jevsnips.data import load_example_pool, load_utterances
from jevsnips.models import Utterance
from jevsnips.retrieval import build_index, retrieve


def utterance(text: str, intent: str = "PlayMusic") -> Utterance:
    """Build an unlabelled utterance from its text."""
    tokens = tuple(text.split())
    return Utterance(tokens=tokens, intent=intent, tags=("O",) * len(tokens))


def test_retrieve_ranks_examples_by_shared_words_and_word_pairs() -> None:
    """The most similar example of the intent comes first."""
    pool = {
        "PlayMusic": [
            utterance("rate this book five stars"),
            utterance("play some jazz music"),
            utterance("play the latest jazz album"),
        ]
    }
    found = retrieve(build_index(pool), "PlayMusic", ("play", "some", "jazz"), 2)
    assert [" ".join(example.tokens) for example in found] == [
        "play some jazz music",
        "play the latest jazz album",
    ]


def test_retrieve_only_returns_examples_of_the_given_intent() -> None:
    """Examples are drawn from the predicted intent's pool alone."""
    pool = {
        "PlayMusic": [utterance("play jazz")],
        "RateBook": [utterance("rate jazz five stars", "RateBook")],
    }
    found = retrieve(build_index(pool), "RateBook", ("play", "jazz"), 1)
    assert [example.intent for example in found] == ["RateBook"]


def test_the_pool_never_contains_an_evaluated_utterance() -> None:
    """A test utterance cannot retrieve itself from the training split."""
    evaluated = {example.tokens for example in load_utterances("test")}
    pool = load_example_pool()
    assert all(len(examples) >= RETRIEVED_EXAMPLES for examples in pool.values())
    assert not any(
        example.tokens in evaluated
        for examples in pool.values()
        for example in examples
    )


def test_retrieve_never_returns_the_same_text_twice() -> None:
    """A repeated training utterance fills one example slot, not several."""
    pool = {
        "PlayMusic": [
            utterance("play some jazz"),
            utterance("play some jazz"),
            utterance("play some rock"),
        ]
    }
    found = retrieve(build_index(pool), "PlayMusic", ("play", "some", "jazz"), 2)
    assert [" ".join(example.tokens) for example in found] == [
        "play some jazz",
        "play some rock",
    ]


def test_the_first_copy_of_a_repeated_text_supplies_its_labels() -> None:
    """When copies of a text disagree on labels, the first one is shown."""
    tokens = ("play", "jazz")
    first = Utterance(tokens=tokens, intent="PlayMusic", tags=("O", "B-genre"))
    second = Utterance(tokens=tokens, intent="PlayMusic", tags=("O", "B-playlist"))
    index = build_index({"PlayMusic": [first, second]})
    assert retrieve(index, "PlayMusic", tokens, 2) == [first]
