# Requirement and release ledger

This is the coordinator's cross-stage gate map. Detailed clause tests belong to the independently authored stage coverage reports. Status is pending until a reviewer names the exact committed revision and evidence. Published samples alone do not establish conformance.

| Contract | Required evidence and difficult transitions | Status |
|---|---|---|
| S1 §§2–3 deployment/runtime | Standalone image, PORT, healthy within 60s, JSON errors, 2 CPU/2 GiB, no runtime outbound traffic, arbitrary fixture reset | Pending |
| S1 §§4–6 model/auth/errors | Opaque IDs, past-date creates, unknown fields, wrong-type versus invalid-value precedence, hashed passwords, simultaneous sessions, owner isolation | Pending |
| S1 §7 receipts | User/method/path scope, JSON-value equality, unknown-field body differences, replay before validation, original response after edits, 50 identical concurrent writes, failed-key reuse | Pending |
| S1 §8 bookings | Half-open adjacency, capacity, grid/opening, cutoff boundary, no-op/cancel repeat, sort by instant, failed amendment leaves original occupancy | Pending |
| S1 §9 time | IANA arbitrary dates, spring gaps, first fold occurrence, absolute duration across transitions, closing instant | Pending |
| S1 §10 state transfer | Atomic replacement, unchanged exports, repeat imports, credentials/tokens/receipts retained, corrupted state rejected without mutation, source-independent use | Pending |
| S1 §11 moves | 1–8 distinct references, swaps, unchanged listed occupancy, input-order non-occupancy precedence, mixed-owner/restaurant, complete rollback | Pending |
| S2 API combinations | Only declared unordered pairs, canonical order, sum capacity, both occupancy members, single compatibility, invalid sets, atomic batch pairs | Pending |
| S2 browser | Required routes/hooks, signup/login/logout, labels, 375px/desktop, stale search generations, conflict refresh without form loss, uncertain exact-body/key retry, repeated success | Pending |
| S2 migration | S1 export with active tokens and lost-response receipt imports while browser remains signed in and pending retry survives | Pending |
| S3 explanations/history | Independent capacity/overlap rules, full order, owner-only 404 including anonymous, contiguous history, no-op/replay silence, pair transitions | Pending |
| S3 policies/terms | Manager isolation, complete validation, same-date tie, out-of-order publication, past effective dates, immutable accepted terms, original receipt, old cutoff then new-policy validation | Pending |
| S3 revisions | Stale revision before cutoff, bool rejection, concurrent CAS, once-per-operation counters, unchanged no-op terms | Pending |
| S3 recurring | Anchor unchanged, count/interval limits, local calendar recurrence, DST rollback, generated per-date policy, permanent individual exceptions, cancellation independence | Pending |
| S3 collective/migration | Batch series increments once, real-change exceptions only, S1/S2 imports with history and adoption preserving identities | Pending |
| S4 closure optimization | Exhaustive independent oracle within 6 tables/4 pairs/6 bookings; changed count then unused seats then reference-order option ranks; fixed bookings and earlier closures constrain assignments | Pending |
| S4 preview/apply | Read-only preview, accepted-capacity use, cutoff-independent repairs, stale restaurant revision, atomic concurrent apply, original apply receipt, unaffected restaurant independence | Pending |
| S4 history/series | Reassigned history has plan ID and table_ids, accepted terms/time unchanged, exceptions/scheduled dates retained, each affected series increments once | Pending |
| S4 recurring amendments | Required CAS, original scheduled dates, skip cancelled/exceptions, index error precedence, all-or-nothing occupancy, no-op/empty eligible success, concurrent change at most once | Pending |
| S4 migration | Imports from all predecessors preserve old booking/series receipts, cancelled/moved occurrences and opaque identities | Pending |

Each accepted stage folder must contain its own Dockerfile, RUN.md, source, tests and offline assets. No symlinks, submodules or nested Git directories are allowed. Final verification runs all folders from the result repository and a clean clone, then runs offline `harness check`. The authentic room export is supplied after the autonomous run and remains an explicitly pending gate until present.

## Accepted revision chain

Stage 1 accepted: implementation `8a2a07abfe972815cfea7c02176a075b8b2accaf`, package tree `2a5107fedec409dd152484de88ede68b861e008b`, complete folder/evidence revision `3813508b5624b4ae89a346b68611a595f83cfde5`. Official host and isolated suites both 120/120; expected stage-2 rejection is the absent search UI. Independent HTTP and network-none checks each 23/23; implementation tests independently rerun 24/24. Fresh-process transfer, 22 malformed-import variants and disabled test controls passed. See [exact commands and durations](../evidence/stage-1/verification.md). Stage-1 matrix rows above are satisfied by that report; later-stage rows remain pending. Hidden judging checks are unavailable.

## Evidence convention

Stage 2 accepted: implementation `e4fc1c5bf52769927b50e139be1d380b1c044aeb`, complete evidence/folder revision `f2e3189db5f113f9b38509cc57241d9e50d91330`. Official host and isolated inherited/current suites 120/120 + 25/25; independent HTTP 30/30 plus 2/2 source-review cases, seven browser scenarios including actual stage-1 pending-retry upgrade, author tests independently rerun 41/41. Expected stage-3 overshoot rejection. See [stage-2 commands, durations and limitations](../evidence/stage-2/verification.md). Stage-2 matrix rows are satisfied by that report; stage-3/4 remain pending.

Record exact command, UTC start/end or elapsed duration, exit status, full Git revision, counts and limitations. Preserve failed attempts. Use a new harness output directory each time and keep exports carrying tokens outside this repository. Expected overshoot failures are identified separately from contract regressions.
