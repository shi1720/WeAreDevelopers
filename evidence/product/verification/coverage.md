# Independent companion acceptance matrix

Verifier: Proofline Pilot Verifier. Product direction and factory configuration: Shivam Gupta.

Derived before companion source review from room dispatch and official contracts at `803560d2a678ace1414465c098eb0ab5380ffade`, `tablekeeper/spec/stage-{1,2,3,4}.md`. Baseline source: `330f1c8321670ca7d34b6b7127c0fb73df84ca25`. Every row starts **pending**; a case design is not a passed check. Acceptance requires an immutable committed candidate and independent execution.

| ID | Requirement and adversarial acceptance cases | Status |
|---|---|---|
| P01 | First product commit tree exactly equals baseline stage-4 tree; original protected paths unchanged; explicit author provenance | pending |
| S01 | SQLite volume restart preserves users/password hashes, session revocations, venue, bookings, identities, accepted terms, histories, series/exceptions, policies, closures/plans and exact receipts | pending |
| S02 | Independent process refuses already-owned SQLite store; durable commit precedes publication; injected persistence failure rolls back or enters safe unready state | pending |
| S03 | Process termination before commit yields no mutation; after commit before response yields exact replay after restart with no duplicate; distinguish unknown outcome from rejection | pending |
| S04 | Firestore two live processes contend on same namespace: one overlapping booking, concurrent identical retries yield one original success and exact replays; callbacks retry without publication | pending |
| S05 | Chunk schema/hash/count/size corruption fails closed; unsupported state never seeds/reset; <=512 KiB chunks, <=4 MiB state, real encoded request margin; capacity rejection preserves all history and receipts | pending |
| S06 | Process-alive versus usable-store readiness; graceful shutdown; bounded transaction retries; safe errors and logs | pending |
| I01 | Empty production has no synthetic account and no accessible test routes; absent/bad setup secret denied; valid setup atomically creates owner+venue and consumes setup; two simultaneous requests create only one owner | pending |
| I02 | Setup persists across restart; venue timezone/hours/grid/duration/cutoff, 1..6 tables, <=4 declared pairs validate types/bounds/duplicates; inventory/timezone fixed afterward | pending |
| I03 | Production requires explicit HTTPS public origin/TLS; setup secret never URL/log/browser storage; protected env/file; demo and development require explicit selection | pending |
| D01 | Two incognito visitors receive cryptographic isolated demo namespaces; copied references/history/roster/plans, body/query/path namespace spoof, role and reset cannot cross visitors | pending |
| D02 | Demo synthetic label/no real data; bounded creation/state/session lifetime, synchronous expiry and bounded cleanup; corruption/missing production state cannot enable demo | pending |
| A01 | Exactly __session browser cookie, HttpOnly, explicit SameSite and production Secure; no browser bearer credentials; CSRF in no-store JSON and request header | pending |
| A02 | Sessions bounded and durable; absolute/inactivity expiry enforced; logout revokes; password change authenticates and revokes appropriate sessions, including across processes/restart | pending |
| A03 | Cross-site setup/login/authenticated writes rejected; direct Cloud Run equivalent requests cannot bypass auth; missing/forged origin/CSRF and spoofed forwarding do not weaken controls | pending |
| A04 | Every dynamic/auth/error/session response private,no-store; no wildcard credentialed CORS; security headers support assets/forms; response and auth enumeration bounded | pending |
| A05 | Oversized body/header, incomplete/slow body, excessive connections and login abuse bounded while legitimate booking remains usable; limiter state bounded; documented proxy closes server gaps | pending |
| B01 | Both adapters: consistent backup during writes; separate-store restore preserves identities/terms/history and original receipt replay; private permissions | pending |
| B02 | Invalid backup/schema/corruption leaves prior store usable; SQLite restore ownership refusal; Firestore explicit maintenance lock and transactional revision protect concurrent changes | pending |
| B03 | Incident restore revokes every session while preserving identities/receipts; expired sessions remain expired; ordinary restore session-resurrection risk/schedule/loss window documented | pending |
| N01 | UTC half-open adjacency, absolute duration, Berlin/New York DST gaps/folds; grid from opening, closing boundary, numeric booleans/invalid dates; failed keys reusable | pending |
| N02 | Singles and declared pairs only, reversed pair canonical/no-op, non-transitivity, sum capacity, overlap on either member; concurrent create/amend serializable | pending |
| N03 | Same parsed JSON replay before endpoint validation; key scope owner/method/path; exact original body after later edits/cancel, concurrent same-key one mutation, no failed claims | pending |
| N04 | Effective-date/version tie policies; immutable accepted terms/history; old cutoff then new terms on real change; no-op retains terms/history/revisions; stale CAS precedence | pending |
| N05 | Collective moves atomic incl swaps/conflicts, ordered non-occupancy errors, multiple affected series increment once; failed state/history/revisions/receipts unchanged | pending |
| N06 | Series adoption calendar weeks, per-date policies, gap rollback, immutable anchor, unique stable references, count2..12 and weeks1..4; individual edits permanently except, cancellation retains identity | pending |
| N07 | Series amend preserves dates/table/identity, skips exceptions/cancelled, old cutoff/new terms, no-op purity, index-order errors, all-or-nothing occupancy, CAS concurrency, exact replay | pending |
| N08 | Planner counts all overlapping confirmed bookings (six boundary/seven rejection), <=6 tables/4 pairs, own accepted capacities, fixed bookings/closures respected; independent optimality oracle and deterministic ties | pending |
| N09 | Preview purity; atomic apply preserving identities/terms; moved histories only; restaurant/affected series revision once; stale/used/cross-venue plan denial; closure future exclusion; exact replay | pending |
| U01 | Owner-only bounded upcoming/past list, pagination and stable result ordering; reference lookup/cancel retained; manager date roster minimal and authorized, no unrelated private history | pending |
| U02 | Individual time/party/table edits use availability and show proposed terms before commit; cutoff, stale CAS and competitor errors honest; no optimistic success | pending |
| U03 | Booking and material amendment/repair pending body+key stored before send, account-scoped without credentials; dropped committed response then reload+server restart replays exact receipt | pending |
| U04 | Intentional pending edit requires explicit recover/discard; logout/account switch isolates recovery; out-of-order search safe; successful series amend refreshes current summary | pending |
| U05 | Real browser 1440px/375px setup, list/edit, roster, closure preview/apply, series summary; keyboard focus/labels, no horizontal overflow; synthetic screenshots; cream/forest/terracotta retained | pending |
| O01 | Fresh clone/empty volume documented local start/backup/restore; clean self-contained image; Python3.12; actual container network-none,2CPU/2GiB local SQLite gate | pending |
| O02 | Firebase actual-route rewrites and __session forwarding assumptions; API errors no SPA fallback; browser deny-all Firestore rules/index exemptions; deploy script project/region/service identity parameters, ADC and no public secret | pending |
| O03 | Hosted Firestore network dependency separated from offline SQLite claim; min0/max2/bounded concurrency; no forbidden services; no em dash in new UI/docs/narrative; honest recovery/auth/scale/cost limitations | pending |

## Companion changes to original harness assumptions

Production forbids original unauthenticated reset/export/import controls and synthetic accounts. Cookie sessions, CSRF, origin enforcement, expiry and revocation replace original immortal bearer transport. Provisioning replaces fixture-only venue setup. Durable restart and operational backup replace ephemeral reset/import assumptions. New browser reload recovery exceeds stage-2 requirements. Hosted Firestore requires network; offline assertion applies to SQLite only. An adapted test must preserve domain assertions and explicitly identify these transport/setup changes. No original official companion pass is claimed.

## Evidence policy

Record exact command, UTC time, full source revision, test-driver revision, exit status and measured duration. Preserve failed output and corrected driver revisions. Synthetic credentials remain in private temporary fixtures; redact tokens/passwords/setup secrets/backup bodies from persisted output. Infrastructure errors are not application failures or passes. Deployed Firestore and operator publication remain external gates.
