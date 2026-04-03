from transition import Transition


def test_get_next_returns_correct_tuple():
    t = Transition('A', 'B', sgate='yes', dgate='out', distribution=10)
    dest, gate, delay = t.get_next()
    assert dest == 'B'
    assert gate == 'out'
    assert delay == 10


def test_zero_delay_by_default():
    t = Transition('A', 'B')
    _, _, delay = t.get_next()
    assert delay == 0


def test_no_gates_by_default():
    t = Transition('A', 'B', distribution=5)
    dest, gate, delay = t.get_next()
    assert dest == 'B'
    assert gate is None
    assert delay == 5
