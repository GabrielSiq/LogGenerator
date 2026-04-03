# LogGenerator

A discrete-event business process simulator that generates synthetic event logs for process mining and BPM research.

Real event logs are hard to obtain — privacy concerns, NDAs, and newly-installed processes leave researchers without data. LogGenerator lets you define a business process in XML, run a simulation over a configurable date range, and get a structured JSON event log you fully control. Every aspect of the process — arrival rates, activity durations, resource pools, routing logic, and data transformations — is configurable without touching the simulation engine.

The bundled `input/` directory models a ride-sharing platform's support organization (ticket triage, support case handling, trust & safety, and background check data collection) and runs out of the box.

Companion paper: [A Log Generator for Process Analytics](A%20Log%20Generator%20for%20Process%20Analytics.pdf)

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the built-in example (last 7 days, default output directory)
python3 main.py

# 3. Find the output
ls output/
```

The output is a JSON array. Each record is one event in the lifecycle of a process instance:

```json
{
  "log_id": 0,
  "timestamp": 1704096420,
  "date": "01/01/2024-00:07:00",
  "process_id": "data_collection",
  "process_instance_id": 1,
  "activity_id": "read",
  "activity_instance_id": 1,
  "status": "start_activity",
  "resource": { "support_1": 1 }
}
```

---

## CLI Reference

All options have sensible defaults — only specify what differs.

| Flag | Default | Description |
|---|---|---|
| `--input DIR` | `input/` | Directory containing XML config files and Python plugins |
| `--start YYYY-MM-DD` | 7 days ago | Simulation start date (inclusive) |
| `--end YYYY-MM-DD` | today | Simulation end date (inclusive) |
| `--name NAME` | auto timestamp | Output filename without extension |
| `--output DIR` | `output/` | Directory to write the JSON log |
| `--resource-limit KEY=VAL ...` | — | Override resource pool quantities at runtime |

```bash
# Custom date range with a named output file
python3 main.py --start 2024-01-01 --end 2024-01-31 --name january_run

# Stress-test resource contention (KEY is the resource id from resources.xml)
python3 main.py --start 2024-01-01 --end 2024-01-07 --resource-limit support=5 trust=5

# Use your own process model in a separate directory
python3 main.py --input my_process/ --name my_run
```

---

## Modeling a Process

A model lives entirely in one directory (default: `input/`). Six files define everything: four XML files and two Python modules. Define things before referencing them — data objects → activities → resources → process models → Python plugins.

> The bundled `input/` is a complete working example. Use it as a reference when building your own model.

### `data.xml` — Data Objects

Data objects are structured forms that travel with a process instance. Field values start as `null` and are populated during simulation by transform functions in `data.py`.

```xml
<DataObjects>
    <DataObject id="ticket" type="form">
        <Name>Ticket</Name>
        <Fields>
            <Field name="Class"/>
        </Fields>
    </DataObject>
</DataObjects>
```

The `id` is referenced everywhere else. Only `type="form"` is currently supported.

---

### `activities.xml` — Activity Library

Activities are defined globally and shared across all process models. Individual parameters can be overridden per-model inside `models.xml`.

```xml
<Activity id="read">
    <Name>Read Ticket</Name>
    <Duration>
        <Distribution type="Normal" mean="300" std="180" />
    </Duration>
    <DataOutput>
        <DataObject id="ticket"/>
    </DataOutput>
    <Resources>
        <Resource ref="support" quantity="1"/>
    </Resources>
