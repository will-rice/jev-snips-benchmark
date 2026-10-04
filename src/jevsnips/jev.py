"""Ask Jev for an utterance's intent and each word's slot, and decode them."""

from collections.abc import Mapping, Sequence

from typesafe_sdk import Choice, JSONValue, SystemOneResponse, TypeSafeClient

from jevsnips.config import MAX_GAP, MODEL, NONE, RETRIEVED_EXAMPLES
from jevsnips.descriptions import (
    INTENT_DESCRIPTIONS,
    NONE_DESCRIPTION,
    SLOT_DESCRIPTIONS,
)
from jevsnips.models import Condition, Prediction, SlotPrediction, Utterance
from jevsnips.retrieval import ALL_INTENTS, ExampleIndex, retrieve


def predict(
    client: TypeSafeClient,
    utterance: Utterance,
    schema: Mapping[str, Sequence[str]],
    examples: Mapping[str, Sequence[Utterance]],
    index: ExampleIndex,
    condition: Condition,
) -> Prediction:
    """Predict the intent, then classify each word into one of its slots.

    Slots are conditioned on the predicted intent, never the gold one. Under
    names the model sees label names only. Under descriptions every intent
    and slot is offered with its definition. Under fewshot the slot request
    also shows a fixed sample of labelled training utterances of the
    predicted intent; under retrieved it shows the ones most similar to the
    utterance instead, and the intent request shows the most similar
    training utterances of any intent with their intents.

    Args:
        client: An open TypeSafe client.
        utterance: The utterance to label.
        schema: Each intent's slot types.
        examples: Each intent's fixed sample of labelled training utterances.
        index: Every usable training utterance, indexed for retrieval.
        condition: What the model is shown besides label names.

    Returns:
        The predicted intent and the slot tags, probabilities, and token
        usage.
    """
    tokens = utterance.tokens
    state = " ".join(tokens)
    described = condition != "names"
    intents = {
        name: INTENT_DESCRIPTIONS[name] if described else None for name in schema
    }
    retrieving = condition == "retrieved"
    intent_state: JSONValue = state
    if retrieving:
        intent_state = {
            "utterance": state,
            "labelled_examples": intent_examples(
                retrieve(index, ALL_INTENTS, tokens, RETRIEVED_EXAMPLES)
            ),
        }
    intent_response = client.system_one(
        intent_state, {"intent": intent_question(intents, retrieving)}, model=MODEL
    )
    intent = intent_response.choices["intent"]
    slots = {
        slot: SLOT_DESCRIPTIONS[intent.choice][slot] if described else None
        for slot in schema[intent.choice]
    }

    slot_state: dict[str, JSONValue] = {"utterance": state}
    if condition == "fewshot":
        slot_state["labelled_examples"] = labelled_examples(examples[intent.choice])
    if retrieving:
        slot_state["labelled_examples"] = labelled_examples(
            retrieve(index, intent.choice, tokens, RETRIEVED_EXAMPLES)
        )
    slot_response = client.system_one(
        slot_state,
        token_questions(
            tokens, intent.choice, slots, NONE_DESCRIPTION if described else None
        ),
        model=MODEL,
    )
    return Prediction(
        utterance=utterance,
        condition=condition,
        intent=intent.choice,
        intent_probabilities=intent.probabilities,
        intent_input_tokens=input_tokens(intent_response),
        slots=SlotPrediction(
            tags=decode_tokens(
                [
                    slot_response.choices[f"token_{index}"].choice
                    for index in range(len(tokens))
                ]
            ),
            probabilities={
                name: answer.probabilities
                for name, answer in slot_response.choices.items()
            },
            input_tokens=input_tokens(slot_response),
        ),
        model=intent_response.model,
    )


def intent_question(intents: Mapping[str, str | None], keyed: bool) -> Choice:
    """Build the question that picks one intent.

    Args:
        intents: Each intent name with its description, or None for name only.
        keyed: Whether the state is an object holding the utterance under an
            `utterance` key, as it is when examples are shown beside it.
    """
    return Choice(
        instructions=(
            "What is the intent of `utterance`?"
            if keyed
            else "What is the intent of the utterance?"
        ),
        criteria=dict(intents),
    )


def intent_examples(utterances: Sequence[Utterance]) -> list[JSONValue]:
    """Show each utterance with its intent."""
    return [
        {"utterance": " ".join(utterance.tokens), "intent": utterance.intent}
        for utterance in utterances
    ]


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
    none option's: when the slots are described and none is not, the model
    over-assigns slots to words outside any slot.
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


def labelled_examples(utterances: Sequence[Utterance]) -> list[JSONValue]:
    """Show each utterance with every word's slot, or none.

    The examples have the same shape as the question, one label per word.
    Shown only as whole slot values, they made the model leave the first
    word of a phrase out of its slot more often.
    """
    return [
        {
            "utterance": " ".join(utterance.tokens),
            "words": [
                {"word": word, "slot": NONE if tag == "O" else tag[2:]}
                for word, tag in zip(utterance.tokens, utterance.tags, strict=True)
            ],
        }
        for utterance in utterances
    ]


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


def input_tokens(response: SystemOneResponse) -> int:
    """Return a response's input token count.

    Raises:
        ValueError: If the response carries no usage.
    """
    if response.usage.input_tokens is None:
        raise ValueError("Jev response has no input token usage")
    return response.usage.input_tokens
