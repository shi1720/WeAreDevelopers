# Partial store corruption repair

Runtime repair: `8d00205c67f2769240f65f24d3afe39fcf8fccb4`. Scoped author run `20260927T191032011628Z.json` records 10 passing tests, exit 0, 0.580143 seconds including runner overhead. Independent acceptance remains the verifier's responsibility.

Two preliminary author checks were not captured by the evidence runner and are recorded here without inventing full logs or exact revisions. They ran against the uncommitted repair:

- Startup-focused pytest selection initially returned 1 failed, 4 passed, 16 deselected in 0.08 seconds. The fixture inserted an unrelated SQLite row then requested WAL checkpoint before committing, raising `sqlite3.OperationalError: database table is locked` before application startup. The fixture now commits before checkpoint; rejection assertions remain unchanged.
- `FIRESTORE_EMULATOR_HOST=127.0.0.1:18980 PYTHONPATH=product /Users/shivamgupta/.cache/tablekeeper-engineer-venv/bin/python -m pytest -q product/tests/author_companion.py product/tests/author_firestore.py -k 'not orphan_lock'` returned 1 failed, 31 passed, 1 deselected in 11.23 seconds. Existing `test_two_live_processes_serialize_booking` expected both subprocesses to succeed immediately. One received the bounded `StoreError: Firestore transaction unavailable; retry the unchanged request`, following DeadlineExceeded and emulator rollback `Can't swap from CLOSED to ACTIVE`. This run is not a concurrency acceptance pass. The test was not weakened or changed. Independent exact-operation retry and crash gates reported separately by the verifier cover bounded recovery.

The repair rejects an existing unsupported SQLite schema/marker or invalid revision before database mutation, retains zero-byte initialization and exact legacy schema support, refuses missing Firestore roots with surviving known chunks, and bounds malformed setup owner values with validation errors before domain changes. No domain invariants or independent assertions changed.
