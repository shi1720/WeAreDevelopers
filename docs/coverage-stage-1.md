# Stage 1 independent requirement coverage

Source: complete official stage-1 specification, immutable kickoff revision `803560d2a678ace1414465c098eb0ab5380ffade`. The participant guide and all four contracts were read before authoring checks. Tests were derived before reviewing implementation or published tests. Ownership: Proofline Verifier. This is a coverage plan, not a pass claim.

| Contract | Independent coverage | Remaining acceptance evidence |
|---|---|---|
| §1 occupancy, half-open duration, failure atomicity | Adjacent slots, overlapping creates, failed PATCH, swaps and rejected batches | Source locking/transaction review; official suite |
| §2 single image, CPU/memory, offline runtime, startup, 50 concurrency | HTTP request deadline assertions; two distinct 50-way races | Dockerfile/RUN review, isolated official execution, measured startup |
| §3 health, listening, reset, JSON, offsets, opaque IDs | Health, public calls, charset, reset token revocation, response IDs and timestamp checks | PORT override/container interface and full ID length review |
| §4 arbitrary fixtures/dates, past bookings, seeded users | Synthetic tables in nonlexical order, all weekdays, past create, immediate seeded login | Seeded reservation exact identity and cross-restaurant fixtures |
| §5 malformed versus invalid, special field precedence | Bad body shapes, party booleans/strings/fractions, local timestamp grammar, query decimal grammar, error envelopes | Exhaustive implementation field validation review |
| §6 signup/login, sessions, owner isolation, password hashing | Duplicate signup, invalid signup, login failures, multiple tokens, private reads/writes, no plaintext in export | Hash function and parameters review; concurrent signup |
| §7 idempotency scope/limits/precedence/original receipts | 255/256 chars, empty/missing, JSON key order, unknown value differences, boolean versus number, user/path scope, failed-key reuse, post-cancel replay, 50 identical writes | Official suite and source receipt atomicity review |
| §8 public restaurants and availability | Fixture order, closed day, empty rows, non-hour opening grid, availability occupancy | Unknown restaurant/table permutations and listing descending |
| §8 create/cancel/PATCH | Capacity, grid, close, overlaps, immutable identity, repeated cancel, cancelled PATCH, old start cutoff | Exact cutoff boundary by time-controlled fixture, cancellation releases all expected intervals |
| §9 DST | 2030 Berlin/New York spring gaps and fall folds, one repeated slot, absolute duration | Additional non-hour zone transition and opening/closing transition review |
| §10 export/import | Sessions, passwords, identities, original create/batch receipts, replacement, repeat import, invalid envelope/state rollback | Fresh-process transfer, structural corruptions discovered from schema, concurrent snapshot consistency |
| §11 atomic moves | Swap, unchanged item, occupancy rollback, shape/duplicates/max, owner rule, input error order, cutoff before proposed validation, original receipt | Eight-item valid batch, cross-restaurant rejection, simultaneous batch visibility |

The independent suite uses only HTTP and standard-library Python. Set `TABLEKEEPER_BASE_URL` to a disposable instance; every test resets it. Tokens and exported state remain in memory, and assertion messages suppress successful authentication/export payloads. No official test or implementation module is imported.

Pending gate: coordinator must freeze an exact committed revision before acceptance execution. Run commands, exit codes, durations, failures, fixes and isolated evidence will be recorded in `evidence/stage-1/`. Later-stage contracts inform extensibility review only; no future feature is required in this folder.