</Activity>
```

**Duration distributions:**

| Type | Parameters |
|---|---|
| `Const` | `value` |
| `Normal` | `mean`, `std` |
| `Uniform` | `low`, `high` |
| `Triangular` | `left`, `mode`, `right` |
| `Beta` | `a`, `b` |

**Optional elements:**

- `<DataInput>` — data objects (and optionally specific fields) the activity reads at start
- `<DataOutput>` — data objects the activity writes on success; field-level filtering can be added
- `<Resources>` — references a resource pool by `id` (`ref="support"`) or inline by org/dept/role
- `<FailureRate>` — probability [0.0–1.0] the activity fails on each attempt
- `<Retries>` — number of retry attempts after failure before giving up
- `<Timeout>` — maximum duration in seconds; exceeded activities log `timeout` and do not write data
- `<Priority>` — `low`, `normal` (default), or `high`; affects queue ordering when timestamps tie

---

### `resources.xml` — Resource Pool

All resources are shared across all processes simultaneously. Activities compete for them.

```xml
<Resource type="human" id="support">
    <Organization>Company, Inc.</Organization>
    <Department>Customer Experience</Department>
    <Role>Support</Role>
    <Quantity>70</Quantity>
    <Availability>
        <Weekday>
            <TimeBlock start="9" end="12"/>
            <TimeBlock start="13" end="17"/>
        </Weekday>
        <Default>
            <TimeBlock start="10" end="12"/>
            <TimeBlock start="13" end="15"/>
        </Default>
    </Availability>
</Resource>
```

`Quantity` creates N individually-scheduled agents (`support_0`, `support_1`, ...). The `id` is what activities reference with `ref=` and what `--resource-limit` overrides use as a key.

**Availability templates** — listed in priority order:
1. Explicit day tags (`<Mon>`, `<Tue>`, ..., `<Sun>`) — applies only to that day
2. `<Weekday>` — applies to Mon–Fri where no explicit day is defined
3. `<Default>` — applies to any remaining days

`<TimeBlock start="H" end="H"/>` uses 24-hour hours (0–24). Hours not covered by any block are unavailable.

**Physical resources** are also supported (`type="physical"`) with an optional `consumable="true"` attribute.

---

### `models.xml` — Process Models

A process model assembles activities and gateways into a directed graph and sets arrival rates.

```xml
<Model id="triage">
    <Name>Ticket Triage</Name>
    <ArrivalRate>
        <Default>
            <TimeBlock start="0" end="6">5</TimeBlock>
            <TimeBlock start="6" end="18">12</TimeBlock>
            <TimeBlock start="18" end="24">6</TimeBlock>
        </Default>
    </ArrivalRate>
    <Activities>
        <Activity id="read">
            <!-- Optional: restrict which fields this activity writes in this process -->
            <DataOutput>
                <DataObject id="ticket">
                    <Fields><Field name="Class"/></Fields>
                </DataObject>
            </DataOutput>
        </Activity>
        <Activity id="send_to_eng"/>
        <!-- ... -->
    </Activities>
    <Gateways>
        <!-- Rule-based: delegates routing to a function in rules.py -->
        <Gateway id="bug">
            <Name>Is it a bug?</Name>
            <Type>Choice</Type>
            <Rule>
                <Gate id="yes"/>
                <Gate id="no"/>
            </Rule>
        </Gateway>
        <!-- Probabilistic: probabilities must sum to 1.0 -->
        <Gateway id="faq">
            <Name>Is it in FAQ?</Name>
            <Type>Choice</Type>
            <Distribution>
                <Gate id="yes">0.4</Gate>
                <Gate id="no">0.6</Gate>
            </Distribution>
        </Gateway>
    </Gateways>
    <Transitions>
        <Transition source="START" destination="read"/>
        <Transition source="read" destination="bug"/>
        <Transition source="bug" source_gate="yes" destination="send_to_eng"/>
        <Transition source="bug" source_gate="no" destination="type"/>
        <!-- ... -->
        <Transition source="send_to_eng" destination="END"/>
    </Transitions>
    <Deadline>50000000</Deadline>
</Model>
```

The triage model above produces this flow:

```
START → read → [bug gateway]
                  ├─ yes → send_to_eng → END
                  └─ no  → [type gateway]
                               ├─ support → check_faq → [faq gateway]
                               │                           ├─ yes → send_response → END
                               │                           └─ no  → open_support → END
                               └─ trust → open_trust → END
