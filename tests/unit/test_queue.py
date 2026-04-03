from datetime import datetime
from unittest.mock import MagicMock
from activity import Activity
from execution_queue import QueueItem, PriorityQueue
from config import PRIORITY_VALUES

_T0 = datetime(2024, 1, 1, 9, 0, 0)
_T1 = datetime(2024, 1, 1, 10, 0, 0)


def make_item(start, priority=PRIORITY_VALUES['normal'], pid='p', piid=1):
    process = MagicMock()
    process.process_id = pid
    process.process_instance_id = piid
    process.get_element_instance_id.return_value = 0
    element = MagicMock(spec=Activity)
    element.priority = priority
    element.id = 'act'
    element.timeout = 3600
    return QueueItem(process, 'act', 0, start, element)


def test_earlier_start_pops_first():
    q = PriorityQueue()
    late = make_item(_T1)
    early = make_item(_T0)
    q.push(late)
    q.push(early)
    assert q.pop().start == _T0


def test_higher_priority_wins_same_start():
    q = PriorityQueue()
    normal = make_item(_T0, priority=PRIORITY_VALUES['normal'])
    high = make_item(_T0, priority=PRIORITY_VALUES['high'])
    q.push(normal)
    q.push(high)
    assert q.pop().element.priority == PRIORITY_VALUES['high']


def test_lower_instance_id_wins_same_start_and_priority():
    q = PriorityQueue()
    newer = make_item(_T0, piid=2)
    older = make_item(_T0, piid=1)
    q.push(newer)
    q.push(older)
    assert q.pop().process_instance_id == 1


def test_repeat_returns_new_item():
    item = make_item(_T0, piid=1)
    original_attempt = item.attempt
    repeated = item.repeat(60)
    assert repeated is not item
    assert item.attempt == original_attempt
    assert repeated.attempt == original_attempt + 1


def test_leftover_returns_new_item_with_correct_duration():
    item = make_item(_T0)
    leftover = item.leftover(original_duration=100, actual_duration=40, data={})
    assert leftover is not item
    # leftover_duration was None → original_duration(100) - actual_duration(40) = 60
    assert leftover.leftover_duration == 60
