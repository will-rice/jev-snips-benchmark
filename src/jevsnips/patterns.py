"""The two ways of extracting values that the Jev docs show, as slot methods.

Both ask about each slot on its own and take the answer from a set of
candidates that code supplies. SNIPS slots have no pattern to find candidates
with, so the candidates are every run of consecutive words in the utterance.
"""

from collections.abc import Iterable, Sequence

from typesafe_sdk import Choice, Noul, SystemOneResponse

from jevsnips.config import MAX_OPTIONS, NONE, STATED_THRESHOLD
from jevsnips.spec import SLOT_SPEC

# The extraction cookbook's wording for its no-value option.
NONE_OF_THESE = "None of these is the requested value."
EXTRACTION_QUESTION = (
    "The intent is {intent}. Which span of the utterance is the {slot}? "
    f"{{definition}} Answer {NONE} if the utterance has no {{slot}}."
)


def extraction_request(
    tokens: Sequence[str], intent: str
) -> tuple[str, dict[str, Choice]]:
    """Build the extraction cookbook's request: pick each slot's value or none.

    Args:
        tokens: The utterance's words.
        intent: The predicted intent, whose slots are asked about.

    Returns:
        The state and one question per slot, named by the slot.
    """
    criteria = dict.fromkeys(candidate_spans(tokens)) | {NONE: NONE_OF_THESE}
    return " ".join(tokens), {
        slot: Choice(
            instructions=EXTRACTION_QUESTION.format(
                intent=intent, slot=slot, definition=pair["definition"]
            ),
            criteria=criteria,
        )
        for slot, pair in SLOT_SPEC[intent].items()
    }


def decode_extraction(
    tokens: Sequence[str], response: SystemOneResponse
) -> tuple[str, ...]:
    """Tag the span each slot picked, ranking overlaps by its probability."""
    return place_spans(
        tokens,
        [
            (answer.probabilities[answer.choice], slot, answer.choice)
            for slot, answer in response.choices.items()
            if answer.choice != NONE
        ],
    )


def function_request(
    tokens: Sequence[str], intent: str
) -> tuple[str, dict[str, Choice | Noul]]:
    """Build the function-calling cookbook's request: a value and a stated.

    The intent is the function and its slots are the arguments. The cookbook's
    arguments are closed sets; a slot's values are open, so the options are
    the utterance's spans. The value question is the one written about the
    idea, followed by the slot's definition.

    Args:
        tokens: The utterance's words.
        intent: The predicted intent, whose slots are asked about.

    Returns:
        The state and, per slot, a value question named by the slot and a
        yes/no question named by the slot followed by a question mark.
    """
    criteria = dict.fromkeys(candidate_spans(tokens))
    questions: dict[str, Choice | Noul] = {}
    for slot, pair in SLOT_SPEC[intent].items():
        questions[slot] = Choice(
            instructions=f"{pair['question']} {pair['definition']}", criteria=criteria
        )
        questions[f"{slot}?"] = Noul(instructions=pair["stated"])
    return " ".join(tokens), questions


def decode_function(
    tokens: Sequence[str], response: SystemOneResponse
) -> tuple[str, ...]:
    """Tag the value of each stated slot.

    A slot is filled when its stated answer reaches STATED_THRESHOLD. Overlaps
    are ranked by the cookbook's confidence, the less certain of the stated
    and the value answers.
    """
    stated = {slot: response.nouls[f"{slot}?"].noul for slot in response.choices}
    return place_spans(
        tokens,
        [
            (
                min(stated[slot], answer.probabilities[answer.choice]),
                slot,
                answer.choice,
            )
            for slot, answer in response.choices.items()
            if stated[slot] >= STATED_THRESHOLD
        ],
    )


def place_spans(
    tokens: Sequence[str], proposals: Iterable[tuple[float, str, str]]
) -> tuple[str, ...]:
    """Convert scored (score, slot, span) proposals to BIO tags.

    Slots are asked about separately, so two can claim the same words. The
    highest score is placed first and a span that overlaps a placed one is
    dropped.
    """
    spans = candidate_spans(tokens)
    tags = ["O"] * len(tokens)
    for _, slot, span in sorted(proposals, reverse=True):
        start, end = spans[span]
        if all(tag == "O" for tag in tags[start:end]):
            tags[start:end] = [f"B-{slot}"] + [f"I-{slot}"] * (end - start - 1)
    return tuple(tags)


def candidate_spans(tokens: Sequence[str]) -> dict[str, tuple[int, int]]:
    """Map every run of consecutive words to its position, shortest first.

    A text that occurs twice keeps its first position. A question takes
    MAX_OPTIONS options, one of which may be none, so the longest runs of a
    long utterance are left out.

    Raises:
        ValueError: If a word is the none option's name.
    """
    if NONE in tokens:
        raise ValueError(f"Utterance contains the word {NONE}: {' '.join(tokens)}")
    spans: dict[str, tuple[int, int]] = {}
    for length in range(1, len(tokens) + 1):
        starts = range(len(tokens) - length + 1)
        if len(spans) + len(starts) > MAX_OPTIONS - 1:
            break
        for start in starts:
            spans.setdefault(
                " ".join(tokens[start : start + length]), (start, start + length)
            )
    return spans
