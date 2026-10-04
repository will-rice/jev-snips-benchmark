"""Tests for data loading against the real dataset."""

from jevsnips.data import load_slot_schema, load_utterances


def test_test_split_parses_to_700_aligned_utterances() -> None:
    """The SNIPS test split has 700 utterances over 7 intents."""
    utterances = load_utterances("test")
    assert len(utterances) == 700
    assert len({utterance.intent for utterance in utterances}) == 7
    assert utterances[0].tokens[:3] == ("add", "sabrina", "salerno")
    assert utterances[0].tags[:3] == ("O", "B-artist", "I-artist")


def test_schema_has_seven_intents_with_known_slots() -> None:
    """The schema maps each intent to the slot types it accepts."""
    schema = load_slot_schema()
    assert len(schema) == 7
    assert schema["SearchCreativeWork"] == ["object_name", "object_type"]
    assert len(schema["BookRestaurant"]) == 14


def test_schema_covers_every_gold_slot_in_test() -> None:
    """Every gold slot type in test is offered for its intent."""
    schema = load_slot_schema()
    for utterance in load_utterances("test"):
        slots = {tag[2:] for tag in utterance.tags if tag != "O"}
        assert slots <= set(schema[utterance.intent])
