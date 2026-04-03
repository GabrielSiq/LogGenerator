import pytest
from datetime import datetime, timedelta
from resource import HumanResource, PhysicalResource, Availability


# Monday 2024-01-01, hours 9-16 available
_MON = datetime(2024, 1, 1)  # Jan 1 2024 is a Monday
_CALENDAR = {'Mon': {h: True for h in range(9, 17)}}


def make_hr():
    return HumanResource('hr_0', 'Org', 'Dept', 'Role', _CALENDAR)


def make_physical(qty=5, consumable=False):
    return PhysicalResource('pr_0', 'printer', qty, 0, consumable)


# --- Availability ---

def test_availability_available_hour():
    a = Availability(_CALENDAR)
    assert a.is_available(_MON.replace(hour=10)) is True


def test_availability_unavailable_hour():
    a = Availability(_CALENDAR)
    assert a.is_available(_MON.replace(hour=8)) is False


def test_availability_absent_day():
    a = Availability(_CALENDAR)
    tue = datetime(2024, 1, 2)  # Tuesday
    assert a.is_available(tue.replace(hour=10)) is False


def test_available_until_end_of_block():
    a = Availability(_CALENDAR)
    start = _MON.replace(hour=9)
    end = _MON.replace(hour=18)
    result = a.available_until(start, end)
    assert result == _MON.replace(hour=16, minute=59, second=59)


# --- HumanResource ---

def test_hr_is_available_when_free():
    hr = make_hr()
    assert hr.is_available(_MON.replace(hour=10)) is True


def test_hr_is_busy_after_use():
    hr = make_hr()
    hr.use(start_time=_MON.replace(hour=9), duration=7200,
           process_id='p', process_instance_id=1,
           activity_id='a', activity_instance_id=1)
    assert hr.is_available(_MON.replace(hour=10)) is False


def test_hr_double_assignment_raises():
    hr = make_hr()
    hr.use(start_time=_MON.replace(hour=9), duration=3600,
           process_id='p', process_instance_id=1,
           activity_id='a', activity_instance_id=1)
    with pytest.raises(RuntimeError):
        hr.use(start_time=_MON.replace(hour=9, minute=30), duration=1800,
               process_id='p', process_instance_id=1,
               activity_id='a', activity_instance_id=2)


def test_hr_when_available_after_busy():
    hr = make_hr()
    # busy 09:00–12:00 (3 hours = 10800s)
    hr.use(start_time=_MON.replace(hour=9), duration=10800,
           process_id='p', process_instance_id=1,
           activity_id='a', activity_instance_id=1)
    # busy_until = 12:00:00; when_available(11:00) → 12:00:01
    result = hr.when_available(_MON.replace(hour=11))
    assert result == _MON.replace(hour=12, minute=0, second=1)


# --- PhysicalResource ---

def test_physical_use_reduces_quantity():
    pr = make_physical(qty=5, consumable=True)
    pr.use(2, start_time=_MON, end_time=_MON + timedelta(hours=1))
    assert pr.get_quantity() == 3


def test_physical_replenish_restores_quantity():
    pr = make_physical(qty=5, consumable=True)
    pr.use(2, start_time=_MON, end_time=_MON + timedelta(hours=1))
    pr.replenish(2)
    assert pr.get_quantity() == 5


def test_physical_check_free_does_not_free_when_false():
    pr = make_physical(qty=2, consumable=False)
    end = _MON + timedelta(hours=2)
    pr.use(2, start_time=_MON, end_time=end)
    assert pr.get_quantity() == 0
    # check_free with free=False should not replenish
    pr.check_free(end + timedelta(seconds=1), 2, free=False)
    assert pr.get_quantity() == 0


def test_physical_check_free_replenishes_when_true():
    pr = make_physical(qty=2, consumable=False)
    end = _MON + timedelta(hours=2)
    pr.use(2, start_time=_MON, end_time=end)
    assert pr.get_quantity() == 0
    pr.check_free(end + timedelta(seconds=1), 2, free=True)
    assert pr.get_quantity() == 2
