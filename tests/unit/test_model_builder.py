from xml.etree.ElementTree import Element, SubElement
from model_builder import ModelBuilder


def make_block(parent, start, end, text=None):
    b = SubElement(parent, 'TimeBlock')
    b.set('start', str(start))
    b.set('end', str(end))
    if text is not None:
        b.text = str(text)
    return b


def make_calendar(*days):
    """days: list of (tag, [(start, end), ...])"""
    avail = Element('Availability')
    for tag, blocks in days:
        day_el = SubElement(avail, tag)
        for start, end in blocks:
            make_block(day_el, start, end)
    return avail


# --- _parse_calendar ---

def test_explicit_days_populate_calendar():
    avail = make_calendar(('Mon', [(9, 17)]))
    cal = ModelBuilder._parse_calendar(avail)
    assert 'Mon' in cal
    assert all(h in cal['Mon'] for h in range(9, 17))
    assert 'Tue' not in cal


def test_weekday_fills_mon_fri():
    avail = Element('Availability')
    wd = SubElement(avail, 'Weekday')
    make_block(wd, 9, 17)
    cal = ModelBuilder._parse_calendar(avail)
    for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']:
        assert day in cal
        assert 9 in cal[day]
    assert 'Sat' not in cal
    assert 'Sun' not in cal


def test_explicit_overrides_weekday():
    avail = Element('Availability')
    mon_el = SubElement(avail, 'Mon')
    make_block(mon_el, 8, 9)   # only hour 8 — does not overlap with Weekday (9-17)
    wd = SubElement(avail, 'Weekday')
    make_block(wd, 9, 17)
    cal = ModelBuilder._parse_calendar(avail)
    # Mon has only hour 8 from explicit; Weekday was NOT applied to Mon
    assert 8 in cal['Mon']
    assert 9 not in cal['Mon']  # Weekday hours did NOT bleed into explicit Mon
    # Other weekdays DO get the Weekday template
    assert 9 in cal['Tue']


def test_default_fills_remaining_days():
    avail = Element('Availability')
    wd = SubElement(avail, 'Weekday')
    make_block(wd, 9, 17)
    default = SubElement(avail, 'Default')
    make_block(default, 0, 6)
    cal = ModelBuilder._parse_calendar(avail)
    for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']:
        assert 9 in cal[day]
    for day in ['Sat', 'Sun']:
        assert 0 in cal[day]
        assert 9 not in cal[day]  # Default did not bleed into Weekday days


# --- _parse_distribution ---

def test_parse_distribution_normal():
    node = Element('Distribution')
    node.set('type', 'Normal')
    node.set('mean', '300')
    node.set('std', '180')
    result = ModelBuilder._parse_distribution(node)
    assert result == {'type': 'Normal', 'mean': 300, 'std': 180}


def test_parse_distribution_const():
    node = Element('Distribution')
    node.set('type', 'Const')
    node.set('value', '10')
    result = ModelBuilder._parse_distribution(node)
    assert result == {'type': 'Const', 'value': 10}


def test_parse_distribution_type_remains_string():
    node = Element('Distribution')
    node.set('type', 'Normal')
    node.set('mean', '100')
    node.set('std', '10')
    result = ModelBuilder._parse_distribution(node)
    assert isinstance(result['type'], str)
