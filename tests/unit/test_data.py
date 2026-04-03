import pytest
from collections import OrderedDict
from data import Form, DataRequirement, DataManager


def make_form():
    fields = OrderedDict([('Class', None), ('Priority', None)])
    return Form('ticket', 'Ticket', fields)


# --- Form ---

def test_form_set_get_roundtrip():
    f = make_form()
    f.set_field('Class', 'bug')
    assert f.get_field('Class') == 'bug'


def test_form_set_unknown_field_raises():
    f = make_form()
    with pytest.raises(KeyError):
        f.set_field('BadField', 'x')


def test_form_from_ordered_dict_preserves_order():
    fields = OrderedDict([('B', 'b'), ('A', 'a')])
    f = Form('obj', 'Obj', fields)
    assert list(f.get_fields().keys()) == ['B', 'A']


def test_form_from_list_initialises_to_none():
    f = Form('obj', 'Obj', ['Class', 'Priority'])
    assert all(v is None for v in f.get_fields().values())


# --- DataRequirement ---

def test_data_requirement_from_empty_list():
    assert DataRequirement.from_list([]) is None


def test_data_requirement_from_none():
    assert DataRequirement.from_list(None) is None


def test_data_requirement_from_list_parses():
    reqs = DataRequirement.from_list([{'id': 'ticket', 'fields': ['Class']}])
    assert len(reqs) == 1
    assert reqs[0].id == 'ticket'
    assert reqs[0].fields == ['Class']


# --- DataManager ---

def _make_manager():
    form = Form('ticket', 'Ticket', OrderedDict([('Class', None)]))
    dm = DataManager([form], process_list=['p1'])
    return dm


def test_data_manager_create_and_read():
    dm = _make_manager()
    dm.create_instance('ticket', 'p1', 1)
    reqs = DataRequirement.from_list([{'id': 'ticket', 'fields': ['Class']}])
    result = dm.read_requirements('p1', 1, reqs)
    assert 'ticket' in result
    assert 'Class' in result['ticket']


def test_data_manager_update_persists():
    dm = _make_manager()
    dm.create_instance('ticket', 'p1', 1)
    dm.update_object('ticket', 'p1', 1, {'Class': 'bug'})
    reqs = DataRequirement.from_list([{'id': 'ticket', 'fields': ['Class']}])
    result = dm.read_requirements('p1', 1, reqs)
    assert result['ticket']['Class'] == 'bug'
