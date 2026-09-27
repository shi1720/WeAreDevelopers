# Stage 4 implementation coverage

Agent-generated backend by Proofline Engineer; independent acceptance remains with the verifier and coordinator.

| Requirement | Implementation | Author evidence |
|---|---|---|
| Bounded global optimum, three objective tiers | planner.py exhaustive search with lexicographic objective and safe nonnegative-cost pruning | objective tiers, fixed full-interval overlap, 6/4/6 limits |
| Own accepted capacities and unchanged promises | Candidate capacities taken from each reservation's accepted_terms; apply edits table selection only | terms/time equality, repair past cutoff |
| Preview purity, replay and stale precedence | replans.py stores immutable context; existing transactional receipts; applied check precedes stale check | preview snapshots, original replay after later edits, stale and impossible rollback |
| Atomic apply and series counters | One store transaction publishes closure and assignments; each affected series touched once | 50 simultaneous apply retries, history and counter assertions |
| Closure occupancy | reservations.check_occupancy and availability closures keyword use half-open UTC intervals | blocked creation and closure-aware availability tests |
| Recurring amendment CAS and rollback | series.amend validates revision first, original dates, eligible indices, old cutoff, then all occupancy | competing CAS, skipped exceptions/cancelled, no-op/empty success, full rollback |
| Provenance without rewriting history | Private series_operations snapshots cross-check receipts and actual historical revisions; ordinary changed events retained | collective/individual exception round trip and provenance corruption rejection |
| Portable plans and closures | portability.py checks optimizer result, historical identities, closure/apply links, original receipts and reassigned history | applied/unapplied round trips and corrupted plan rejection |
| Deployment | Existing non-root Python3.12 image, local assets, no runtime downloads | independent host/isolated gates required before acceptance |

Manager-only `GET /api/restaurants/{id}/replans/{plan_id}` returns preview fields at top level plus `before_reservations`, with public snapshots omitting user_id. Owners retain private lookup/history permissions.

Run author checks from this folder with the prepared interpreter:
`/tmp/proofline-official-spec/.venv/bin/python -m unittest discover -s tests -p 'test_*.py'`.

Initial environment probes failed: macOS system Python3.9 lacks hashlib.scrypt; Homebrew Python3.14 lacks Playwright and differs in datetime parsing. Prepared-interpreter run passed 73 tests in 12.292s before two additional backend boundary tests. These probes did not alter earlier stages or official harness files. Final measured checks are reported with the committed handoff.

Subsequent evolving-tree discovery ran 78 tests in 27.681s, exit 1: newly added browser tests `test_closure_apply_lost_response_and_mobile` and `test_closure_stale_refresh_and_impossible` timed out waiting for `replan-preview`; other 76 passed. Failures were handed to the Experience owner. This is not an acceptance claim.
