"""Tests that every label the model is offered has a description."""

from jevsnips.data import load_slot_schema
from jevsnips.descriptions import INTENT_DESCRIPTIONS, SLOT_DESCRIPTIONS


def test_every_intent_has_a_description() -> None:
    """The described intents are exactly the schema's intents."""
    assert set(INTENT_DESCRIPTIONS) == set(load_slot_schema())


def test_every_slot_of_every_intent_has_a_description() -> None:
    """The described slots are exactly each intent's schema slots."""
    schema = load_slot_schema()
    assert {intent: set(slots) for intent, slots in SLOT_DESCRIPTIONS.items()} == {
        intent: set(slots) for intent, slots in schema.items()
    }
