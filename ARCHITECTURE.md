# LogGenerator — Architecture Analysis & Improvement Plan

> **Purpose:** This document is a thorough audit of the LogGenerator simulator's design, code quality, and performance. It separates findings into **Core** (same functionality, done right) and **Extra** (new capabilities). Intended for future execution on the `refactor` branch.

---

## 1. Executive Summary

The simulator works, but it has meaningful bugs, a critical performance architecture problem, and XML input that requires painful manual work. The biggest wins come from three areas:

1. **Performance:** A single architectural change to resource scheduling (per-role priority heaps instead of shuffle-and-scan) eliminates the 5x slowdown under resource pressure cited in the paper. A transition lookup index is a one-line change that accelerates every activity completion.
2. **Modeling ergonomics:** The XML is extremely verbose — days repeat identically, all transitions hardcode the same 10s delay, and resource specs are copy-pasted across every activity. Sane defaults and reference syntax would reduce model files by ~60%.
3. **Code clarity:** `_simulate_activity()` is a 73-line function with 4 nesting levels and a `TODO: Refactor` comment. Several bugs were hiding in unclear code (now fixed — see §2).

---

## 2. Critical Bugs ✅ All Fixed

| # | File | Location | Bug | Status |
|---|------|----------|-----|--------|
| 1 | `log.py` | `__lt__` | `self.process_id < self.process_id` — compares item to itself, secondary sort broken | ✅ Fixed: `other.process_id` |
| 2 | `resource.py` | `_assign_physical()` | `next(available)` on a `list` — raises `TypeError` for physical resources | ✅ Fixed: `iter(self.get_available(...))` |
| 3 | `resource.py` | `assign_resources()` | Returns after first requirement; all subsequent requirements silently ignored | ✅ Fixed: accumulates all assignments |
| 4 | `duration.py` | `__init__` | `distribution.pop('type')` mutates the caller's dict, corrupting distribution spec on reuse | ✅ Fixed: copies dict before mutating |
| 5 | `duration.py` | `generate()` | `int()` truncation biases all continuous durations downward | ✅ Fixed: `round()` for continuous distributions |
| 6 | `resource.py` | `_search_physical()` | `check_free()` called twice — second call sees already-mutated heap state | ✅ Fixed: computed once per resource, reused |

---

## 3. Core Improvements

### 3.1 Performance ✅ All Done (71s → 4.4s, 16× speedup on 7-day simulation)

#### 3.1.1 — Resource Scheduling Overhaul ✅ Fixed

**Current problem:** The paper explicitly notes resource-constrained scenarios run 5× slower. The root cause is in `resource.py`:

```python
# _search_human() — called every time an activity needs a resource
for resource in sample(all, len(all)):   # shuffles ENTIRE workforce
    if resource.is_available(start_time):
        available.append(resource)
```

Then every time ANY resource frees up, ALL waiting activities are re-evaluated (because `postpone()` re-queues them at the new resource availability time — but if multiple activities are waiting for the same role, they all wake up at the same time and race through the same scan).

`check_free()` for physical resources also pops and re-pushes the busy heap on every call, which is O(n) and stateful (corrupts heap state on exception).

**Fix — per-role availability heap:**
- At init, build a dict: `role_heap: dict[role_key, MinHeap[(free_at, resource_id)]]`
- When a resource is assigned, push `(end_time, id)` onto the role heap
- `when_available(role)` = `heap[role][0][0]` — O(1) instead of O(n) scan + shuffle
- `get_available(role, start_time)` = pop all items where `free_at <= start_time` — O(log n) per resource

