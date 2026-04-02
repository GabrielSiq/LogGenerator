# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
pip install -r requirements.txt
```

## Running the Simulator

Use `main.py` as the CLI entry point:

```bash
# Run the built-in example (defaults to last 7 days)
python3 main.py

# Custom date range and output name
python3 main.py --start 2024-01-01 --end 2024-01-31 --name january_run

# Override resource quantities at runtime
python3 main.py --start 2024-01-01 --end 2024-01-07 --resource-limit support=20 trust=5

# Use a different input directory
python3 main.py --input my_process/ --name my_run

python3 main.py --help  # show all options
```

Output is written to `output/` (or `--output DIR`) as a JSON file.

## Architecture

This is a discrete-event business process simulator that generates synthetic event logs for process mining/BPM research (academic project, UCSB CS). The goal is to simulate realistic multi-process business environments with shared resources and produce structured logs for algorithm development.

**Execution flow:**
1. `ModelBuilder` parses XML files in `input/` into in-memory objects (processes, activities, gateways, resources, data)
2. `SimulationManager` drives a priority queue (`ExecutionQueue`) ordered by timestamp → priority level → instance ID (older instances win ties)
3. Each dequeued item is either an `Activity` or `Gateway`; activities consume resources and log events, gateways route control flow
4. `LogWriter` (`log.py`) writes events to `output/` as JSON

**Key design patterns:**
- **Resource contention:** Three outcomes when assigning resources: full assignment, partial (activity pauses mid-execution and re-queues as `leftover()`), or none (re-queues with `postpone()`). Input data is snapshotted at start and held; output is only written on successful completion — failed/timed-out activities do not write data.
- **Merge gateways:** Track all incoming flows in `pending_merges`; only proceed when all branches have arrived. Start time is set to `max(arrival times) + 1s`.
- **Rule gateways:** A Choice gateway variant that delegates routing to custom functions in `input/rules.py` based on current process data.
- **Data functions:** Custom transformations during activity execution are defined in `input/data.py`.
- **Performance:** Resource-constrained scenarios can be significantly slower (up to 5x) — every time a resource frees, all queued activities waiting for it are re-evaluated.

## Input Configuration

All process definitions live in `input/` as XML files. Activities are a **global library** shared across all process models; individual parameters can be overridden when referenced in `models.xml`.

- `activities.xml` — global activity definitions: durations (Normal/Uniform/Triangular/Beta/Const distributions), resource requirements, failure rates, retries, timeouts, data I/O, priority
- `models.xml` — process models: arrival rates (by day/hour time blocks), activity/gateway/transition sets, and a `Deadline` (instances exceeding it are suspended)
- `resources.xml` — resource pool shared across all processes: human (org/dept/role, quantity) or physical (type), with per-day availability `<TimeBlock>` schedules
- `data.xml` — data object (form) definitions with field names
- `input/rules.py` — Python functions for rule-based gateway routing decisions
- `input/data.py` — Python functions for activity data transformations

Default paths are defined as constants in `config.py`.

## Output Format

`LogWriter` outputs **JSON** — the canonical designed format. Each log record contains: `log_id` (LSN), `timestamp`, `date`, `process_id`, `process_instance_id`, `activity_id`, `activity_instance_id`, `status`, `data_input`, `data_output`, `resource`. Possible status values: `start_activity`, `end_activity`, `pause_activity`, `failed`, `timeout`, `waiting_resource`. `None` fields are omitted from output.
