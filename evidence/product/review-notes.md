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

## First committed candidate review

Candidate: `70cf83c8de4c67babab92973264913c2ccc7b984`. Protected-path diff against pre-task `5ce35b4fcc332db2776a7e17c7713592b1738729` was empty when excluding only product/, evidence/product/ and allowed factory/companion/run.json.

Independent immutable-checkout evidence reports eight HTTP checks passing and storage 39 passing with two failures: malformed maintenance metadata accepted, and the multi-process Firestore counter test exhausted five transaction attempts. Both logs are preserved in verification/runs and were returned to Engineer. A built image is not yet a passed runtime gate.

Coordinator viewed synthetic screenshots for desktop setup and updated recurring visits, and mobile roster and closure preview. The cream/forest/terracotta identity remains clear, forms have visible labels, and the reviewed images show no horizontal clipping. Screenshot inspection does not establish keyboard behavior or independent browser acceptance. The author browser run on this candidate retained a test-driver failure waiting for an HTML option to be visible; correction must preserve booking behavior assertions and original failure output.

Further source findings sent to authors: demo reset reused the account recovery scope; anonymous sessions can exhaust the namespace cap; inline style attributes conflict with the restrictive CSP. Live SQLite backup now has a read-only reader path in the candidate, subject to independent execution.

## Additional confirmed provisioning validation defect

At observed HEAD `bc2b0f235d91d129b3409672b7a4b109e413ece6`, Python 3.12 accepted a durable envelope containing the complete synthetic venue/users/bookings but `setup_consumed=false`. Reproduction body: `v=fresh(); v['domain']=from_fixture(fixture()); encode(v)`, importing storage, state and demo from product with `PYTHONPATH=product`. Exit 0, encoded 7088 bytes, Python-measured 0.08713074999832315 seconds including synthetic fixture creation and revision lookup. This is a failed review expectation: such inconsistent provisioning metadata could permit setup to replace existing bookings. Reported to Engineer and Verifier for schema repair and independent negative-restore regression.

Repair commits `ee21b65f7f6bd70b2a23120862fa86e6fe116b49` and `80429d6e2a127722f5091b604c075f5ad2ae5f8e` reject both unconsumed setup with configured data and consumed setup without a venue/manager, plus inconsistent demo expiration metadata. Final independent regression remains the acceptance authority.

## Confirmed request-boundary defects and scoped rechecks

Independent lost-response browser forwarding exposed lowercase idempotency headers becoming missing after conversion to a case-sensitive dictionary. The proxy trickle test also kept four uploads open beyond 24 seconds because request buffering delayed the backend deadline. Repair `eb9e521f13bbcf4fd7fcbea9e34bb1f553a03061` explicitly preserves the consumed idempotency header and streams ingress bodies to the bounded backend. Verifier's scoped candidate `48c45d0b63bc7c4e6aba582b381e7be5262ca3ff` passed 11 selected metadata/header checks and one booking reload/restart recovery check. The rebuilt proxy test closed all four tricklers by its 24.034-second observation while a healthy booking completed in 0.015 seconds. Exact commands, full revisions and durations remain in verification/runs; this is not a substitute for final combined acceptance.

## Usage observation

At the initial observation, `band usage rooms --since 2026-09-27 --until 2026-09-27 --json` returned other rooms and unattributed usage, but no entry for this fresh companion room. Those totals cannot be attributed to this task. Provider billed cost is unavailable; no zero-cost claim is warranted.
