# Hosted companion: operator deployment evidence

**Status: the first image built but failed Cloud Run startup; corrected materialization/rebuild and live acceptance are pending.** This report is an operator evidence scaffold. It does not establish that the website works, that live persistence/isolation checks passed, or that scheduled cleanup is running. Replace pending rows only with observed results and sanitized supporting records.

This is the separately built operational companion. Its deployment does not change or extend the original four-stage BAND run's test results. The frozen graded folders and their room export retain their original provenance.

## Artifact identity

| Item | Recorded value |
|---|---|
| Accepted companion evidence commit | `8f749427004a35e6ac25ed34abb7997515ec4354` |
| Runtime implementation revision | `d6194c8c9575f0a6b85ec2a322e8a65cbb9af740` |
| Accepted `product/` Git tree | `81f770ca92f61af4c58e5a763d9a466a671804c8` |
| First built image digest, rejected for cloud startup | `sha256:429e0df437255c0e5de29d3f901e323bc57de3fba236152f3d5e92b57a316a1c` |
| Artifact Registry image | `us-central1-docker.pkg.dev/gen-lang-client-0444960702/proofline/proofline-tablekeeper` |
| Build ID, immutable build record and time | **PENDING operator attachment** |
| Deployed Cloud Run revision / resolved image digest | **PENDING observation** |
| Live Hosting release/version and time | **PENDING observation** |

The accepted commit and product tree above were read from Git. Image build success/digest were supplied by the deploying operator; attach the actual build record before treating this table as independently checked build provenance. The companion acceptance report records local and emulator evidence with explicit gaps. It does not claim real Cloud Run, Firestore IAM or Hosting behavior was already tested.

## Dedicated scope within the shared project

- Project: `gen-lang-client-0444960702`; region: `us-central1`.
- Named Firestore database: `proofline-tablekeeper`, not `(default)`.
- Runtime identity: `proofline-runtime@gen-lang-client-0444960702.iam.gserviceaccount.com`.
- Hosting site: `tablekeeper-proofline`; intended URL: `https://tablekeeper-proofline.web.app`. **Reserved/intended address, not yet a verified live application.**
- Cloud Run service: `proofline-tablekeeper`; collection: `proofline_demo`.
- Cleanup job: `proofline-demo-cleanup`; hourly scheduler: `proofline-demo-cleanup-hourly`.
- Scheduler identity: `proofline-scheduler@gen-lang-client-0444960702.iam.gserviceaccount.com`.

Only dedicated resources are in scope. Do not publish full project IAM inventories or unrelated applications' resource details. The [portable deployment recipe](../../deployment/README.md) generates a config with one explicit Hosting site and one explicit named database, and never calls the default-scoped product helper. Actual operator command evidence must still establish what was deployed.

## Preprovision safeguards observed

The operator's private preprovision configuration contains a one-entry Firestore array with `database: proofline-tablekeeper`. Its rules deny all browser/client reads and writes. The private release observation identifies `cloud.firestore/proofline-tablekeeper`, created/updated at `2026-09-27T19:07:48.141635Z`, ruleset `73bb5c10-1d83-4dcd-bce2-dbc0a331b908`, and records an exact source match with SHA-256 `ed1e7c11f025d9464e80e4c4584711c474a0c9b0e07802618de8d02dddadec87`. The Firebase CLI preprovision log reports successful rules/index deployment for this named database. Attach a sanitized release/rules extract here; do not expose unrelated project rules.

The later private IAM removal result retains the runtime's `roles/datastore.user` binding with this exact condition:

```text
resource.name=="projects/gen-lang-client-0444960702/databases/proofline-tablekeeper"
```

The earlier `startsWith` binding was removed. Older private inventory summaries still show that prefix-based state and must not be copied as the final configuration. This reviewed result supports the narrow binding change; a live request under the deployed runtime identity and a review for additional inherited/broad grants remain separate verification steps. Server SDKs use IAM and bypass browser Security Rules; deny-all rules alone do not constrain a privileged server identity.

