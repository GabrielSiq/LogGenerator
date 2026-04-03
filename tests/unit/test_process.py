from process import Process
from activity import Activity
from data import DataRequirement
from transition import Transition
from config import SENTINEL


def make_process():
    act = Activity('act1', 'Act One', distribution=60)
    t1 = Transition(SENTINEL['start'], 'act1', distribution=0)
    t2 = Transition('act1', SENTINEL['end'], distribution=0)
    data_reqs = DataRequirement.from_list([{'id': 'ticket', 'fields': ['Class']}])
    return act, Process(
        id='p', name='Test', arrival_rate={'Mon': {10: 5}},
        deadline=999999, activities={'act1': act}, gateways=[],
        transitions=[t1, t2], data_objects=data_reqs
    )


def test_get_first_activity():
    act, process = make_process()
    result, gate, delay = process.get_first_activity()
    assert result is act
    assert gate is None
    assert delay == 0


def test_get_next_from_activity_reaches_end():
    _, process = make_process()
    result, gate, delay = process.get_next('act1')
    assert result is None
    assert gate is None
    assert delay is None


def test_get_next_unknown_source_returns_none():
    _, process = make_process()
    result, gate, delay = process.get_next('nonexistent')
    assert result is None
    assert gate is None
    assert delay is None


def test_get_arrival_rate_known():
    _, process = make_process()
    assert process.get_arrival_rate('Mon', 10) == 5


def test_get_arrival_rate_missing_day():
    _, process = make_process()
    assert process.get_arrival_rate('Fri', 10) == 0


def test_get_arrival_rate_missing_hour():
    _, process = make_process()
    assert process.get_arrival_rate('Mon', 5) == 0


def test_new_increments_instance_counter():
    _, process = make_process()
    inst1 = process.new()
    inst2 = process.new()
    assert inst1.process_instance_id == 1
    assert inst2.process_instance_id == 2
