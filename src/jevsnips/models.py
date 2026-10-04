"""Pydantic models for parsed data and saved predictions."""

from typing import Self

from pydantic import BaseModel, model_validator


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


class Prediction(BaseModel, frozen=True):
    """The saved record for one utterance."""

    utterance: Utterance
    intent: str
    intent_probabilities: dict[str, float]
    intent_input_tokens: int
    token: SlotPrediction
    span: SlotPrediction
    model: str

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
