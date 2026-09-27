# Engineer requirement coverage

This matrix records implementation and author evidence, not independent acceptance. Baseline copy commit: `1448eea24239a59e03941fc3a1a691b86bad19d9`; initial backend: `70cf83c8de4c67babab92973264913c2ccc7b984`; repair: `145536827499efcf1342b0936e8311d00bc0c33b`. Author run `20260927T184422174514Z` observed shared HEAD `91a1cfc90fde69c11ef0ba7b577c5b923c7ba625`, with only other seats' working changes; it passed 34 tests and 14 subtests in 4.82s, 5.080165207997197s measured wall time. Exact command/status/diff context are in its JSON. Independent immutable-candidate results and final gates belong to Verifier and Coordinator.

| Requirement | Implementation | Author evidence / limit |
| --- | --- | --- |
| Unchanged first copy, original preservation | baseline.json and copy commit | Git tree hashes equal `53912d0263085f441225f962351d8876fef68ca1`; only scoped paths committed |
| Python 3.12 and offline SQLite | standard library core, Docker Python3.12 | Prepared3.12.14; network-none2CPU/2GiB readiness/session smoke; complete container gate independent |
| One venue, 1-6 tables, <=4 pairs | setup validation and envelope validation | Initial-policy bounds reused; setup author and HTTP checks |
| All original domain invariants | inherited candidate modules and validation | Author temporal/availability plus policies/series/closure restart; exhaustive inherited independent gate remains Verifier-owned |
| Durable private candidates | storage.transact | Rollback, failure injection, restart and exact receipts |
| SQLite single writer, commit-before-response | ownership flock, WAL/FULL, transaction | Second owner refusal, concurrent booking and crash hooks |
| Firestore multiprocess safety | transactional root/revision/chunks, SDK5 attempts | Two live booking processes, bounded contention recovery rehearsal |
| Callback retry purity | callback-local token and domain, commit result only | Forced server-released abort reruns callback twice, durable counter once |
| 512KiB chunks, 4MiB cap, encoded margins | encode/decode and protobuf request measurement | Exactly4MiB/eight chunks accepted; +1byte rejected atomically; checksum corruption refused |
| Corrupt/unsupported state fail closed | schema/hash/domain/metadata validation | Corruption and malformed maintenance checks; no automatic reset |
| Durable users, sessions, history, exceptions and receipts | companion envelope wraps validated domain | Restart policy/series/closure and old receipt replay |
| Cloud authority and ADC | Firestore adapter, K_SERVICE SQLite refusal | No cloud credentials/resources used; real deployed gate remains operator work |
| One-time protected setup | secret comparison and atomic owner/venue/consumption | Two concurrent setup requests yield201/409; second setup after restart rejected |
| Explicit production origin/TLS | startup validation; Secure cookie | HTTP rehearsal plus source review; deployed TLS gate remains operator work |
| No default synthetic/test access | fresh main state, unconditional test-route404 | HTTP acceptance rehearsal |
| Random isolated demo, bound role/reset | cookie namespace+secret and per-namespace storage | Two visitors, swapped locator rejection, isolated role/reset |
| Demo expiry/cap/cleanup | 2h,100 namespaces,10 creates/min, bounded CLI | Expiry synchronous; cleanup implementation reviewed; independent cleanup gate pending |
| Durable bounded sessions and revocation | digests,12h max/2h idle,8/user,1024 total | Logout/password old-cookie rejection, restart; independent time-boundary tests pending |
| Anonymous capacity protection | max128 anonymous,60 creations/min | Authenticated booking succeeds during anonymous abuse |
| Browser cookie and CSRF | __session HttpOnly/SameSite, JSON token/header+Origin | HTTP rehearsal and cross-origin rejection; browser storage owned by Experience |
| Private no-store and security headers | Handler plus nginx always header | Host/container smoke; full error/proxy checks independently executed |
| Auth abuse and enumeration resistance | durable bounded counters and dummy scrypt | Failed login and password quotas; login result does not reveal account existence |
| Body/header/deadline/resource bounds | nginx plus independent backend limits | Container build/smoke; slow/oversized/proxy gate independently executed |
| Owner password assistance without invented email | private CLI file, hash+revocation | Source implementation and operations guide; no email/provider integration |
| Consistent backup both adapters | atomic snapshots,0600/O_EXCL/fsync | SQLite read-only reader during writes; Firestore backup during writes |
| Validated restore and maintenance/CAS | read_backup then guarded replacement | Invalid snapshot preserves state; stale revision rejected; separate SQLite target |
| Incident restore revocation | --revoke-sessions, absolute expiry | Sessions removed while original receipt and identities retained |
| Recovery limits/off-host schedule | operations.md | Nightly/off-host guidance; no claim of deployed scheduler or zero-loss backup |
| Health/graceful shutdown/private errors | live vs validated ready, supervisor signals | Container smoke; independent kill/restart/receipt gates required |
| Owner booking pagination and edit | view/offset, keyed PATCH+CAS | HTTP suite rehearsal; owner filtering and revision history |
| Manager narrow date roster | manager guard, bounded operational fields | HTTP rehearsal; no account email/private history in roster |
| Edit availability and terms | owner-validated exclude_reference; policy0 | Supports Experience preview; server still revalidates atomic save |
| Closure bound and recovery message | unchanged planner plus clear limit message | All overlaps counted, no split workaround; independent oracle gate required |
| Pending browser restart recovery | account_scope includes namespace/user/reset generation | Backend durable exact receipts; UI/reload tests owned by Experience/Verifier |
| Firebase rewrites/rules/indexes/deploy | all routes to backend; deny-all; unindexed bytes | Source review and build; no resources provisioned or deployment claimed |
| Small economical runtime | min0/max2/concurrency16, no polling requirement | Deployment config only; billing/cost/real-world load unknown |

The source is an agent-generated implementation. No author assertion here grants acceptance. Original failed checks remain in early-checks.md and independently owned logs; repairs preserve original commits. No root packaging, GitHub publication, room export, cloud deployment, real guest data, real secrets, payments, SMS, external model calls, Kubernetes or enterprise certification is included.
