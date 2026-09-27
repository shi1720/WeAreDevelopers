# Stage 3 independent coverage

Contracts: full stages 1–3 at official `803560d2a678ace1414465c098eb0ab5380ffade`. Copy-forward `5fe6f09be2d41500a051d3f77983941d0eb97ce8` copied accepted stage 2 unchanged; source/destination tree `3cff1d59fd5dbf0a625e5b223ce222dc87fcd0f4`. Earlier folders remain frozen.

This matrix and new HTTP tests precede new implementation review. Preparation is not an acceptance result. Inherited checks remain enabled, with stage-specific expectation changes permitted only where the newer contract changes behavior.

| Clause | Independent cases / transitions | Remaining acceptance work |
|---|---|---|
| Inherited stages 1/2 | 32 inherited HTTP cases and seven browser scenarios | Execute all against frozen candidate; inspect inherited semantics |
| Complete policy validation | Missing every field, booleans, wrong types, range endpoints, invalid dates, duplicate weekdays, exact capacity keys; failed key reusable | Run tests; deepen malformed hours/capacity during source review |
| Policy permissions | Anonymous401, diner403, unknown404; public list | Manager UI and role separation |
| Selection | Out-of-effective-date publication order, same-date newest version, before-first policy0, original detail unchanged | Additional local-date/timezone boundary |
| Immutable terms | Publication retains booking/history; real amendment adopts selected policy; no-op retains all; pair capacity selected policy | Accepted cutoff boundary with changed policy |
| Histories | Creation fields/order/nulls, only changed fields, contiguous seq/revision, ordered timestamps, cancel once, replay none | Seed/import history invariants and tampered state |
| Private history/decision | Owner current terms; anonymous, invalid token, manager404 | Confirm no leak through all read paths |
| Revision CAS | Invalid revision422; stale before cutoff/field validation;50 simultaneous real writes, one winner | Concurrent batch/individual interactions |
| Pair transitions | Canonical reversed pair no-op; pair creation and pair-to-single table_ids history | Single-to-pair and single-to-single preservation |
| Series identity | Anchor completely unchanged,12 occurrences/4-week intervals, unique refs/indexes, own histories, original receipts | Genuine stage1 and stage2 export adoption |
| Occurrence validation | Future-date policy selection, late overlap rollback, failed key reusable, DST gap rollback/fold first occurrence | Earliest failing occurrence precedence across error classes |
| Series permissions/types | Anonymous write401, other owner404, count/interval type/range, already adopted | Cancelled/cutoff anchor boundaries |
| Exceptions/cancellation | No-op none, real PATCH permanent exception even reverted, cancel retains exception flags; sibling survives anchor cancellation; replay original | Race tests and manager cannot see diner series |
| Collective moves | Two members changed: series increments once, each revision once, exceptions; stale later member rolls entire export back | Multiple affected series and restaurant once-per-operation counters |
| Export/import | Current series and batch receipts roundtrip | Both actual predecessor processes; credential replacement; relational corruption rollback |
| Browser/product | Inherited recovery/stale searches/responsive suite | New manager policy/history/series flows,375px/desktop render, local assets, labels/focus |
| Deployment/official | Immutable official host suites1–3, expected4 rejection, isolated internal network2CPU2GiB | Run only after coordinator freeze; new shared output every time |

Reviewer owns `stage-3/tests/independent_*.py`, this matrix and `evidence/stage-3/`. Source repairs belong to authors. Exports/tokens stay in memory or private outside repository. Restaurant revision has no mandatory public read endpoint in stage3: exact counter validation requires source review and exported opaque-state inspection, without demanding a future stage4 endpoint.
