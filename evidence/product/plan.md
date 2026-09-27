# Tablekeeper operational companion

This is a separately traced companion, not a graded stage. Baseline: `330f1c8321670ca7d34b6b7127c0fb73df84ca25`. Preserve all original graded folders and commits. Shivam Gupta leads product and factory direction; the configured coding seats implement and independently verify.

1. Engineer commits the complete unchanged stage-4 tree into product and records matching tree hashes in evidence/product/baseline.json. No other product writes before this gate.
2. Agree cookie/CSRF, setup, booking edit/list, roster, demo and retry interfaces. Engineer owns backend, persistence, packaging and operations; Experience owns static UI and user/demo documentation. Verifier owns independent acceptance tests and evidence.
3. Implement durable SQLite and Firestore adapters, secure first-run setup and sessions, isolated bounded demos, backups and recovery. Preserve all original domain invariants and exact receipts. In parallel, implement presentation-ready setup, booking recovery/edit, roster and pending-request recovery UI.
4. Freeze a committed candidate. Verifier independently tests Python 3.12, offline SQLite container at 2 CPU/2 GiB, Firestore emulator with multiple processes, failures/restarts/backups/auth/isolation, inherited domain contracts and real desktop/mobile browser flows. Preserve failed checks and repair commits; rerun scoped repairs before final gates.
5. Accept only an independently verified immutable revision. Publish clause coverage, commands/status/duration, screenshots, provenance, limitations, elapsed time and honestly available usage. Operator retains cloud provisioning, deployed Firestore gate, publication and room export.

Release constraints: one venue per namespace, 1-6 tables, at most 4 pairs, at most 6 overlapping confirmed bookings for closure planning; production has no test routes or seeded accounts; hosted authority is Firestore with ADC, never SQLite. No real data or secrets, no cloud deployment by seats, no push/merge/history rewriting. Unknown or unexecuted coverage remains explicit.

