"""Choose few-shot examples by similarity to the utterance being labelled."""

from collections.abc import Mapping, Sequence
from itertools import pairwise

from scipy.sparse import spmatrix
from sklearn.feature_extraction.text import TfidfVectorizer

from jevsnips.models import Utterance

ExampleIndex = dict[str, tuple[TfidfVectorizer, spmatrix, Sequence[Utterance]]]


def build_index(pool: Mapping[str, Sequence[Utterance]]) -> ExampleIndex:
    """Index each intent's examples by the TF-IDF of their words and word pairs."""
    index: ExampleIndex = {}
    for intent, examples in pool.items():
        vectorizer = TfidfVectorizer(analyzer=words_and_pairs)
        matrix = vectorizer.fit_transform([example.tokens for example in examples])
        index[intent] = (vectorizer, matrix, examples)
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
