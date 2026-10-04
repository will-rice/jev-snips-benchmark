"""Pydantic models for parsed data and saved predictions."""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, computed_field, model_validator
from pydantic.alias_generators import to_camel
from seqeval.metrics.sequence_labeling import get_entities

Condition = Literal["names", "descriptions"]


class Utterance(BaseModel, frozen=True):
    """A SNIPS utterance with its gold intent and BIO slot tags."""

    tokens: tuple[str, ...]
    intent: str
    tags: tuple[str, ...]

    @model_validator(mode="after")
    def check_aligned(self) -> Self:
        """Reject an utterance whose token and tag counts differ."""
        if len(self.tokens) != len(self.tags):
            raise ValueError(f"{len(self.tokens)} tokens but {len(self.tags)} tags")
        return self


class SlotPrediction(BaseModel, frozen=True):
    """One slot scheme's result for one utterance."""

    tags: tuple[str, ...]
    probabilities: dict[str, dict[str, float]]
    input_tokens: int


class ParsedIntent(BaseModel, frozen=True):
    """The predicted intent in the Snips NLU result shape."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    intent_name: str
    probability: float


class ParsedSlot(BaseModel, frozen=True):
    """One filled slot in the Snips NLU result shape.

    SNIPS labels each slot value with a single name, so the entity is the
    slot name, and the value is the utterance text, not a resolved value.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    value: str
    entity: str
    slot_name: str


class Parse(BaseModel, frozen=True):
    """An utterance's intent and slots in the Snips NLU result shape."""

    intent: ParsedIntent
    slots: tuple[ParsedSlot, ...]


class Prediction(BaseModel, frozen=True):
    """The saved record for one utterance."""

    utterance: Utterance
    condition: Condition
    intent: str
    intent_probabilities: dict[str, float]
    intent_input_tokens: int
    token: SlotPrediction
    span: SlotPrediction
    model: str

    @computed_field
    @property
    def parse(self) -> Parse:
        """The predicted intent and the token scheme's slots as a parse."""
        return Parse(
            intent=ParsedIntent(
                intent_name=self.intent,
                probability=self.intent_probabilities[self.intent],
            ),
            slots=tuple(
                ParsedSlot(
                    value=" ".join(self.utterance.tokens[start : end + 1]),
                    entity=slot,
                    slot_name=slot,
                )
                for slot, start, end in get_entities(list(self.token.tags))
            ),
        )

    @model_validator(mode="after")
    def check_tag_lengths(self) -> Self:
        """Reject a scheme whose tags do not cover every token."""
        for scheme, slots in (("token", self.token), ("span", self.span)):
            if len(slots.tags) != len(self.utterance.tokens):
                raise ValueError(
                    f"{scheme} has {len(slots.tags)} tags "
                    f"for {len(self.utterance.tokens)} tokens"
                )
        return self
