from app.explanation.guard import find_unsupported_numbers, numbers_in

ALLOWED = numbers_in('{"Administrative": 49, "income": "$22,250", "internet": "79.3%", "year": 2025}')


def test_numbers_in_parses_separators_and_percentages():
    assert numbers_in("$22,250 and 79.3% in 2025, -0.20") == {22250.0, 79.3, 2025.0, 0.2}


def test_guard_accepts_numbers_from_payload_within_rounding():
    assert find_unsupported_numbers("Administrative is weakest (49%).", ALLOWED) == []
    assert find_unsupported_numbers("Income is $22,250 per person.", ALLOWED) == []
    assert find_unsupported_numbers("About 79% use the internet.", ALLOWED) == []


def test_guard_flags_invented_number():
    text = "Clients must withhold a 20% tax."
    assert find_unsupported_numbers(text, ALLOWED) == ["20%"]


def test_guard_ignores_indicator_ids():
    assert find_unsupported_numbers("See A3 and G1 for details.", ALLOWED) == []
