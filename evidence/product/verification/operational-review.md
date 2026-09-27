# Operational review additions

These are unexecuted acceptance cases until a committed candidate is available.

| Matrix link | Additional independent case |
|---|---|
| S05/B02 | Mutate durable operational envelope while leaving domain valid, and mutate domain receipts/history while envelope remains valid. Both startup and restore must reject malformed state without resetting or changing prior store. Validation must cover both layers. |
| S04/A01 | Force callback rerun and final commit failure during signup/login/setup. No cookie, usable session, token or process-memory identity may escape before successful durable commit. After a retry, returned cookie must match the committed session only. |
| A02/S06 | Read authenticated data just before inactivity expiry on process A, then read on process B/restart. If reads refresh expiry, the touch must be durable. Inject failure on touch: no successful read may imply a refresh that did not commit. Readiness must reflect inability to access the required store. Test exact expiry boundary without revival. |
| A05 | Split invalid logins across two live processes sharing one namespace. A process-local counter must not double the permitted budget. Test many absent accounts, repeated real synthetic account and spoofed forwarding; limiter state remains bounded and legitimate booking via another valid session remains usable. |
| A05/O01 | Against the real container proxy, trickle headers and request-body bytes just inside configured idle timeouts. Measure total connection lifetime rather than treating an idle timeout as a total deadline. Open a bounded concurrent group and verify a healthy authenticated booking still commits promptly. Record infrastructure/resource failures separately. |
| A04/O01 | Trigger proxy-generated oversized-header/body and upstream-unavailable errors; verify private,no-store plus required security headers on proxy-generated 4xx/5xx, not only backend responses. Build and start the actual non-root nginx image and verify writable runtime paths and PORT behavior. |

## Primary documentation reviewed 2026-09-27

- [Firebase Hosting with Cloud Run](https://firebase.google.com/docs/hosting/cloud-run): billing account is required even where free quotas apply. Deployment remains operator-owned. Review actual route rewrites and public backend authentication independently.
- [Firebase cache behavior](https://firebase.google.com/docs/hosting/manage-cache): Hosting forwards the specially named `__session` cookie and normally removes others. Acceptance checks one session cookie and JSON/header CSRF, and requires private, no-store responses without relying on cache variation alone.
- [Firestore transactions](https://firebase.google.com/docs/firestore/manage-data/transactions): reads precede writes; transaction callbacks can rerun; successful writes commit together. Test private candidates with no callback side effects or premature HTTP/session publication.
- [Firestore contention](https://firebase.google.com/docs/firestore/transaction-data-contention): library retries are finite and contention may ultimately fail. Server concurrency mode affects locking behavior. Test two live processes, retry exhaustion, and honest unknown-outcome recovery rather than assuming every contention attempt succeeds.
- [Firestore quotas](https://firebase.google.com/docs/firestore/quotas): API request limit is 10 MiB; field values have a sub-1-MiB limit. Validate encoded request/document margins around bounded chunks, including metadata and deletes, rather than equating JSON state length with wire size. The dispatch's conservative 4 MiB state and 512 KiB chunk limits remain binding.

The emulator can demonstrate local behavior but does not establish deployed quota, IAM, billing, latency or Hosting behavior. Those remain disclosed operator deployment gates.
