# Firestore orphan-lock and RPC deadline repair

Coordinator reported independent `20260927T185258029932Z-security-crash-recovery-70cf83c.log`: 11 passed, one Firestore before-commit HTTP recovery failure in 54.63s. The failed client read timed out. The original evidence remains unchanged.

Source inspection of pinned google-cloud-firestore2.21.0 showed `Transaction._begin`, `_commit` and `_rollback` call generated RPCs without explicit timeout/retry arguments. The generated commit path exposed a 60-second RPC default in the original traceback. A backend15-second socket deadline did not cancel that thread's storage work.

Repair source is committed as `ca1f02b21da70f26cefdc525728f3def59481650`. The SDK GAPIC boundary now applies a thread-local monotonic eight-second shared network budget, four-second per-RPC ceiling and no automatic RPC retries. Rollback receives at most one extra second for cleanup. SDK aborted-transaction reruns remain at most five and use the same cumulative budget. Existing-main startup uses a read-only validated snapshot rather than acquiring a write transaction. Missing-main creation is still transactional. No emulator-specific storage path or relaxed state check was introduced.

Author commands executed from `/Users/shivamgupta/.codex/worktrees/tablekeeper-pilot/we-are-developers` on the working repair that was then committed as ca1f02b:

```sh
FIRESTORE_EMULATOR_HOST=127.0.0.1:18980 PYTHONPATH=product /Users/shivamgupta/.cache/tablekeeper-engineer-venv/bin/python -m pytest -q product/tests/author_firestore.py
FIRESTORE_EMULATOR_HOST=127.0.0.1:18980 PYTHONPATH=product /Users/shivamgupta/.cache/tablekeeper-engineer-venv/bin/python -m pytest -q -s product/tests/author_firestore.py::test_orphan_lock_recovery_has_bounded_attempts_and_one_receipt
PYTHONPATH=product /Users/shivamgupta/.cache/tablekeeper-engineer-venv/bin/python -m pytest -q product/tests/author_companion.py
```

Results: existing six Firestore checks passed in5.39s; new orphan recovery check passed in61.13s;16 companion checks passed in1.72s. These are pytest durations, not separately wrapped whole-command wall times. The orphan test used a unique `author_` collection in the local `demo-proofline-pilot` emulator, killed a live transaction before commit, and retried the exact original body/key. Its directly measured result was:

```json
{"orphan_recovery_seconds":60.477,"attempts":[{"seconds":8.067,"outcome":"retryable_unknown"},{"seconds":8.067,"outcome":"retryable_unknown"},{"seconds":8.064,"outcome":"retryable_unknown"},{"seconds":8.072,"outcome":"retryable_unknown"},{"seconds":8.062,"outcome":"retryable_unknown"},{"seconds":8.062,"outcome":"retryable_unknown"},{"seconds":6.054,"outcome":"success"}]}
```

After release, the store contained exactly one new booking and one original receipt; an immediate same-key replay returned the identical successful body with200. Each failed attempt remained below10seconds. The overall observation window was75seconds, informed by [Firestore's documented60-second idle expiry](https://firebase.google.com/docs/firestore/quotas), without expanding individual request waits. This is measured emulator behavior, not a claim of deployed lock-release timing or an SLA. Real deployment remains an operator gate.

Verifier was asked to retain the original failure, independently measure bounded HTTP responses and eventual original-receipt recovery, and use a bounded overall idle-expiry observation window rather than repeated unbounded client waits. Independent acceptance is not inferred from this author run.
