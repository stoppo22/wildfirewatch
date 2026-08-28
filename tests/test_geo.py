"""Tests for geographic distance calculations."""

import pytest

from wildfirewatch.geo import haversine_distance_km


def test_haversine_distance_same_point_is_zero():
    actual = haversine_distance_km(
        41.9028,
        12.4964,
        41.9028,
        12.4964,
    )
    expected = pytest.approx(0.0)

    assert actual == expected


def test_haversine_distance_one_degree_at_equator():
    actual = haversine_distance_km(0.0, 0.0, 0.0, 1.0)
    expected = 111.2

    assert actual == pytest.approx(expected, abs=0.1)


def test_haversine_distance_is_symmetric():
    rome_to_milan = haversine_distance_km(41.9028, 12.4964, 45.4642, 9.1900)
    milan_to_rome = haversine_distance_km(45.4642, 9.1900, 41.9028, 12.4964)

    assert rome_to_milan == pytest.approx(milan_to_rome)


def test_haversine_distance_rome_to_milan():
    actual = haversine_distance_km(
        41.9028,
        12.4964,
        45.4642,
        9.1900,
    )
    expected = 477.0

    assert actual == pytest.approx(expected, abs=1.0)