The configured index exemptions target `chunks.data` and `chunks.revision`. A subsequent read-only Firestore Admin API check parsed both responses through the official Python SDK Field protobuf: each has an index configuration present, `usesAncestorConfig=false`, zero indexes and `reverting=false`. Both explicit empty-index configurations are verified in [field-index-config.json](field-index-config.json). The earlier concern based on the presence of `ancestorField` was resolved: that field is also present for explicit configurations and names the ancestor that would apply if the override were removed. It does not itself indicate inheritance. [Official field semantics](https://docs.cloud.google.com/firestore/docs/reference/rest/v1/projects.databases.collectionGroups.fields)

Official references: [named database selection and IAM](https://firebase.google.com/docs/firestore/manage-databases), [multi-database Firebase configuration](https://firebase.google.com/docs/cli#configuration_for_multiple_cloud_firestore_databases), [server SDK rules boundary](https://firebase.google.com/docs/firestore/security/rules-conditions).

## Preserved deployment failure

The operator reports that the first image at digest `429e0df437255c0e5de29d3f901e323bc57de3fba236152f3d5e92b57a316a1c` failed startup with `PermissionError` on `/app/tablekeeper/__init__.py`. The deployment wrapper had materialized archived source files as 0600 and directories as 0700; Docker COPY made them root-owned, unreadable to the accepted image's UID 65534. This is a deployment packaging failure, not a successful launch. The operator changed snapshot file/directory modes to 0644/0755 under a private 0700 enclosing record and initiated a rebuild. **Replacement image digest and startup result remain pending.** Preserve the actual failed revision/log and corrected build record when finalizing this report.

## Deployment and live acceptance record

| Required observation | Current result / evidence |
|---|---|
| Actual deployed image matches accepted build digest | PENDING |
| Production mode, Firestore adapter, explicit named database/collection and exact origin | PENDING deployed environment inspection |
| Dedicated runtime identity; exact database-scoped IAM; no default-database changes | Preprovision binding reviewed; deployed identity/access and noninterference PENDING |
| Min 0 / max 2 instances, CPU 2, memory 2 GiB, concurrency 16, timeout 30 seconds | Intended settings; PENDING deployed inspection |
| Public demo enabled, no setup secret and no default real manager credentials | Intended configuration; PENDING live negative checks |
| HTTPS Hosting route, `__session` forwarding, secure cookie and no-store headers | PENDING |
| Two browser visitors cannot read, mutate, reset or assume roles in the other's demo | PENDING |
| Guest booking/edit and manager preview/apply at desktop/mobile sizes | PENDING |
| Persistence after new revision/instance; original retry receipt after uncertain response | PENDING |
| Live concurrent mutations preserve one effect and original receipt | PENDING |
| Public test/import/export routes absent; anonymous owner setup denied | PENDING |
| Active chunk-field index exemptions in the named database | Verified read-only for data and revision; see field-index-config.json |
| Cleanup job uses same digest/identity/database, limit 100; initial execution succeeds | PENDING |
| Dedicated scheduler identity has invoker only on the cleanup job | PENDING job-scoped binding and broad-grant review |
| Hourly authenticated scheduler dispatch and completed cleanup execution | PENDING; API dispatch success alone is insufficient |
| Final public URL opened and full workflow verified | PENDING |

Attach UTC timestamps, command exit status, resource/revision/digest, synthetic scenario, expected/actual result and limitations for each observation. Use selected nonsecret extracts, not full raw API responses, cookies, bearer tokens or visitor records. A pass in an emulator does not fill a live-cloud row.

## Operating and cost boundaries

This deployment is a synthetic visitor demo, not the authoritative booking book of a real restaurant. Each visitor receives an isolated demo namespace with a two-hour authorization lifetime. The registry permits at most 100 retained entries, including expired entries until cleanup. A successful hourly cleanup with limit 100 can remove the full expired registry; it does not guarantee spare capacity between runs or after failures. Monitor capacity errors and completed job executions.

The database provisioning record reports **`freeTier: false`**. No Firestore free allowance, zero-cost deployment or current cash bill is claimed. Cloud Run, Firestore reads/writes/storage, build execution, Artifact Registry, Hosting transfer, Scheduler and cleanup can incur charges. Instance caps and timeouts limit some exposure but do not cap the whole project's bill. Any budget controls must preserve unrelated shared-project services.

The planner still supports at most six tables, four declared pairs and six considered bookings. All overlapping confirmed bookings count. The companion has bounded store/network operations and known emulator precommit lock recovery observations; none establishes a universal deployed request-latency guarantee. Durable storage is distinct from off-host backup and tested disaster recovery. Production certification, real customers, revenue, hidden-suite success and unlimited scale are not claimed.

**Finalization action:** replace the top status and pending rows only after the deploying operator captures actual results. Preserve preprovision failures and incomplete snapshots as history. Do not change the original graded evidence to imply it tested this cloud deployment.
