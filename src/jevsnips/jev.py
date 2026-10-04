"""Ask Jev for an utterance's intent and slots, and decode its answers."""

from collections.abc import Mapping, Sequence

from typesafe_sdk import Choice, ChoiceAnswer, SystemOneResponse, TypeSafeClient

from jevsnips.config import MAX_GAP, MAX_OPTIONS, MODEL, NONE
from jevsnips.descriptions import (
    INTENT_DESCRIPTIONS,
    NONE_DESCRIPTION,
    SLOT_DESCRIPTIONS,
)
from jevsnips.models import Condition, Prediction, SlotPrediction, Utterance


def predict(
    client: TypeSafeClient,
    utterance: Utterance,
    schema: Mapping[str, Sequence[str]],
    condition: Condition,
) -> Prediction:
    """Predict the intent, then the slots under both schemes.

    Both slot schemes are conditioned on the predicted intent, so they
    differ only in how slots are asked and decoded. Under the descriptions
    condition every intent and slot is offered with its definition; under
    names the model sees label names only.

    Args:
        client: An open TypeSafe client.
        utterance: The utterance to label.
        schema: Each intent's slot types.
        condition: Whether labels are offered with descriptions.

    Returns:
        The predicted intent and each scheme's tags, probabilities, and
        token usage.
    """
    tokens = utterance.tokens
    state = " ".join(tokens)
    described = condition == "descriptions"
    intents = {
        name: INTENT_DESCRIPTIONS[name] if described else None for name in schema
    }
    intent_response = client.system_one(
        state, {"intent": intent_question(intents)}, model=MODEL
    )
    intent = intent_response.choices["intent"]
    slots = {
        slot: SLOT_DESCRIPTIONS[intent.choice][slot] if described else None
        for slot in schema[intent.choice]
    }

    token_response = client.system_one(
        {"utterance": state},
        token_questions(
            tokens, intent.choice, slots, NONE_DESCRIPTION if described else None
        ),
        model=MODEL,
    )
    span_response = client.system_one(
        state, span_questions(tokens, intent.choice, slots), model=MODEL
    )
    return Prediction(
        utterance=utterance,
        condition=condition,
        intent=intent.choice,
        intent_probabilities=intent.probabilities,
        intent_input_tokens=input_tokens(intent_response),
        token=SlotPrediction(
            tags=decode_tokens(
                [
                    token_response.choices[f"token_{index}"].choice
                    for index in range(len(tokens))
                ]
            ),
            probabilities={
                name: answer.probabilities
                for name, answer in token_response.choices.items()
            },
            input_tokens=input_tokens(token_response),
        ),
        span=SlotPrediction(
            tags=decode_spans(tokens, span_response.choices),
            probabilities={
                name: answer.probabilities
                for name, answer in span_response.choices.items()
            },
            input_tokens=input_tokens(span_response),
        ),
        model=intent_response.model,
    )


def intent_question(intents: Mapping[str, str | None]) -> Choice:
    """Build the question that picks one intent.

    Args:
        intents: Each intent name with its description, or None for name only.
    """
    return Choice(
        instructions="What is the intent of the utterance?",
        criteria=dict(intents),
    )


def token_questions(
    tokens: Sequence[str],
    intent: str,
    slots: Mapping[str, str | None],
    none_description: str | None,
) -> dict[str, Choice]:
    """Build one question per token asking which slot type it fills.

    The word and the words on either side of it are labelled fields of the
    instructions, which the model reads more reliably than a marker inside a
    sentence, and which tell a repeated word apart by its context. The
    question refers to the `utterance` key of the state.

    A slot's description, if any, is its option's criteria, and so is the
    none option's: without one, the model gives most words outside a slot a
    slot anyway.
    """
    criteria = {**slots, NONE: none_description}
    return {
        f"token_{index}": Choice(
            instructions={
                "intent": intent,
                "words_before": " ".join(tokens[:index]),
                "word": token,
                "words_after": " ".join(tokens[index + 1 :]),
                "question": (
                    "Which slot does `word` fill in `utterance`? "
                    f"Answer {NONE} if it fills no slot."
                ),
            },
            criteria=criteria,
        )
        for index, token in enumerate(tokens)
    }


def span_questions(
    tokens: Sequence[str], intent: str, slots: Mapping[str, str | None]
) -> dict[str, Choice]:
    """Build one question per slot type asking which span fills it.

    The options are spans, so a slot's description, if any, goes in the
    instructions.
    """
    criteria = dict.fromkeys([*span_candidates(tokens), NONE])
    return {
        slot: Choice(
            instructions=(
                f"The intent is {intent}. Which span of the utterance is the "
                f"{slot}? {f'{description} ' if description else ''}"
                f"Answer {NONE} if the utterance has no {slot}."
            ),
            criteria=criteria,
        )
        for slot, description in slots.items()
    }


def span_candidates(tokens: Sequence[str]) -> dict[str, tuple[int, int]]:
    """Map each candidate span's text to its first (start, end) position.

    Span length is capped at the largest length whose spans, plus the none
    option, fit in one Choice.

    Raises:
        ValueError: If a token equals the none option.
    """
    if NONE in tokens:
        raise ValueError(f"Token '{NONE}' collides with the none option")
    max_length = len(tokens)
    while (
        sum(len(tokens) - length + 1 for length in range(1, max_length + 1)) + 1
        > MAX_OPTIONS
    ):
        max_length -= 1
    candidates: dict[str, tuple[int, int]] = {}
    for length in range(1, max_length + 1):
        for start in range(len(tokens) - length + 1):
            end = start + length
            candidates.setdefault(" ".join(tokens[start:end]), (start, end))
    return candidates


def decode_tokens(choices: Sequence[str]) -> tuple[str, ...]:
    """Convert per-token slot types to BIO tags, merging equal neighbours.

    Up to MAX_GAP unlabelled words between two words of the same type take
    that type, so small words inside a name or title stay in its span.
    """
    labels = list(choices)
    for start, label in enumerate(labels):
        if label == NONE:
            continue
        for end in range(start + 2, min(start + MAX_GAP + 2, len(labels))):
            if labels[end] == label and all(
                between == NONE for between in labels[start + 1 : end]
            ):
                labels[start + 1 : end] = [label] * (end - start - 1)
                break
    tags = []
    previous = NONE
    for choice in labels:
        if choice == NONE:
            tags.append("O")
        else:
            tags.append(f"{'I' if choice == previous else 'B'}-{choice}")
        previous = choice
    return tuple(tags)


def decode_spans(
    tokens: Sequence[str], answers: Mapping[str, ChoiceAnswer]
) -> tuple[str, ...]:
    """Convert per-slot span choices to BIO tags.

    Proposals are accepted from most to least probable; one that overlaps
    an accepted span is dropped.
    """
    candidates = span_candidates(tokens)
    proposals = sorted(
        (
            (answer.probabilities[answer.choice], slot, answer.choice)
            for slot, answer in answers.items()
            if answer.choice != NONE
        ),
        reverse=True,
    )
    tags = ["O"] * len(tokens)
    for _, slot, text in proposals:
        start, end = candidates[text]
        if all(tag == "O" for tag in tags[start:end]):
            tags[start:end] = [f"B-{slot}", *[f"I-{slot}"] * (end - start - 1)]
    return tuple(tags)


def input_tokens(response: SystemOneResponse) -> int:
    """Return a response's input token count.

    Raises:
        ValueError: If the response carries no usage.
    """
    if response.usage.input_tokens is None:
        raise ValueError("Jev response has no input token usage")
    return response.usage.input_tokens
