from app.auth.throttle import LoginThrottle


def test_blocks_after_five_failures_within_window():
    throttle = LoginThrottle()
    for second in range(4):
        throttle.record_failure("1.2.3.4", now=second)
    assert not throttle.is_blocked("1.2.3.4", now=10)
    throttle.record_failure("1.2.3.4", now=10)
    assert throttle.is_blocked("1.2.3.4", now=11)


def test_failures_older_than_window_are_forgotten():
    throttle = LoginThrottle()
    for _ in range(5):
        throttle.record_failure("1.2.3.4", now=0)
    assert throttle.is_blocked("1.2.3.4", now=900)
    assert not throttle.is_blocked("1.2.3.4", now=901)


def test_keys_are_independent():
    throttle = LoginThrottle()
    for _ in range(5):
        throttle.record_failure("1.1.1.1", now=0)
    assert not throttle.is_blocked("2.2.2.2", now=1)


def test_reset_clears_failures():
    throttle = LoginThrottle()
    for _ in range(5):
        throttle.record_failure("1.2.3.4", now=0)
    throttle.reset("1.2.3.4")
    assert not throttle.is_blocked("1.2.3.4", now=1)
