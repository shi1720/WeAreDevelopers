# Companion acceptance matrix

Status is pending until supported by independent committed-revision evidence. Original graded results are provenance, not companion results.

| Requirement | Author | Independent gate | Status |
|---|---|---|---|
| Unchanged full baseline copy | Engineer | Source/product Git tree equality | Verified: 1448eea24239a59e03941fc3a1a691b86bad19d9; tree 53912d0263085f441225f962351d8876fef68ca1 |
| Durable candidate transactions and exact receipts | Engineer | SQLite restart/crash/failure; Firestore multi-process conflicts/callback retry | Pending |
| Bounded validated Firestore chunks and request margins | Engineer | Hash/schema corruption; 4 MiB capacity; encoded commit bounds | Pending |
| Single-writer SQLite ownership | Engineer | Competing process refuses; durable commit precedes response | Pending |
| Atomic secret-authorized one-time setup | Engineer + Experience | Wrong secret, concurrent setup, restart and browser setup | Pending |
| Production defaults and isolated public demo | Engineer + Experience | No synthetic login/test routes; two visitors and copied identifiers; expiry/reset/cleanup | Pending |
| Durable bounded cookie sessions and CSRF | Engineer + Experience | Expiry/logout/password change, origins, forwarded spoofing, no-store and __session | Pending |
| Resource limits and abuse resilience | Engineer | Body/header/slow/login abuse with legitimate booking progress | Pending |
| Consistent private backup and safe restore | Engineer | Both adapters during writes; separate restore; invalid restore; maintenance revision lock; revoke sessions | Pending |
| Liveness/readiness and private-safe shutdown/errors | Engineer | Failure readiness and graceful stop checks | Pending |
| Booking list/edit and manager venue roster | Engineer + Experience | Ownership/pagination/date bounds; changed terms/CAS/retries; browser flows | Pending |
| Persistent uncertain-request recovery | Experience + Engineer | Lost committed response, reload and restart; exact body/key; user switch isolation | Pending |
| Preserved domain invariants | Engineer | Concurrency, UTC/DST, pairs, accepted terms/history, permanent exceptions, atomic series/CAS, optimal bounded closures | Pending |
| Preserved polished accessible UI | Experience | 1440/375 screenshots, keyboard/focus and no overflow; no new em dashes | Pending |
| Reproducible self-hosted operations | Engineer | Fresh clone/empty volume documented commands; clean Python 3.12 container offline at 2 CPU/2 GiB | Pending |
| Hosted packaging | Engineer | Firebase route rewrites, deny browser DB access, exemptions, ADC and parameterized deployment review | Pending; deployed acceptance remains operator gate |
| Provenance and honest final report | Coordinator | Frozen original paths; full revisions, failed checks, durations, limitations and available usage | Pending |

Original harness transport changes must be enumerated explicitly: judge reset/import/export controls and seeded fixtures are unavailable by default; browser bearer credentials are replaced by __session plus JSON CSRF; setup is durable and one-time. Any adapted domain check must retain its domain assertions and record the adaptation.
