# Independent companion verification

Recommendation: accept the bounded local/emulator pilot at source revision `d6194c8c9575f0a6b85ec2a322e8a65cbb9af740`, with the disclosed coverage limits below. No known material defect remains from this review. This is not deployed acceptance, security certification, an SLA, or a rerun of the completed graded submission.

The final source was tested from fresh local clone `/Users/shivamgupta/.cache/proofline-pilot-verifier/final-d6194c8`, detached and clean. Corrected multiprocess test driver: `6e74d8e42294dd85ea724729c7e68b322593ca1f`. Other final drivers are in the source revision. That later commit changes only the verifier test; implementation equality was checked. All commands, full revisions, exit statuses, UTC starts and measured durations are preserved in `runs/*.json`, with complete output in matching `.log` files. Failed checks were not deleted or rewritten.

## Final executed gates

| Gate | Observed result | Runner duration | Evidence label |
|---|---|---:|---|
| SQLite/Firestore storage, HTTP, domain, security, two-process and crash cases | 87 passed, one driver assertion failed; corrected scoped run below completes coverage of all88 cases |105.230903s|final-operational-d6194c8|
| Corrected two-process unknown-outcome and shared-auth-pressure checks |2 passed; exact receipts through both processes, one booking effect per key, one competitor winner|18.875995s|multiprocess-unknown-recovery-d6194c8|
| Real Chromium flows plus inherited availability/temporal tests |23 passed: five browser scenarios and18 pure tests;14 additional subtests|11.321539s|final-ui-domain-d6194c8|
| Exact clean-clone image build |exit0, cached build with network disabled|3.074906s|final-build-d6194c8|
| Real container with empty volumes |setup, booking, policy, series adoption/amendment and closure apply survive restart; consistent online backup and separate-volume restore retain identities/history/original receipts|2.410410s|final-container-d6194c8|
| Eight simultaneous trickling header/body clients on repaired proxy |all closed within24s; healthy booking about14ms; exit0|24.860701s|proxy-header-body-48c45d0|
| Actual nginx upstream timeout |504 carries private,no-store and security headers; exit0|20.774200s|proxy-generated-504-48c45d0|

Proxy/handler configuration is unchanged between the repaired48c45d0 source and final source; those passing targeted abuse checks were not blindly repeated. Final container independently checks proxy oversized body/header errors and non-root startup.

Final image: `sha256:ad581e03b6a305dd34f6f08149f6fc5e7fe6cf768f7d45108bcbd951ee754c79`. Runtime inspection: network `none`, CPU quota2000000000 nanocpus, memory2147483648 bytes, user65534:65534. Python3.12.14 was used. Firestore tests use the local emulator and shipping pinned SDK2.21.0, with unique verifier collections and at least two live service processes. Hosted Firestore necessarily requires Google API network access; no cloud resources or credentials were used.

Crash tests terminate before commit and after commit/before response on both adapters, restart and recover the original request. Injected commit failure preserves prior state. The emulator can retain an abandoned transaction lock for about60 seconds: bounded requests may return503 meanwhile. Recovery kept the same body/key and eventually recovered exactly one receipt without resetting data. This observation does not establish deployed latency.

## Review and repairs

Independent review reproduced case-sensitive HTTP header handling, weak operational-envelope validation, missing total proxy body deadlines, unsupported/missing storage metadata acceptance, and malformed setup owner500 errors. Engineer repairs were independently rechecked. Findings, original failures, test-driver corrections and source dispositions are in `findings.md`.

The final full-run failure was an incorrect test expectation after an uncertain committed503: both callers can legitimately recover HTTP200. The corrected driver allows that only after observed503, verifies equal original receipts and revision1, replays through both live processes, and checks exactly two bookings for the two distinct test slots. The corrected run observed same-key initial503/503 then200/201; competing keys503/503 then201/409. It did not weaken the one-effect or exact-receipt assertions.

Real browser scenarios cover setup, guest list/edit with proposed terms, manager roster, closure preview/apply, current series summary, and deliberately dropped committed booking/PATCH/series/closure responses followed by page reload and service restart. Booking recovery includes logout, another account and return to the original account. Synthetic1440px/375px screenshots are under `screenshots/final-d6194c8/`. Automated overflow checks pass. Visual inspection of setup, edit terms, roster, closure preview and updated series found legible hierarchy and controls without clipping. Browser series refresh uses an eight-second bounded wait, not a premature instantaneous assertion.

First copy `1448eea24239a59e03941fc3a1a691b86bad19d9:product` and baseline `330f1c8321670ca7d34b6b7127c0fb73df84ca25:stage-4` both have Git tree `53912d0263085f441225f962351d8876fef68ca1`. Protected original paths have no diff. Reservation/policy/series/replan domain modules remain unchanged; planner change is its actionable limit message. Independent HTTP domain cases add DST, declared pairs, concurrency, immutable terms, permanent exceptions, collective rollback, CAS/cutoff, six/seven-overlap bounds and three exhaustive planner-oracle comparisons.

## Limits and operator handoff

`coverage.md` maps every dispatch area to executed evidence or source review. The original official HTTP harness was not rerun against the companion: unauthenticated reset/import/export, fixture initialization and immortal bearer tokens intentionally no longer apply. Pure availability/temporal tests were actually rerun; other original domain error-order, swap, series-bound and no-op permutations were not exhaustively ported. Sustained distributed denial-of-service, every session/demo capacity permutation, exhaustive accessibility and cross-browser certification were not tested. Configured numerical bounds and applicable source were reviewed. These are disclosed limits, not manufactured passes.

Firebase rewrites, special `__session` handling, deny-all Firestore browser rules, chunk index exemptions, workload ADC and parameterized deployment script were reviewed. Actual Hosting cookie forwarding, deployed Firestore/IAM/contention, TLS and billing must be checked after operator provisioning. The preferred site name's availability is unverified. No deployment, publication, push, merge or room export was performed.

For the local synthetic demo, follow `product/docs/demo.md`: use Python3.12 from `product/`, an empty private SQLite path, explicit development mode and origin, and `TABLEKEEPER_PUBLIC_DEMO=1`; open `/demo`. The setup/start and private-secret procedure, image/volume commands, online backup and maintenance/CAS restore commands are in `product/docs/operations.md`. Those start/backup/restore paths were exercised from clean clones and empty volumes. Operator work remains project/billing/Firestore/service identity/secret provisioning, authenticated deployment, real hosted acceptance, off-host backups, room export and publication.

The44 preserved run records span2026-09-27T18:21:35.797195Z to2026-09-27T19:15:16.835880Z, measured elapsed3221.038685 seconds including gaps. This excludes earlier planning and later reporting. `run-index.json` records that window and supplements early missing driver fields only where a clean checkout and repository-relative command establish the source revision; original records remain intact.

Shivam Gupta is product and factory lead. Proofline Pilot Engineer and Experience authored implementation; Proofline Pilot Verifier authored these independent cases, executed checks and reviewed evidence. Provider token usage and actual monetary cost are unavailable to this seat. Run durations are measured and may overlap; they are not a provider bill or an additive elapsed-time claim.
