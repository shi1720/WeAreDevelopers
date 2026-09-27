# Early author checks and preserved failures

These are author executions, not independent acceptance. Commands ran in `/Users/shivamgupta/.codex/worktrees/tablekeeper-pilot/we-are-developers`. Initial source was a working draft after baseline `1448eea24239a59e03941fc3a1a691b86bad19d9`; the implementation was then committed as `70cf83c8de4c67babab92973264913c2ccc7b984`. Other seats committed their owned files concurrently. Earlier checks were not wrapped by the later exact wall-clock recorder; reported pytest durations below are pytest's measured durations, not invented whole-command timings.

| Check | Exact command | Result |
| --- | --- | --- |
| Initial SQLite/operational author checks | `PYTHONPATH=product /tmp/proofline-official-spec/.venv/bin/python -m pytest -q product/tests/author_companion.py` | Exit 0, 6 passed in 0.36s; expanded draft later 8 passed in 0.78s |
| Inherited local domain units plus author checks | `PYTHONPATH=product /tmp/proofline-official-spec/.venv/bin/python -m pytest -q product/tests/author_companion.py product/tests/test_temporal.py product/tests/test_availability.py` | Exit 0, 24 passed and 14 subtests in 0.55s, before two additional author tests |
| HTTP suite author rehearsal at 70cf83c | `PYTHONPATH=product /Users/shivamgupta/.cache/tablekeeper-engineer-venv/bin/python -m pytest -q product/tests/acceptance_http.py` | Exit 0, 8 passed in 4.00s; verifier's separate execution is authoritative |
| Initial Firestore author suite | `FIRESTORE_EMULATOR_HOST=127.0.0.1:18980 PYTHONPATH=product /Users/shivamgupta/.cache/tablekeeper-engineer-venv/bin/python -m pytest -q product/tests/author_firestore.py` | Exit 1, 5 passed and 1 failed in 11.32s |
| Corrected SDK retry driver, scoped | `FIRESTORE_EMULATOR_HOST=127.0.0.1:18980 PYTHONPATH=product /Users/shivamgupta/.cache/tablekeeper-engineer-venv/bin/python -m pytest -q product/tests/author_firestore.py::test_sdk_callback_retry_uses_private_candidate` | Exit 0, 1 passed in 0.13s |
| Schema fix and stable-key contention rehearsal | `FIRESTORE_EMULATOR_HOST=127.0.0.1:18980 ACCEPTANCE_FIRESTORE_PROJECT=demo-proofline-pilot PYTHONPATH=product /Users/shivamgupta/.cache/tablekeeper-engineer-venv/bin/python -m pytest -q product/tests/acceptance_storage.py::test_operational_schema_corruption_rejected product/tests/acceptance_storage.py::test_firestore_multiprocess_counter_and_revision` | Exit 0, 9 passed in 20.60s |

## Preserved author test-driver failure

The first `test_sdk_callback_retry_uses_private_candidate` replaced `Transaction._commit` with this branch:

```python
calls.append(True)
if len(calls) == 1:
    raise Aborted('synthetic retry')
return original(transaction)
```

That raised locally while leaving the first emulator transaction and its lock live. The SDK's retry then failed with `google.api_core.exceptions.Aborted: 409 Transaction lock timeout`, followed by `ValueError: Failed to commit transaction in 5 attempts`, wrapped as `StoreError: Firestore transaction unavailable; retry the unchanged request`. This did not simulate a server abort correctly. The correction rolls back that server transaction before raising the synthetic Aborted. Assertions remain: callback runs twice, returned counter is 1 and durable counter is 1. The original five passing cases covered two live booking processes, 4MiB/eight-chunk boundary and hash corruption, both crash boundaries, and concurrent backup/CAS restore.

## Preserved container startup failure

Build command: `DOCKER_HOST=unix:///Users/shivamgupta/.colima/default/docker.sock DOCKER_CONFIG=/tmp/proofline-public-docker-config /opt/homebrew/bin/docker build -t tablekeeper-companion:author product`. Initial build exited 0, image `9512e71e0ab8`. Initial container command used `--name tablekeeper-author-smoke --network none --cpus 2 --memory 2g -v tablekeeper-author-smoke:/data -e TABLEKEEPER_MODE=development -e TABLEKEEPER_PUBLIC_ORIGIN=http://localhost:8080 -e TABLEKEEPER_PUBLIC_DEMO=1 tablekeeper-companion:author`; Docker creation exited 0 but the service container stopped. Readiness exec exited 1 because it was not running. The retained log reported:

```text
2026/09/27 18:32:27 [emerg] 8#8: mkdir() "/var/lib/nginx/fastcgi" failed (13: Permission denied)
```

The image runs unprivileged. nginx's unused default FastCGI/uWSGI/SCGI temporary directories still required creation. Explicit `/tmp` paths fixed startup; rebuilt image `74977560d4d9` ran as `tablekeeper-author-smoke-fixed` under the same network-none, 2 CPU, 2GiB constraints. `docker exec ... python -c` requests to `/health/ready` and `/auth/session` returned 200; readiness body was `{"status":"ready"}`, cache was `private, no-store`, setup was required, user was null and `__session` was set. This limited smoke is not the full independent container/restart gate.

## Real review findings retained

Verifier's immutable 70cf83c storage run found malformed `maintenance='locked'` accepted. Repair validates null or exactly `{since: finite nonnegative timestamp}`. Coordinator additionally found callback nonlocal token mutation, anonymous-session capacity exhaustion and demo-reset recovery scope reuse. Repair makes token callback-local, reserves authenticated capacity with a bounded anonymous pool/rate, and rotates the reset generation. No graded source, original test, original commit, or failed independent evidence was removed or rewritten.