```

**Key elements:**

- `<ArrivalRate>` — uses the same `<Default>` / `<Weekday>` / day-specific template system as resources. `<TimeBlock>` values are the average number of new process instances spawned per hour in that window.
- `<Gateways>` — three types: `Choice` (pick one branch, probabilistic or rule-based), `Parallel` (split into all branches simultaneously), `Merge` (wait for all incoming branches before proceeding)
- `<Transitions>` — directed edges. `source_gate` identifies which gate of a gateway this edge leaves from. `START` and `END` are reserved sentinels.
- `<Transition>` may include a `<Duration>` element for transit delay between elements.
- `<Deadline>` — maximum process instance duration in seconds. Instances exceeding this are suspended.

---

### `rules.py` — Gateway Routing Functions

For `Choice` gateways configured with `<Rule>`, the simulator calls a Python function to determine the outgoing branch based on live process data.

**Contract:** one function per rule gateway, named exactly after the gateway `id`.

```python
# Called when the 'bug' gateway is reached
def bug(input):
    if input['ticket']['Class'] == 'bug':
        return 'yes'   # must be a gate id defined in models.xml
    else:
        return 'no'

# Called when the 'type' gateway is reached
def type(input):
    if input['ticket']['Class'] == 'support':
        return 'support'
    else:
        return 'trust'
```

`input` is a `DataSnapshot`: `{'object_id': {'field_name': value, ...}, ...}`. Only data objects listed in the gateway's model context are present. Returning an unrecognised gate ID raises `RuntimeError` at simulation time.

See [`plugins.py`](plugins.py) for the full type contract.

---

### `data.py` — Activity Data Transform Functions

When an activity with `<DataOutput>` completes successfully, the simulator calls a Python function to produce or transform data.

**Contract:** one function per transforming activity, named exactly after the activity `id`.

```python
from numpy import random

# Called when the 'read' activity completes
def read(input):
    # Return only the fields to update — not the full snapshot
    return {
        'ticket': {
            'Class': random.choice(['support', 'trust', 'bug'], p=[0.6, 0.2, 0.2])
        }
    }
