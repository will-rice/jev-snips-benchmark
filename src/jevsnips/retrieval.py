"""Choose few-shot examples by similarity to the utterance being labelled."""

from collections.abc import Mapping, Sequence
from itertools import pairwise

from scipy.sparse import spmatrix
from sklearn.feature_extraction.text import TfidfVectorizer

from jevsnips.models import Utterance

ExampleIndex = dict[str, tuple[TfidfVectorizer, spmatrix, Sequence[Utterance]]]


def build_index(pool: Mapping[str, Sequence[Utterance]]) -> ExampleIndex:
    """Index each intent's examples by the TF-IDF of their words and word pairs.

    SNIPS repeats some training utterances. Only the first copy of a text is
    indexed, so retrieval never spends two example slots on the same text.
    """
    index: ExampleIndex = {}
    for intent, examples in pool.items():
        first_by_text: dict[tuple[str, ...], Utterance] = {}
        for example in examples:
            first_by_text.setdefault(example.tokens, example)
        distinct = list(first_by_text.values())
        vectorizer = TfidfVectorizer(analyzer=words_and_pairs)
        matrix = vectorizer.fit_transform([example.tokens for example in distinct])
        index[intent] = (vectorizer, matrix, distinct)
    return index


def retrieve(
    index: ExampleIndex, intent: str, tokens: Sequence[str], count: int
) -> list[Utterance]:
    """Return an intent's examples most similar to the utterance, best first.

    Similarity is the cosine between TF-IDF vectors, which are unit length,
    so it is their dot product.
    """
    vectorizer, matrix, examples = index[intent]
    scores = (matrix @ vectorizer.transform([tokens]).T).toarray().ravel()
    return [
        examples[position] for position in scores.argsort(kind="stable")[::-1][:count]
    ]


def words_and_pairs(tokens: Sequence[str]) -> list[str]:
    """Return an utterance's words and its adjacent word pairs."""
    return [*tokens, *(f"{left} {right}" for left, right in pairwise(tokens))]
