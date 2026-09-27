# Companion engineering

The unchanged stage-4 domain is extended through `tablekeeper/companion.py` and `tablekeeper/storage.py`. Domain operations still derive private candidate state. SQLite commits with exclusive writer ownership; Firestore commits namespace roots, revisions and bounded byte chunks transactionally across processes. Successful receipts are stored in the same transaction as the effects.

Auth uses durable digested cookie sessions, CSRF and exact Origin checks. One-time setup, isolated public demos, bounded operational lists, private backups and maintenance/CAS restore are documented in [operations](docs/operations.md).

[Engineer coverage](../evidence/product/engineering/coverage.md) maps the requirements to implementation and author evidence. It is not independent acceptance. [Baseline provenance](../evidence/product/baseline.json) records the unchanged source and destination tree hashes. Original implementation and historical reports remain in the original stage folders and the first-copy commit.

The original temporal, availability, reservation, policy, series, planner, history and portability modules preserve half-open UTC occupancy, IANA gaps/folds, declared-pair selection, immutable accepted terms, append-only history, permanent recurring exceptions, collective atomic CAS and deterministic bounded global closure planning. The companion adds durable extra receipts for individual edit/cancel without rewriting inherited receipt contracts.

Author checks from this folder:

```sh
PYTHONPATH=. python3.12 -m pytest -q tests/author_companion.py tests/test_temporal.py tests/test_availability.py
FIRESTORE_EMULATOR_HOST=127.0.0.1:18980 PYTHONPATH=. python3.12 -m pytest -q tests/author_firestore.py
```

The Firestore author suite uses the synthetic emulator project `demo-proofline-pilot` and unique `author_` collections. Install the hash-locked requirements first. Independent tests are maintained by Verifier, browser implementation/tests by Experience, and final acceptance/reporting by Coordinator. Agent-generated code is credited to those coding seats; Shivam Gupta leads project, product and factory configuration.
