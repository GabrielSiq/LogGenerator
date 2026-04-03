from failure import Failure


def test_rate_zero_never_fails():
    f = Failure(0.0)
    assert all(not f.check_failure() for _ in range(100))


def test_rate_one_always_fails():
    f = Failure(1.0)
    assert all(f.check_failure() for _ in range(100))