This eliminates:
- `sample(all, len(all))` shuffle on every search
- The broken LRU cache (which doesn't invalidate on state changes)
- Hourly iteration in `when_available()` (currently increments by 1 hour in a loop)

For physical resources, replace the stateful `check_free()` heap-pop loop with a similar indexed structure.

**Files:** `resource.py` — `ResourceManager`, `HumanResource`, `PhysicalResource`

---

#### 3.1.2 — Transition Lookup Index ✅ Fixed

**Current problem:** `process.get_next()` is called on **every** activity and gateway completion — it's the hottest path in the simulation. It does a linear scan:

```python
for transition in self.transitions:   # O(n) per completion
    if transition.source == source and ...
```

**Fix:** At model load time, build: `self._transition_index: dict[tuple[str, str | None], Transition]`

```python
# In Process.__init__ or a post-init step:
self._transition_index = {
    (t.source, t.source_gate): t for t in self.transitions
}

# get_next becomes:
def get_next(self, source, gate=None):
    t = self._transition_index.get((source, gate))
    if t is None:
        return None, None, None
    ...
```

O(n) → O(1). Zero behavioral change.

**File:** `process.py` — `Process.get_next()`

---

#### 3.1.3 — Per-Resource-Type Wait Queue ✅ Fixed

**Current problem:** When resources are scarce, re-queued activities accumulate. Every time any resource frees up, the simulation tries ALL queued activities and rejects most. The paper describes this: "a large number of activities will accumulate in the queue and the simulator will attempt to run each of them every time a new resource frees up."

**Fix:** Maintain a secondary dict: `waiting_queues: dict[resource_role, PriorityQueue[QueueItem]]`

When an activity can't get resources (current `postpone()` case), push it to `waiting_queues[role]` instead of the main execution queue. When a resource frees up, pop only from the relevant role's queue and re-try that one item. This avoids the cascade re-evaluation.

**Files:** `simulation_manager.py`, `execution_queue.py`

---

#### 3.1.4 — Eliminate Hot-Path `deepcopy` ✅ Fixed

**Current problem:** `simulation_manager.py` line 60:

```python
input = copy.deepcopy(data)
```

This deep-copies the data snapshot on **every** activity execution. For large forms this is expensive and usually unnecessary (the snapshot is only needed to log `data_input`, which doesn't change after this point).

**Fix:** Copy only the data fields needed for logging, not the entire data graph. Or delay copying until the log item is constructed.

**File:** `simulation_manager.py` — `_simulate_activity()`

---

### 3.2 Code Clarity & Architecture

#### 3.2.1 — Decompose `_simulate_activity()` ✅ Fixed

This is a 73-line function with a `# TODO: Refactor this function.` comment at line 53. It handles resource allocation, failure, timeout, data processing, logging, and successor queuing all in one place with 4 levels of nesting.

**Proposed decomposition:**

```
_simulate_activity(item)
  ├── _read_activity_data(item)         → data dict
  ├── _allocate_resources(item, data)   → (assigned, new_item_if_postponed)
  ├── _log_start(item, assigned, data)
  ├── _check_failure(activity)          → bool
  ├── _handle_failure(item, assigned)
  ├── _check_timeout(duration, timeout) → bool
  ├── _write_activity_data(item, data)
  └── _log_end(item, assigned, output)
```

Each sub-function is testable in isolation.

**File:** `simulation_manager.py`

---

#### 3.2.2 — Fix `QueueItem` Mutation Pattern ✅ Fixed

`repeat()`, `leftover()`, and `postpone()` mutate `self` and return `self`. This looks like a builder pattern but isn't — the caller must immediately push the returned value to the queue. If they don't, mutations accumulate silently.

**Fix:** Make these return **new** `QueueItem` instances (shallow copy + override). The memory overhead is negligible (these are small objects) and the intent becomes clear.

**File:** `execution_queue.py`

---

#### 3.2.3 — Fix `QueueItem.__lt__` Ordering ✅ Fixed

```python
# Current — when priorities equal AND process_ids equal:
self.process_instance_id > other.process_instance_id  # higher ID = "less than" = processed first???
```

The intent (from the paper): older instances (lower ID, having waited longer) should have priority. But `>` makes higher IDs go first — which is the opposite. Either the intent or the comparison is wrong. Clarify and document.

**File:** `execution_queue.py` — `__lt__`

---

#### 3.2.4 — Gateway Type Mutation ✅ Fixed

In `gateway.py`, a gateway initialized as `type='choice'` silently has its type changed to `'rule'` during `__init__` if a rule function is present. This means the type stored on the object doesn't match what was specified in XML, and code that branches on `gateway.type` must know about this implicit aliasing.

**Fix:** Keep `type='choice'` and store `self.is_rule_based = rule is not None`. Or add `'rule'` as a proper gateway type in the XML (it's already in `config.py`).

**File:** `gateway.py`

---

#### 3.2.5 — Eliminate Magic Strings ✅ Fixed

`"END"` appears as a hardcoded string in `activity.py`, `process.py`, `model_builder.py`, and `simulation_manager.py`. Any typo silently breaks process termination.

**Fix:** Add to `config.py`:
```python
SENTINEL = {'end': 'END', 'start': 'START'}
```
Replace all string literals.

**Files:** `config.py`, `activity.py`, `process.py`, `model_builder.py`

---

#### 3.2.6 — `duration.py` Cleanup ✅ Fixed

- `isinstance(distribution, dict)` instead of `type(distribution) is dict`
- Don't mutate the input dict (bug #4 above also)
- Raise `ValueError` for unknown distribution types instead of returning `None` silently
- Add parameter validation (e.g., beta requires a, b > 0)

**File:** `duration.py`

---

#### 3.2.7 — `model_builder.py` Cleanup ✅ Fixed

- Remove the list comprehension used purely for side effects (line 191): `[attributes.update(...) for ...]` → use a `for` loop
- Fix the suspicious `'Duration/'` XPath (line 76) — trailing slash is not standard
- Deduplicate `DataInput`/`DataOutput` parsing (lines 83-119 are nearly identical) → extract `_parse_data_requirements(node)`
- Fix condition on line 114 where `org is not None` is required even when other filters are None (should be OR logic matching the intent of partial resource specification)
- Remove `pass` after `return` on line 312

**File:** `model_builder.py`

---

### 3.3 Modeling Ergonomics (XML Usability)

The current XML requires enormous manual effort. A 7-day model with 4 processes takes 559 lines. Most of it is copy-paste repetition.

#### 3.3.1 — Arrival Rate Defaults

**Current:** Must specify every hour block for every day of the week, even when Mon–Sun are identical:

```xml
<Mon><TimeBlock start="0" end="6">5</TimeBlock>...</Mon>
<Tue><TimeBlock start="0" end="6">5</TimeBlock>...</Tue>
<!-- × 7 days -->
```

**Fix:** Add a `<Default>` block that applies to all unspecified days:

```xml
<ArrivalRate>
  <Default>
    <TimeBlock start="0" end="6">5</TimeBlock>
    <TimeBlock start="6" end="18">12</TimeBlock>
    <TimeBlock start="18" end="24">6</TimeBlock>
  </Default>
  <Sat><TimeBlock start="0" end="24">3</TimeBlock></Sat>
  <Sun><TimeBlock start="0" end="24">3</TimeBlock></Sun>
</ArrivalRate>
```

Reduces arrival rate specification from 7 identical blocks to 1 default + exceptions.

---

#### 3.3.2 — Resource References Instead of Inline Specs

**Current:** Every activity fully re-specifies the resource:

```xml
<Resource class_type="human" org="Company, Inc." dept="Customer Experience" role="Support">1</Resource>
```

**Fix:** Resources defined once in `resources.xml` get an ID. Activities reference by ID:

```xml
<!-- resources.xml -->
<Resource type="human" id="support">...</Resource>

<!-- activities.xml -->
<Resources>
  <Resource ref="support" quantity="1"/>
</Resources>
```

---

#### 3.3.3 — Transition Delay Default

Every transition in `models.xml` has the same boilerplate:

```xml
<Transition source="read" destination="bug">
  <Duration><Distribution type="Const" value="10"/></Duration>
</Transition>
```

**Fix:** `<Duration>` on a `<Transition>` should be optional, defaulting to 0. Users only specify it when there's a meaningful travel/handoff delay.

---

#### 3.3.4 — Activity Overrides in Model Context

**Current pattern** (already exists but is verbose): Activities are defined globally in `activities.xml`, then listed in `models.xml` with optional field overrides. The override syntax requires re-specifying the full element:

```xml
<Activity id="read">
  <DataOutput>
    <DataObject id="ticket"><Fields><Field name="Class"/></Fields></DataObject>
  </DataOutput>
</Activity>
```

**Fix:** Keep this pattern but support attribute-level overrides with less nesting:

```xml
<Activity id="read" duration_mean="600" priority="high"/>
```

Common single-value overrides shouldn't require full sub-element nesting.

---

#### 3.3.5 — Resource Availability Template

**Current:** Mon–Fri are specified identically 5 times for each resource type.

**Fix:** Add `<WeekdayTemplate>` that applies to Mon–Fri by default, with day-specific overrides:

```xml
<Availability>
  <Weekday>
    <TimeBlock start="9" end="17"/>
  </Weekday>
  <Sat><TimeBlock start="10" end="14"/></Sat>
  <!-- Sun: not available (no entry = unavailable) -->
</Availability>
```

---

#### 3.3.6 — Validate Rules/Data Functions at Load Time

Currently, if `rules.py` is missing a function for a gateway, the error occurs mid-simulation when the gateway is first encountered. With potentially millions of events before that gateway fires, debugging is painful.

**Fix:** In `ModelBuilder.build_all()`, after parsing all gateways, verify that every rule-based gateway's function exists in the rules module. Same for activity data functions. Fail fast with a clear error:

```
ConfigurationError: Gateway 'bug' references rule function 'bug' which was not found in input/rules.py
```

**File:** `model_builder.py` — `build_all()`

---

## 4. Extra Features (New Functionality)

These are beyond the current scope and should not block the core refactor.

### 4.1 Multi-Resource Support Per Activity
The paper calls this out explicitly as future work. Currently `assign_resources()` only processes the first resource requirement (bug #3 above). True fix requires:
- Accumulating all resource assignments before logging start_activity
- Handling partial availability across multiple resource types (e.g., resource A available from 9am, resource B from 10am → activity starts at 10am)
- Rolling back partial assignments if any resource in the set is unavailable

### 4.2 Inclusive / Exclusive Resource Requirements
Also from the paper: "inclusive" requirements (need engineer AND designer) vs "exclusive" (cashier OR manager). Currently only one resource type per activity, and there's no OR logic.

### 4.3 Simulation Seeding for Reproducibility
`numpy.random` supports seeding. Accepting a `--seed` parameter in `main.py` + passing it to `np.random.seed()` before simulation would make runs reproducible — critical for debugging and research comparison.

### 4.4 Intermediate Events
The paper flags the absence of intermediate events as a limitation. These model external triggers (customer callback, timer expiry, error notification) that interrupt or resume process instances.

### 4.5 Deadlines Actually Enforced
Process models have a `<Deadline>` value that is parsed (line 234 in `model_builder.py`) but it's unclear if it's enforced anywhere in `SimulationManager`. Verify and implement: instances exceeding their deadline should log a `deadline_exceeded` event and halt.

### 4.6 XML Schema Validation
Add an XSD schema file for each XML input type. `model_builder.py` has `# TODO: Implement XML validation` at line 14. With schema validation, misconfigured models fail at load time with clear field-level errors instead of cryptic mid-simulation crashes.

### 4.7 BPMN Import
The paper suggests importing BPMN-compliant files from other tools. Lower priority but would dramatically reduce modeling effort for users with existing process diagrams.

---

## 5. Implementation Roadmap

### Phase 1 — Bugs (do immediately, no design changes)
1. Fix `log.py:26` — comparison bug
2. Fix `resource.py:72` — `next()` on list
3. Fix `duration.py:10` — dict mutation
4. Fix `duration.py:19-27` — `round()` instead of `int()`
5. Fix `resource.py` `_search_physical()` — double `check_free()` call
6. Fix `resource.py` `assign_resources()` — early return drops all but first resource

### Phase 2 — Performance ✅ Complete (16× speedup achieved)
1. ✅ Transition lookup index in `Process.get_next()`
2. ✅ Role index + shuffle removal in `ResourceManager`
3. ✅ Per-resource-type wait queues in `SimulationManager`
4. ✅ Eliminate hot-path `deepcopy`

### Phase 3 — Code Clarity ✅ Complete
1. ✅ Decompose `_simulate_activity()` into sub-functions
2. ✅ `QueueItem` immutable mutation methods; remove dead `postpone()`
3. ✅ Fix `QueueItem.__lt__` ordering and document intent
4. ✅ Fix gateway type mutation
5. ✅ Eliminate magic `"END"` / `"START"` strings
6. ✅ `duration.py` and `model_builder.py` cleanup

### Phase 4 — Modeling Ergonomics (XML)
1. Transition delay default (zero if omitted)
2. Arrival rate `<Default>` block
3. Resource `ref=` attribute in activities
4. Availability `<Weekday>` template
5. Validate rules/data functions at load time (fail-fast)

### Phase 5 — Extra Features (as prioritized)
1. Simulation seeding (very small effort, high research value)
2. Deadline enforcement
3. Multi-resource support
4. Inclusive/exclusive resource requirements
5. Intermediate events
6. XML schema validation

---

## 6. Critical Files Reference

| File | Primary Role | Key Issues |
|------|-------------|------------|
| `simulation_manager.py` | Orchestrator | Monolithic `_simulate_activity`, `deepcopy` hot path, merge gate dict structure |
| `resource.py` | **Main perf bottleneck** | Shuffle+scan, stateful heap, broken cache, O(n) `check_free`, incomplete multi-resource |
| `process.py` | Process graph | O(n) transition scan (hot path), needs index |
| `execution_queue.py` | Event queue | Mutable item methods, questionable `__lt__` |
| `gateway.py` | Flow control | Type mutation, fragile dynamic function loading |
| `model_builder.py` | XML parsing | Duplicate code, logic errors, no validation |
| `log.py` | Output | Self-comparison bug |
| `duration.py` | Sampling | Dict mutation bug, truncation bias |
| `input/models.xml` | Config | 559 lines, 95% repetition |
| `input/resources.xml` | Config | 5× duplicate availability blocks |
