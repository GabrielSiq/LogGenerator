import types
import pytest
import gateway as gw
from unittest.mock import patch
from gateway import GateDistribution, GateRule
from config import ConfigurationError


def _mock_rules(**funcs):
    mod = types.ModuleType('mock_rules')
    for name, fn in funcs.items():
        setattr(mod, name, fn)
    return mod


def test_distribution_deterministic():
    d = GateDistribution(['a', 'b'], [1.0, 0.0])
    assert d.get_gate() == 'a'


def test_distribution_probabilities_must_sum_to_one():
    with pytest.raises(ValueError):
        GateDistribution(['a', 'b'], [0.3, 0.8])


def test_rule_gate_returns_correct_gate():
    mock_mod = _mock_rules(my_rule=lambda data: 'yes')
    with patch.object(gw, 'RULE_MODULE', mock_mod):
        rule = GateRule(['yes', 'no'], 'my_rule')
        assert rule.get_gate({'ticket': {'Class': 'bug'}}) == 'yes'


def test_rule_gate_invalid_return_raises():
    mock_mod = _mock_rules(bad_rule=lambda data: 'invalid_gate')
    with patch.object(gw, 'RULE_MODULE', mock_mod):
        rule = GateRule(['yes', 'no'], 'bad_rule')
        with pytest.raises(RuntimeError):
            rule.get_gate({})


def test_missing_rule_function_raises_configuration_error():
    mock_mod = _mock_rules()  # empty module — no functions
    with patch.object(gw, 'RULE_MODULE', mock_mod):
        with pytest.raises(ConfigurationError):
            GateRule(['yes', 'no'], 'missing')