```

`input` is a `DataSnapshot` of the activity's declared inputs (may be empty if no `<DataInput>` was specified). The return value must be a dict of `{object_id: {field: new_value}}` — only the fields you return are updated. Returning an unknown object ID or field name raises `ConfigurationError`.

See [`plugins.py`](plugins.py) for the full type contract.

---

## Output Format

Each simulation run produces a single JSON file — an array of event records sorted by timestamp.

**To reconstruct individual process cases:** group by `(process_id, process_instance_id)` and sort by `timestamp`.

**Fields:**

| Field | Type | Description |
|---|---|---|
| `log_id` | int | Sequential log sequence number (LSN), 0-based |
| `timestamp` | int | Unix timestamp (seconds) |
| `date` | string | `MM/DD/YYYY-HH:MM:SS` |
| `process_id` | string | Process model ID |
| `process_instance_id` | int | Case ID within the process |
| `activity_id` | string | Activity or gateway ID |
| `activity_instance_id` | int | Execution count for this activity within the case |
| `status` | string | See below |
| `resource` | object | `{"resource_id": quantity}` — omitted if none |
| `data_input` | object | Data snapshot at activity start — omitted if none |
| `data_output` | object | Data written by the activity — omitted if none |

Fields with null values are omitted from output.

**Status values:**

| Status | Meaning |
|---|---|
| `start_activity` | Activity began execution and claimed a resource |
| `end_activity` | Activity completed successfully |
| `pause_activity` | Activity paused mid-execution; re-queued for remaining duration (partial resource availability) |
| `failed` | Activity failed (probabilistic); data is not written |
| `timeout` | Activity exceeded its configured timeout; data is not written |
| `waiting_resource` | No resource was available; activity re-queued |

**Example — a complete activity lifecycle:**

```json
{
  "log_id": 0,
  "timestamp": 1704096420,
  "date": "01/01/2024-00:07:00",
  "process_id": "data_collection",
  "process_instance_id": 1,
  "activity_id": "read",
  "activity_instance_id": 1,
  "status": "start_activity",
  "resource": { "support_1": 1 }
}
{
  "log_id": 3,
  "timestamp": 1704096802,
  "date": "01/01/2024-00:13:22",
  "process_id": "data_collection",
  "process_instance_id": 1,
  "activity_id": "read",
  "activity_instance_id": 1,
  "status": "end_activity",
  "resource": { "support_1": 1 },
  "data_output": { "ticket": { "Class": "support" } }
}
```

---

## Architecture

A discrete-event engine built around a priority queue. Every pending activity or gateway is a timestamped item; the engine always processes the item with the earliest timestamp.

**Queue ordering:** timestamp (ascending) → priority level (descending) → process instance ID (ascending, so older instances win ties).

**Components:**

| Module | Role |
|---|---|
| `main.py` | CLI; parses arguments, launches simulation |
| `model_builder.py` | Parses XML files and Python plugins into in-memory objects |
| `simulation_manager.py` | Main event loop |
| `execution_queue.py` | Priority queue with three-level ordering |
| `resource.py` | Resource pool; per-resource availability windows and scheduling |
| `log.py` | Collects `LogItem` records; serializes to JSON |
| `gateway.py` | Choice (probabilistic/rule-based), Parallel, Merge routing logic |
| `plugins.py` | Interface contract and type aliases for `rules.py` / `data.py` |
| `config.py` | Shared constants: gateway types, priority values, sentinel strings, default paths |

**Execution flow:**

1. `ModelBuilder` parses all 6 input files into in-memory `Process`, `Activity`, `Gateway`, `Resource`, and `Form` objects.
2. The execution queue is seeded: for each process model, arrival rate blocks generate initial instance arrivals across the date range.
3. Main loop — pop the lowest-timestamp item:
   - **Activity:** attempt resource allocation. Three outcomes — *full* (execute, log `start_activity` → `end_activity`, enqueue successor); *partial* (log `start_activity` → `pause_activity`, re-enqueue as leftover with remaining duration); *none* (log `waiting_resource`, park in per-role wait queue).
   - **Gateway:** *Choice* picks one branch; *Parallel* enqueues all branches; *Merge* waits in `pending_merges` until all incoming branches have arrived (start time = `max(arrival times) + 1s`).
4. Loop ends when the queue is empty or the next item's timestamp exceeds `--end`.
5. `LogWriter` sorts all collected events by timestamp and writes the JSON array.

**Resource contention:** waiting activities are held in per-role wait queues rather than the main execution queue. When a resource frees, only activities waiting on that specific role are re-evaluated. Simulations with tight resource limits can run significantly slower than unconstrained ones.

---

## Differences from the Paper

The companion paper describes the original design. This implementation extends it in a few modeling-visible ways:

- **XML templates for arrival rates and availability.** The paper specifies rates and availability as explicit per-day blocks. The implementation adds `<Weekday>` (expands to Mon–Fri) and `<Default>` (fills remaining days) shorthand templates, with explicit day tags as overrides. This eliminates the repetition of specifying the same schedule seven times.

- **Resource `ref=` shorthand.** Activities can reference a resource pool by its `id` (`<Resource ref="support" quantity="1"/>`) instead of repeating the org/dept/role inline. The paper does not describe this shorthand.

- **Rule gateways as a first-class type.** The paper describes rule-based routing as a variant of `Choice` gateways. The implementation treats it as a distinct gateway type with its own validated interface, defined in `plugins.py`.

- **Plugin interface contract.** `rules.py` and `data.py` function signatures and the `DataSnapshot` format are formally specified in `plugins.py`. Data function return values are validated at runtime — returning an unknown object ID or field name raises `ConfigurationError` naming the offending activity.

---

## Testing

```bash
source .venv/bin/activate && pytest
```

59 tests, 1 skipped (deterministic seeded runs, pending), runs in ~2s.

- **Unit tests** (`tests/unit/`) — duration sampling, failure rates, gateway routing, resource availability and scheduling, data transforms, queue ordering, process graph traversal, XML parsing
- **Integration tests** (`tests/integration/`) — full 1-day and 7-day simulation runs, activity lifecycle completeness (every terminal event has a matching `start_activity`), resource contention triggering

---

## Project Context

Academic project, UCSB Computer Science. The companion paper ([A Log Generator for Process Analytics](A%20Log%20Generator%20for%20Process%20Analytics.pdf)) describes the original design and a demonstration application using the simulator to inform staffing decisions after a new process is introduced.
