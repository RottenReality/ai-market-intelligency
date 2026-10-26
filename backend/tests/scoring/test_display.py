import pytest

from app.scoring.display import format_raw, format_score


@pytest.mark.parametrize(
    ("value", "unit", "expected"),
    [
        (79.345, "%", "79.3%"),
        (22250.0, "USD", "$22,250"),
        (42090207.0, "people", "42.1M"),
        (-0.1973526, "index", "-0.20"),
        (3.0, "hours", "3 h"),
        (True, "bool", "Yes"),
        (False, "bool", "No"),
        ("very_low", "band", "Very low"),
        (None, "%", "n/a"),
    ],
)
def test_format_raw_matches_the_web_app(value, unit, expected):
    assert format_raw(value, unit) == expected


def test_format_score():
    assert format_score(46.05) == "46"
    assert format_score(74.5) == "75"
    assert format_score(None) == "n/a"
