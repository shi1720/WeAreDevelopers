# Stage 4 independent coverage

Status: preparation in progress; no stage-4 acceptance claim. Governing source is official commit `803560d2a678ace1414465c098eb0ab5380ffade`, all four specifications. Baseline copy `8c26116e8aba226c5a8f5e7d58014823b4cc17a2` preserves accepted stage 3. Prior folders remain frozen.

| Contract | Independent checks | Gate status |
|---|---|---|
| All inherited API/browser/policy/series contracts | Copied independent suites, rerun against frozen candidate | Pending |
| Global seating optimum: changed sets, unused accepted seats, reference-ordered rank vector | Separate exhaustive Cartesian-product oracle; deterministic six-table/four-pair/six-booking generated cases | Authored, not run |
| Full interval conflicts including fixed bookings and closures | Oracle checks complete booking spans; generated staggered bookings; half-open closure edge checks | Authored; prior-closure expansion pending |
| Preview purity, no-feasible rollback, failed-key reuse | History/current-record comparisons, private snapshot equality | Authored, not run |
| Apply atomicity, original receipts, moved-only revision/history, preserved terms | Plan/apply assertions and roundtrip; fifty identical concurrent applies | Authored; concurrent-reader expansion pending |
| Stale plans, no-op silence, already-applied distinct key | Dedicated transition tests | Authored; unrelated-restaurant expansion pending |
| Collective amendments retain identity and scheduled dates; do not mark exceptions | Full occurrence comparisons, private native roundtrip | Authored, not run |
| Skip cancelled and permanent exceptions, empty/no-op success | Mixed series transitions and revision assertions | Authored, not run |
| Amendment validation, permissions, CAS, atomic conflict rollback | Invalid types/bounds, fifty unique-key contenders, reusable failed key | Authored; DST/cutoff/error-order expansion pending |
| Accepted-policy capacity and repair cutoff exemption | Dedicated historical-policy/past-booking scenarios | Pending |
| Genuine predecessor exports and native relation corruption | Actual stages 1–3 services plus plan/closure/series/history/receipt corruption cases | Pending |
| Manager closure and recurring amendment UX, exact uncertain retries | Independent Chromium desktop/375px scenarios and visual inspection | Pending |
| Offline/resource limits, official inherited suites | Host and isolated official harness on frozen revision, runtime inspection | Pending |

Tests hold exports and bearer tokens in memory; assertion diagnostics do not print them. Author test claims are not independent evidence. Final evidence will record exact commands, revisions, exit statuses, durations and limitations; unexecuted tests remain explicitly pending.
