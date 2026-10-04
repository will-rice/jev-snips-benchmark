"""Tests for the run script's output path."""

from pathlib import Path

import pytest

from jevsnips.scripts.run import results_path


def test_full_run_writes_to_the_split_file() -> None:
    """A full run owns results/test.jsonl."""
    assert results_path(None) == Path("results/test.jsonl")


def test_limited_run_does_not_overwrite_the_full_results() -> None:
    """A smoke run writes to its own file."""
    assert results_path(20) == Path("results/test-first20.jsonl")


@pytest.mark.parametrize("limit", [0, -5])
def test_non_positive_limit_is_rejected(limit: int) -> None:
    """A limit that selects nothing, or drops from the end, is an error."""
    with pytest.raises(ValueError, match="positive"):
        results_path(limit)
