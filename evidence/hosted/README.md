# Hosted companion: operator deployment evidence

**The published companion passed live HTTPS API, visitor-isolation and desktop/mobile browser checks at [tablekeeper-proofline.web.app](https://tablekeeper-proofline.web.app). Durable revision continuity also passed on the preceding deployment.** This is a public synthetic demo of the separately accepted operational companion, not a production certification or an extension of the original graded run's evidence.

The [sanitized deployment summary](deployment-summary.json) records the scoped image, revisions, traffic, startup probe, resources, database/IAM/rules and cleanup observations. It excludes credentials, cookies, visitor request bodies and unrelated project resources.

## Accepted source and deployed artifact

| Item | Value |
|---|---|
| Accepted companion evidence commit | `8f749427004a35e6ac25ed34abb7997515ec4354` |
| Runtime implementation revision | `d6194c8c9575f0a6b85ec2a322e8a65cbb9af740` |
| Accepted product tree | `81f770ca92f61af4c58e5a763d9a466a671804c8` |
| Initial verified deployment image digest | `sha256:d22729b181ac9b8df69d743d52b260fbb11039d2b46affe40876b16a0fb2d0c2` |
| Published source commit | `053ae0d6260f79b924752949c37a8837ded4d480` |
| Published product tree | `3045a3091e812a4171a8decd514e3ee5edd784ab` |
| Published image digest | `sha256:4242b0226aaad2aecc432cb1999a2e49530025b3da92fc36eb3f2d21b4ea6792` |
| Service / region | `proofline-tablekeeper` / `us-central1` |
| Previous tested revision | `proofline-tablekeeper-00003-6th` |
| Latest ready revision / observed traffic | `proofline-tablekeeper-00005-dz5` / 100% |
| Public Hosting site | `tablekeeper-proofline` |

Source identities were read from Git; deployed image/revision/traffic are selected from operator-captured service metadata. The finalized Hosting release is `1790538459826000`, version `0b3ca453ade4aa32`, published at 19:47:39.826 UTC on 27 September 2026. Its pinned Run tag selects the published revision. Hosting metadata records private no-store headers and the dedicated service rewrite. The cloud build record ID is not included in the summary. The original graded folders retain their own accepted revisions and authentic room export.

## Executed live checks

| Observation | Result and evidence |
|---|---|
| Published image, direct Cloud Run backend | [PASS](final-backend-check.json), 19:46:55 to 19:47:13 UTC, 27 September 2026 |
| Published image, actual Firebase Hosting origin | [PASS](final-firebase-check.json), 19:48:04 to 19:48:23 UTC |
| Previous image API checks | [Backend PASS](backend-check-5.json) and [Firebase PASS](firebase-check-2.json), preserved as historical observations |
| Durable booking/session prepared before revision change | [PASS](continuity-before.json), revision 00003-6th |
| Original booking/session and exact retry receipt after new revision | [PASS](continuity-after.json), revision 00004-gfq; post-check logout revoked the session |
| Explicit chunk index exemptions | [Verified](field-index-config.json), both data and revision fields |
| Initial cleanup execution | Completed successfully: `proofline-demo-cleanup-lqkwb` |
| Authenticated Scheduler-triggered cleanup execution | Completed successfully: `proofline-demo-cleanup-6ttt4`, 19:38:35.889619 UTC |
| Published-image cleanup execution | Completed successfully: `proofline-demo-cleanup-qznnz`, 19:48:54.029745 UTC |
| Published JavaScript content | [Both live hashes match source](final-static-hashes.json) |
| Final live browser walkthrough at desktop/mobile sizes | [PASS](browser-check.json): automatic roster refresh, applied/closed labels, viewport widths 375 and 1440 equal scroll width; no captured warning/error entries |

Live API assertions include health/readiness, static assets/security headers, JSON errors, secure `__session` cookies, no-store responses, missing public test controls, denied setup without a secret, distinct synthetic visitor scopes, booking/replay, cross-visitor denial/reset isolation and concurrent same-key recovery. Read the individual reports for exact assertions and limitations.

**Contention was observed and recovered, not hidden.** The final backend test received two 503 responses and the final Firebase test received one among four concurrent same-key requests. Retrying with the unchanged request/key returned 200; identical original response and one-effect assertions passed. This does not establish zero transient errors, unlimited concurrency or a latency guarantee. The continuity test demonstrates state and receipt survival across a verified new revision/traffic switch, not every possible regional outage or disaster scenario.

## Verified post-factory UI polish

The operator's initial live browser walkthrough found that a successful seating repair did not refresh the manager roster and retained “Preview only” / “Proposed closure” labels. The published source contains a narrow two-JavaScript-file operator repair outside both completed factory runs. It refreshes the selected-date roster after confirmed apply, shows applied/closed labels, and keeps a failed follow-up read separate from a successful mutation. The backend implementation is unchanged from the accepted companion.

[Local acceptance](operator-ui-acceptance.json) and the [three-test result](operator-ui-tests.log) cover roster refresh, a failed roster read after a successful mutation, and exact retry following a real committed response loss across durable restart. The local report's cloud-pending status records its earlier checkpoint; subsequent [live browser verification](browser-check.json), API reports and source-hash checks above complete that follow-up. The browser report distinguishes the full initial-image walkthrough from affected-flow and responsive checks on the patched image. This is finite Chrome verification, not exhaustive accessibility or cross-browser certification.

## Scoped configuration and access

Dedicated resources live in shared project `gen-lang-client-0444960702`. Firestore database is explicitly `proofline-tablekeeper`, never `(default)`; the demo collection is `proofline_demo`. The service uses `proofline-runtime@gen-lang-client-0444960702.iam.gserviceaccount.com`. The read-only project IAM inspection retained this identity's `roles/datastore.user` binding with:

```text
resource.name=="projects/gen-lang-client-0444960702/databases/proofline-tablekeeper"
```

The prior prefix condition was removed. This targeted project-policy check does not independently enumerate organization/folder inheritance. No unrelated project bindings are published. Deny-all client rules are attached to `cloud.firestore/proofline-tablekeeper`; the matched rules source SHA-256 is `ed1e7c11f025d9464e80e4c4584711c474a0c9b0e07802618de8d02dddadec87`. Server SDK authorization uses IAM, not those browser rules.

Read-only field API responses decoded through the official SDK confirm explicit empty indexes for `chunks.data` and `chunks.revision`: `usesAncestorConfig=false`, zero indexes, `reverting=false`. The presence of `ancestorField` is expected even with explicit settings and is not evidence of inherited indexing. [Official field semantics](https://docs.cloud.google.com/firestore/docs/reference/rest/v1/projects.databases.collectionGroups.fields)

The deployed environment specifies production security mode, Firestore, the named database, exact public origin and isolated demo flag `1`. Service metadata records two CPUs/two GiB, concurrency 16, timeout 30 seconds and maximum two instances. Minimum zero is the omitted platform default, consistent with the configured setting. The explicit HTTP startup probe checks `/health/ready` on port 8080 every ten seconds, with ten-second timeout and twelve allowed failures. The [portable deployment recipe](../../deployment/README.md) documents these boundaries.

## Preserved startup failures and operator repair

The first built image, `sha256:429e0df437255c0e5de29d3f901e323bc57de3fba236152f3d5e92b57a316a1c`, failed startup with `PermissionError` on `/app/tablekeeper/__init__.py`. Archived source was materialized as 0600 files/0700 directories; Docker COPY made it root-owned and unreadable to runtime UID 65534. The operator corrected snapshot files/directories to 0644/0755 inside a private 0700 enclosing record and rebuilt. This packaging failure is not presented as a successful deployment.

The default TCP startup check could observe nginx listening before Python was ready. Under request-based CPU allocation this produced 502 behavior before the backend completed startup. The operator configured an HTTP `/health/ready` startup probe to require application readiness. The subsequent deployed revision and live checks above passed. These are post-run operator infrastructure repairs, not undocumented changes to the original autonomous graded result.

## Cleanup and operating limits

The cleanup job uses the same deployed image, runtime identity, named database and demo collection, invoking `python -m tablekeeper.operations cleanup --limit 100`. It has one task, parallelism one, zero retries and a 300-second task timeout. The dedicated scheduler identity `proofline-scheduler@gen-lang-client-0444960702.iam.gserviceaccount.com` has `roles/run.invoker` on that named job. The enabled UTC schedule is `0 * * * *`, calling the Run API with OAuth.

The Scheduler was manually triggered for verification on the preceding image, and its created execution reached Completed=True with one successful task. The job was then updated to the published image and a new operator-triggered execution also completed successfully. This proves the configured authenticated trigger completed a job; it does not establish future unattended reliability or a specific number of expired namespaces deleted. Monitor both scheduler dispatch and job completion.

Demo authorization expires after two hours. The registry holds at most 100 retained entries, including expired entries until cleanup. A successful hourly limit-100 run can clear the full expired registry; availability between runs or after failures is bounded. The planner remains limited to six tables, four declared pairs and six considered bookings, counting every overlapping confirmed booking.

The named database reports **`freeTier: false`**. Actual billed spend is unknown. Compute, Firestore operations/storage, builds, image storage, Hosting transfer, Scheduler and cleanup can incur charges; instance limits do not cap the entire bill. Durable storage is distinct from off-host backup/disaster-recovery proof. No real customers, revenue, production certification, hidden-suite success or unlimited scale are claimed.
