import pytest

from app.sources.timezone import max_hour_difference

LA = "America/Los_Angeles"


@pytest.mark.parametrize(
    ("zone", "expected"),
    [
        ("America/Bogota", 3),  # UTC-5 all year vs PST -8 / PDT -7
        ("America/Mexico_City", 2),  # UTC-6 all year since 2022
        ("Europe/Madrid", 9),  # CET/CEST vs PST/PDT (8 only in the DST gap weeks)
        (LA, 0),
    ],
)
def test_max_hour_difference_with_los_angeles(zone, expected):
    assert max_hour_difference(zone, LA, year=2026) == expected


def test_order_of_arguments_does_not_matter():
    assert max_hour_difference(LA, "America/Bogota", year=2026) == 3
