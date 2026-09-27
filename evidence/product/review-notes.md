# Coordinator review record

## Baseline gate

Inspected original stage 1, 3 and 4 contracts and baseline storage, auth, server, reservation and planner modules. Baseline copy commit `1448eea24239a59e03941fc3a1a691b86bad19d9` has product tree `53912d0263085f441225f962351d8876fef68ca1`, identical to source `330f1c8321670ca7d34b6b7127c0fb73df84ca25:stage-4`. This verifies copy provenance only, not operational readiness.

## Risks raised before implementation

- Baseline validates only original POST receipt paths. New individual edit/cancellation idempotency must be durably validated without weakening old receipt/history checks.
- Firestore transaction retries must never publish a session token, response or process-memory state before commit. Durable last-seen updates also participate in transaction and expiry rules.
- Per-process throttles cannot establish deployment-wide authentication bounds. Independent tests must exercise multiple live backend processes.
- The planner counts every confirmed interval overlap. Capacity rejection must not silently split a closure or discard history/receipts.
- Browser pending-operation persistence must precede send and survive dropped committed responses, reload and server restart. Success must not be inferred from a network timeout.

## Early draft integration review

- Found and reported incompatible session routes/shapes in backend and UI drafts: `/auth/session` plus nested user versus `/api/session` plus flattened fields. Setup/demo route prefixes also differed. Requested explicit wire agreement before further route-dependent work.
- Found and reported browser pending state clearing on authentication/CSRF rejection. A committed request with a lost response must remain recoverable after session expiry and reauthentication.
- Found and reported a nonlocal token mutation inside a retryable Firestore callback. Candidate generation must remain callback-local until committed result returns.
- Requested explicit anonymous-session abuse bounds so public session creation cannot exhaust the login capacity.

These are draft findings, not claims that a committed candidate failed or that repairs have passed.

## Usage observation

At the initial observation, `band usage rooms --since 2026-09-27 --until 2026-09-27 --json` returned other rooms and unattributed usage, but no entry for this fresh companion room. Those totals cannot be attributed to this task. Provider billed cost is unavailable; no zero-cost claim is warranted.
