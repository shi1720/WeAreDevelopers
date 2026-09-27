# Companion release coverage

Accepted bounded local/emulator pilot. Independently checked runtime: `d6194c8c9575f0a6b85ec2a322e8a65cbb9af740`. Accepted code/test revision: `8f749427004a35e6ac25ed34abb7997515ec4354`; its sole product difference is the independently executed corrected multiprocess driver.

See [independent clause evidence](verification/coverage.md), [exact runs](verification/runs/), [preserved findings](verification/findings.md) and [factory report](report.md). Original graded results are provenance, not companion results.

| Requirement | Release evidence and scope |
|---|---|
| Unchanged baseline copy | Commit 1448eea; matching source/product tree 53912d0263085f441225f962351d8876fef68ca1 |
| Durable atomic state and receipts | Both adapters; restart, pre/post-commit termination, persistence failures, exact receipt replay |
| Firestore concurrency | Two live processes, competing and same-key bookings, callback retries and unknown-outcome recovery |
| Bounded chunks and corruption | Schema/checksum/capacity failures, encoded request margins; no truncation |
| SQLite ownership | Second writer refused; partial/corrupt schema fails closed; durable commit before acknowledgement |
| Atomic provisioning | Wrong secret, concurrent setup, restart, malformed metadata and real browser setup |
| Private setup-secret delivery | Supplemental non-root offline container with host-owned 0600 file: readiness 200 and setup 201 |
| Production and demo isolation | Test routes/seeded credentials absent by default; two visitors, copied identifiers, role/reset isolation, expiry and cleanup |
| Sessions and request boundary | Exact __session cookie, JSON CSRF, origin, expiry/logout/password revocation, forwarded-header spoofing and no-store |
| Bounded abuse | Body/header/auth pressure and eight trickling clients; legitimate booking progress; no distributed denial-of-service claim |
| Backup and restore | Both adapters during writes; separate target restore, invalid restore preservation, maintenance/CAS and incident session revocation |
| Health and shutdown | Readiness distinguishes unusable storage; process and container failure/restart checks |
| Booking list/edit and roster | Owner scope, pagination/date bounds, changed terms/CAS/exact retries, real desktop/mobile flows |
| Browser uncertain outcomes | Lost committed booking/edit/series/closure responses, reload plus restart, original body/key/receipt, account isolation |
| Domain invariants | Selected independent contracts, concurrency, planner oracle, 18 inherited pure tests plus 14 subtests; not every original HTTP permutation ported |
| Visual and keyboard use | Five Chromium scenarios at 1440/375, screenshots and no overflow; source/visual review, not exhaustive accessibility certification |
| Self-hosted operations | Clean-clone image, empty volume, Python 3.12, network-none SQLite at 2 CPU/2 GiB, restart and separate restore |
| Hosted packaging | Firebase routes/cookie forwarding configuration, deny-all browser Firestore rules, exemptions, ADC and parameterized deployment reviewed; actual deployment remains operator gate |
| Provenance and reporting | Original paths frozen; author commits and failures retained; exact revisions/durations; room token usage and provider spend unavailable |

The broad final operational run recorded 87 passes and one unknown-outcome driver assertion failure. The corrected scoped run passed two cases and strengthened receipt assertions. Together these cover 88 operational cases; no single 88-pass execution is claimed. Final UI/pure-domain run recorded 23 passes and 14 subtests.

Original judge reset/import/export controls, seeded initialization, bearer credentials and ephemeral state assumptions intentionally no longer apply. Companion setup is durable and one-time; browser authentication uses __session plus JSON CSRF. Domain assertions were not relaxed for these transport changes. The official original HTTP harness was not rerun.

External gates: operator cloud provisioning, IAM, real Hosting/TLS/cookie forwarding, deployed Firestore contention and recovery, budgets/monitoring/off-host backup, publication and room export. Residual coverage excludes exhaustive old swap/error/no-op/series permutations, sustained distributed abuse, all browsers and exhaustive accessibility. Emulator orphan-lock recovery latency is disclosed in the report. Acceptance is a bounded pilot, not an SLA or security certification.
