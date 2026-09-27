# Current operator status

Supplement added after the original run; the historical coordinator ledger below is preserved unchanged. All four stages have acceptance evidence. The authentic full [room export](../room.json) is present. The [post-export package check](../evidence/final/package-check.md) passed, and the [unauthenticated public-clone check](../evidence/final/public-clone-check.txt) at `fb76fd0487212119f5b0fa7e6f7722057b93ddd7` confirmed public access, matching stage trees/room fingerprint and checker exit 0. Earlier statements about missing export or pending stage gates describe their historical observation, not current status.

These package checks do not replace the [isolated service evidence](../evidence/final/verification.md). The mandatory recorded video and separate hosted companion remain pending until their own verified results are published. Start with the [three-minute judge guide](JUDGE-GUIDE.md) for the evidence trail and disclosed runtime restart.

---

# Requirement and release ledger

This is the coordinator's cross-stage gate map. Detailed clause tests belong to the independently authored stage coverage reports. Status is pending until a reviewer names the exact committed revision and evidence. Published samples alone do not establish conformance.

| Contract | Required evidence and difficult transitions | Status |
|---|---|---|
| S1 §§2–3 deployment/runtime | Standalone image, PORT, healthy within 60s, JSON errors, 2 CPU/2 GiB, no runtime outbound traffic, arbitrary fixture reset | Accepted; see stage evidence and final report |
| S1 §§4–6 model/auth/errors | Opaque IDs, past-date creates, unknown fields, wrong-type versus invalid-value precedence, hashed passwords, simultaneous sessions, owner isolation | Accepted; see stage evidence and final report |
| S1 §7 receipts | User/method/path scope, JSON-value equality, unknown-field body differences, replay before validation, original response after edits, 50 identical concurrent writes, failed-key reuse | Accepted; see stage evidence and final report |
| S1 §8 bookings | Half-open adjacency, capacity, grid/opening, cutoff boundary, no-op/cancel repeat, sort by instant, failed amendment leaves original occupancy | Accepted; see stage evidence and final report |
| S1 §9 time | IANA arbitrary dates, spring gaps, first fold occurrence, absolute duration across transitions, closing instant | Accepted; see stage evidence and final report |
| S1 §10 state transfer | Atomic replacement, unchanged exports, repeat imports, credentials/tokens/receipts retained, corrupted state rejected without mutation, source-independent use | Accepted; see stage evidence and final report |
| S1 §11 moves | 1–8 distinct references, swaps, unchanged listed occupancy, input-order non-occupancy precedence, mixed-owner/restaurant, complete rollback | Accepted; see stage evidence and final report |
| S2 API combinations | Only declared unordered pairs, canonical order, sum capacity, both occupancy members, single compatibility, invalid sets, atomic batch pairs | Accepted; see stage evidence and final report |
| S2 browser | Required routes/hooks, signup/login/logout, labels, 375px/desktop, stale search generations, conflict refresh without form loss, uncertain exact-body/key retry, repeated success | Accepted; see stage evidence and final report |
| S2 migration | S1 export with active tokens and lost-response receipt imports while browser remains signed in and pending retry survives | Accepted; see stage evidence and final report |
| S3 explanations/history | Independent capacity/overlap rules, full order, owner-only 404 including anonymous, contiguous history, no-op/replay silence, pair transitions | Accepted; see stage evidence and final report |
| S3 policies/terms | Manager isolation, complete validation, same-date tie, out-of-order publication, past effective dates, immutable accepted terms, original receipt, old cutoff then new-policy validation | Accepted; see stage evidence and final report |
| S3 revisions | Stale revision before cutoff, bool rejection, concurrent CAS, once-per-operation counters, unchanged no-op terms | Accepted; see stage evidence and final report |
| S3 recurring | Anchor unchanged, count/interval limits, local calendar recurrence, DST rollback, generated per-date policy, permanent individual exceptions, cancellation independence | Accepted; see stage evidence and final report |
| S3 collective/migration | Batch series increments once, real-change exceptions only, S1/S2 imports with history and adoption preserving identities | Accepted; see stage evidence and final report |
| S4 closure optimization | Exhaustive independent oracle within 6 tables/4 pairs/6 bookings; changed count then unused seats then reference-order option ranks; fixed bookings and earlier closures constrain assignments | Accepted; see stage evidence and final report |
| S4 preview/apply | Read-only preview, accepted-capacity use, cutoff-independent repairs, stale restaurant revision, atomic concurrent apply, original apply receipt, unaffected restaurant independence | Accepted; see stage evidence and final report |
| S4 history/series | Reassigned history has plan ID and table_ids, accepted terms/time unchanged, exceptions/scheduled dates retained, each affected series increments once | Accepted; see stage evidence and final report |
| S4 recurring amendments | Required CAS, original scheduled dates, skip cancelled/exceptions, index error precedence, all-or-nothing occupancy, no-op/empty eligible success, concurrent change at most once | Accepted; see stage evidence and final report |
| S4 migration | Imports from all predecessors preserve old booking/series receipts, cancelled/moved occurrences and opaque identities | Accepted; see stage evidence and final report |

