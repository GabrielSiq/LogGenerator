import pytest
from duration import Duration


def test_const_returns_exact_value():
    assert Duration(300).generate() == 300


def test_const_from_dict():
    assert Duration({'type': 'const', 'value': 42}).generate() == 42


def test_negative_clamp():
    assert Duration({'type': 'normal', 'mean': -1000, 'std': 0}).generate() == 0


def test_unknown_type_raises():
    with pytest.raises(ValueError, match="Unknown distribution type"):
        Duration({'type': 'poisson', 'mean': 5}).generate()


def test_uniform_in_range():
    d = Duration({'type': 'uniform', 'low': 10, 'high': 20})
    for _ in range(100):
        result = d.generate()
        assert 10 <= result <= 20


def test_dict_input_not_mutated():
    spec = {'type': 'normal', 'mean': 300, 'std': 60}
    Duration(spec).generate()
    assert 'type' in spec
    assert spec['mean'] == 300
