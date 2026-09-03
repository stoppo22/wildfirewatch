"""Tests for environmental context handling."""

from wildfirewatch.environment import land_cover_name


def test_land_cover_name_returns_name_for_known_code():
    actual = land_cover_name(10)

    assert actual == "tree_cover"


def test_land_cover_name_returns_none_for_unknown_code():
    actual = land_cover_name(999)

    assert actual is None
