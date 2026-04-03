"""
Defines the interface for user-supplied plugin functions in input/rules.py
and input/data.py.

Naming convention
-----------------
Rule functions must be named after the gateway ID they serve.
Data transform functions must be named after the activity ID they serve.
Both files are discovered from the input directory specified at runtime
(default: ``input/``).

Data format
-----------
Both function types receive a DataSnapshot — a dict mapping each data object ID
to a dict of its current field values::

    {'ticket': {'Class': 'support', 'Priority': 'high'}}

Only data objects listed in the activity's DataInput (or available in the
process instance's data store for gateways) are guaranteed to be present.
Field values are the current state at the moment the activity or gateway fires.

Rule functions  (input/rules.py)
---------------------------------
Signature::

    def <gateway_id>(data: DataSnapshot) -> str

Receives the current data snapshot and must return a gate ID string that
matches one of the gates defined for this gateway in models.xml.
Returning an unrecognised gate ID raises ``RuntimeError`` at simulation time.

Example::

    def bug(data: DataSnapshot) -> str:
        return 'yes' if data['ticket']['Class'] == 'bug' else 'no'

Data transform functions  (input/data.py)
------------------------------------------
Signature::

    def <activity_id>(data: DataSnapshot) -> DataSnapshot

Receives the current data snapshot and must return a dict of the form
``{object_id: {field: new_value, ...}}`` containing only the objects and
fields to update — other fields are left unchanged.  Object IDs and field
names must match those defined in data.xml; returning an unknown object ID or
field name raises ``ConfigurationError`` at simulation time.

Example::

    def read(data: DataSnapshot) -> DataSnapshot:
        cls = random.choice(['support', 'trust', 'bug'], p=[0.6, 0.2, 0.2])
        return {'ticket': {'Class': cls}}
"""
from typing import Callable, Dict, Any

DataSnapshot = Dict[str, Dict[str, Any]]
RuleFunction = Callable[[DataSnapshot], str]
DataFunction = Callable[[DataSnapshot], DataSnapshot]
