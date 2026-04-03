import json
import os
import pytest
from datetime import datetime
from simulation_manager import SimulationManager

_OUTPUT_NAME = '_test_integration'
_OUTPUT_PATH = f'output/{_OUTPUT_NAME}.json'
_TIGHT_OUTPUT_NAME = '_test_integration_tight'
_TIGHT_OUTPUT_PATH = f'output/{_TIGHT_OUTPUT_NAME}.json'
_WEEK_OUTPUT_NAME = '_test_integration_week'
_WEEK_OUTPUT_PATH = f'output/{_WEEK_OUTPUT_NAME}.json'


@pytest.fixture
def one_day_events():
    mgr = SimulationManager(datetime(2024, 1, 1), datetime(2024, 1, 2))
    mgr.simulate(name=_OUTPUT_NAME)
    with open(_OUTPUT_PATH) as f:
        events = json.load(f)
    yield events
    if os.path.exists(_OUTPUT_PATH):
        os.remove(_OUTPUT_PATH)


@pytest.fixture
def tight_resource_events():
    mgr = SimulationManager(datetime(2024, 1, 1), datetime(2024, 1, 2))
    mgr.simulate(name=_TIGHT_OUTPUT_NAME, resource_limit={'support': '1', 'trust': '1'})
    with open(_TIGHT_OUTPUT_PATH) as f:
        events = json.load(f)
    yield events
    if os.path.exists(_TIGHT_OUTPUT_PATH):
        os.remove(_TIGHT_OUTPUT_PATH)


def test_produces_events(one_day_events):
    assert len(one_day_events) > 0


def test_all_terminal_events_have_matching_start(one_day_events):
    terminal_statuses = {'end_activity', 'failed', 'timeout'}
    starts = set()
    for event in one_day_events:
        if event['status'] == 'start_activity':
            key = (event['process_id'], event['process_instance_id'],
                   event['activity_id'], event['activity_instance_id'])
            starts.add(key)
    for event in one_day_events:
        if event['status'] in terminal_statuses:
            key = (event['process_id'], event['process_instance_id'],
                   event['activity_id'], event['activity_instance_id'])
            assert key in starts, f"Terminal event has no matching start: {key}"


def test_waiting_resource_appears_under_tight_limits(tight_resource_events):
    statuses = {e['status'] for e in tight_resource_events}
    assert 'waiting_resource' in statuses


def test_full_week_completes():
    output_path = _WEEK_OUTPUT_PATH
    try:
        mgr = SimulationManager(datetime(2024, 1, 1), datetime(2024, 1, 8))
        mgr.simulate(name=_WEEK_OUTPUT_NAME)
        with open(output_path) as f:
            events = json.load(f)
        assert len(events) > 0
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)


@pytest.mark.skip(reason="Requires --seed support (Phase 5.1)")
def test_deterministic_with_seed():
    pass
