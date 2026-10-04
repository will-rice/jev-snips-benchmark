"""Tests for the run script's output path."""

from pathlib import Path

import pytest

from jevsnips.scripts.run import results_path


def test_full_run_path_names_the_condition_and_run() -> None:
    """Each condition and repeat owns its own file."""
    assert results_path("names", 2, None) == Path("results/test-names-run2.jsonl")


def test_limited_run_does_not_overwrite_the_full_results() -> None:
    """A smoke run writes to its own file."""
    path = results_path("descriptions", 1, 20)
    assert path == Path("results/test-descriptions-run1-first20.jsonl")


@pytest.mark.parametrize("limit", [0, -5])
def test_non_positive_limit_is_rejected(limit: int) -> None:
    """A limit that selects nothing, or drops from the end, is an error."""
    with pytest.raises(ValueError, match="positive"):
        results_path("names", 1, limit)