Each accepted stage folder must contain its own Dockerfile, RUN.md, source, tests and offline assets. No symlinks, submodules or nested Git directories are allowed. Final verification runs all folders from the result repository and a clean clone, then runs offline `harness check`. The authentic room export is supplied after the autonomous run and remains an explicitly pending gate until present.

## Accepted revision chain

Stage 1 accepted: implementation `8a2a07abfe972815cfea7c02176a075b8b2accaf`, package tree `2a5107fedec409dd152484de88ede68b861e008b`, complete folder/evidence revision `3813508b5624b4ae89a346b68611a595f83cfde5`. Official host and isolated suites both 120/120; expected stage-2 rejection is the absent search UI. Independent HTTP and network-none checks each 23/23; implementation tests independently rerun 24/24. Fresh-process transfer, 22 malformed-import variants and disabled test controls passed. See [exact commands and durations](../evidence/stage-1/verification.md). Stage-1 matrix rows above are satisfied by that report; later-stage rows remain pending. Hidden judging checks are unavailable.

## Evidence convention

Stage 3 accepted after repair: implementation `8a12344510a97d7ee20a4326935cacc3ab00798e`, complete evidence/folder revision `0e302c79de3521fc0993cb6ed0b6f21a52d493e4`. Host and isolated 152/152; independent 47 HTTP plus three deeper cases, genuine stage-1/2 migrations, seven inherited browser and three product scenarios, and author tests independently rerun 62/62. The first candidate incorrectly accepted an imported exception flag erased after a real diner amendment; independent rejection and author fix are preserved. See [stage-3 verification](../evidence/stage-3/verification.md). Stage-3 matrix rows are satisfied by that report; stage 4 remains pending.

Stage 2 accepted: implementation `e4fc1c5bf52769927b50e139be1d380b1c044aeb`, complete evidence/folder revision `f2e3189db5f113f9b38509cc57241d9e50d91330`. Official host and isolated inherited/current suites 120/120 + 25/25; independent HTTP 30/30 plus 2/2 source-review cases, seven browser scenarios including actual stage-1 pending-retry upgrade, author tests independently rerun 41/41. Expected stage-3 overshoot rejection. See [stage-2 commands, durations and limitations](../evidence/stage-2/verification.md). Stage-2 matrix rows are satisfied by that report; stage-3/4 remain pending.

Record exact command, UTC start/end or elapsed duration, exit status, full Git revision, counts and limitations. Preserve failed attempts. Use a new harness output directory each time and keep exports carrying tokens outside this repository. Expected overshoot failures are identified separately from contract regressions.

## Final Stage4 and complete-chain acceptance

Stage4 accepted service `53617a341d21ebae3d76761f41b6ea4d38bc2a6c`, independent evidence `aa816477c6a2a40b528a28c362a7ec67bfc566a1`. Independent69/69 HTTP both host/network-none, genuine predecessor migrations and browser checks pass. Coordinator host158/158; all-stage isolated and clean-clone isolated each575 required checks pass with correct overshoot rejection. See [final exact commands, durations and limitations](../evidence/final/verification.md). All matrix rows are accepted based on the corresponding stage reports, with finite-test/source-review limits retained. Earlier pending prose records the historical sequence and is superseded by this final decision. Authentic operator room export remains the only observed offline submission-check failure.
