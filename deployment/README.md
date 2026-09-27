# Deploy the separately accepted companion

**The companion is deployed at [tablekeeper-proofline.web.app](https://tablekeeper-proofline.web.app). The published image passed live HTTP/isolation and desktop/mobile browser checks; durable revision continuity passed on the preceding deployment.** See the [hosted evidence](../evidence/hosted/README.md) for the actual image, scoped settings, contention recovery and successful cleanup executions. This portable operator recipe documents how to reproduce the separate `product/` deployment; it does not claim the original graded BAND run created a live cloud service or that every host has tested this script.

The initial deployment used accepted evidence commit `8f749427004a35e6ac25ed34abb7997515ec4354`; its image digest is `sha256:d22729b181ac9b8df69d743d52b260fbb11039d2b46affe40876b16a0fb2d0c2`. The published operator UI follow-up uses source `053ae0d6260f79b924752949c37a8837ded4d480`, image `sha256:4242b0226aaad2aecc432cb1999a2e49530025b3da92fc36eb3f2d21b4ea6792`, and ready revision `proofline-tablekeeper-00005-dz5`. Its [local acceptance](../evidence/hosted/operator-ui-acceptance.json), [live API verification](../evidence/hosted/final-firebase-check.json) and [browser recheck](../evidence/hosted/browser-check.json) are separate post-factory evidence. The initial image and its continuity checks remain preserved. An earlier image failed because private snapshot permissions were copied into a root-owned image unreadable by UID 65534. Snapshot source now uses 0644/0755 inside the private enclosing directory; preserve that distinction.

The script plans by default. It requires a full accepted Git commit and a nonempty tracked independent acceptance report at that commit. It archives only committed `product/` source into a private directory outside the repository, scans for common credential files/key patterns, and creates a narrowly scoped Firebase config. A report's existence is not proof of acceptance: read its actual result before executing. The secret scan is a conservative screen, not proof that arbitrary secret formats are absent.

## Prerequisites and resource boundaries

Use Python 3, Git, `gcloud` and `firebase` on PATH, authenticated through their supported CLI flows. Provision the selected project with billing/APIs, one dedicated named Firestore database, one dedicated Artifact Registry repository, one dedicated Hosting site, a runtime service account and a separate scheduler service account. The script does not create these or enable APIs. Verify Cloud Build's selected build identity has only the permissions needed for this build/image publication.

For shared projects, the runtime identity must be restricted to the exact named database. Review both direct and inherited IAM grants; an additional broad grant defeats a conditional narrow grant. Firebase client rules deny browser access, while server SDK access uses IAM. Never grant a project-wide database role just to resolve an access error. The script refuses `(default)` and generates a Firestore array containing only the explicit named database. It never invokes the product's default-scoped deployment helper, `firebase init`, a project-wide Firebase deploy or `--force`.

The Hosting site must belong to the same project as the Cloud Run service. Its explicit site configuration contains no other hosting target, hooks or resource types. The empty static directory forwards every route to the accepted backend with no-store headers; application authentication remains necessary on the direct Cloud Run URL. Before selecting names, confirm that each resource is dedicated to this companion. Service/job deployment updates that named resource and clears its secret bindings; do not point it at another app.

## Prepare a plan

Set these values to actual resources and an independently accepted revision. All paths are explicit; there are no workstation-specific defaults. Use a private output directory outside this repository, not a location tracked by Git.

```sh
export DEPLOY_PROJECT='your-billing-project'
export DEPLOY_SITE='your-dedicated-site'
export DEPLOY_DATABASE='your-named-database'
export DEPLOY_SERVICE='your-dedicated-service'
export DEPLOY_REGION='us-central1'
export DEPLOY_REGISTRY='your-artifact-repository'
export DEPLOY_RUNTIME_SA="runtime-account@$DEPLOY_PROJECT.iam.gserviceaccount.com"
export DEPLOY_SCHEDULER_SA="scheduler-account@$DEPLOY_PROJECT.iam.gserviceaccount.com"
export DEPLOY_REVISION='actual-full-40-character-accepted-commit'
export DEPLOY_EVIDENCE='evidence/product/actual-independent-report.md'
export DEPLOY_SOURCE='/absolute/path/to/repository-with-product'
export DEPLOY_OUTPUT='/absolute/private/path/to/deployment-records'
```

In a POSIX-compatible shell, define a convenience function. All values are passed as separate quoted arguments, not evaluated as shell code:

```sh
deploy_companion() {
  python3 deployment/deploy.py \
    --source "$DEPLOY_SOURCE" --output-dir "$DEPLOY_OUTPUT" \
    --project "$DEPLOY_PROJECT" --site "$DEPLOY_SITE" \
    --database "$DEPLOY_DATABASE" --service "$DEPLOY_SERVICE" \
    --region "$DEPLOY_REGION" --artifact-repository "$DEPLOY_REGISTRY" \
    --runtime-sa "$DEPLOY_RUNTIME_SA" --scheduler-sa "$DEPLOY_SCHEDULER_SA" \
    --accepted-revision "$DEPLOY_REVISION" --acceptance-evidence "$DEPLOY_EVIDENCE" \
    "$@"
}
deploy_companion
```

Inspect the generated `plan.json`, source snapshot, named-database rules/indexes and runtime environment. No cloud calls occur in plan mode. Optional `--cleanup-job` and `--scheduler-name` select explicit dedicated names; otherwise they derive from the service name. Pass the same choices in every phase. For the operator's intended initial installation those names are `proofline-demo-cleanup` and `proofline-demo-cleanup-hourly`; the [hosted summary](../evidence/hosted/deployment-summary.json) records their actual deployed configuration and completed verification executions.

## Execute one phase at a time

`--confirm-reviewed` means the operator actually reviewed acceptance, resource ownership/IAM and the source for credentials. It is not a substitute for those checks. No phase runs automatically after another; failures stop without retry or broader fallback.

```sh
deploy_companion --phase build --execute --confirm-reviewed
```

Read the generated `built-image.json` and set the exact resulting digest. This binds deployment to the built artifact, not a mutable tag. The recorded source tree and image digest provide provenance; the use of an upstream base image does not establish bit-for-bit reproducible image builds.

```sh
export DEPLOY_DIGEST='sha256:actual-64-hex-character-built-image-digest'
deploy_companion --phase datastore --execute --confirm-reviewed
deploy_companion --phase service --image-digest "$DEPLOY_DIGEST" --execute --confirm-reviewed
```

The datastore phase uses `--only firestore` with a config containing exactly one named database. It does not touch default-database rules/indexes. Verify the resulting named rules/indexes and default-database noninterference, including any pending index build. The service phase uses:

- Firestore adapter with explicit project, database and `proofline_demo` collection.
- Production HTTPS/security mode, exact `https://SITE.web.app` origin and isolated public-demo flag `1`.
- Minimum 0 / maximum 2 instances, two CPUs, two GiB, concurrency 16 and 30-second request timeout.
- HTTP startup probe `/health/ready` on port 8080, every ten seconds, ten-second timeout, twelve allowed failures. A TCP listener alone is insufficient: nginx can accept connections before Python is ready under request-based CPU allocation.
- Dedicated runtime identity, no setup secret, and accepted image by digest.

Run live backend acceptance before Hosting publication: health; two independent visitor sessions with cross-namespace access denied; persistence across revision/instance restart; retry recovery; absence of test controls; setup unavailable without a secret; secure `__session` cookie and no-store responses. Origin-sensitive checks must use the configured origin. Do not disable origin checks to make direct-service tests pass.

## Deploy actual cleanup

Use the same immutable image, named database, collection and runtime identity. The job invokes `python -m tablekeeper.operations cleanup --limit 100`, with one task, parallelism one, no automatic task retry and a 300-second timeout.

```sh
deploy_companion --phase cleanup-job --image-digest "$DEPLOY_DIGEST" --execute --confirm-reviewed
deploy_companion --phase cleanup-initial --image-digest "$DEPLOY_DIGEST" --execute --confirm-reviewed
```

Inspect the actual initial execution outcome before scheduling. The following grant is **only on the dedicated job**, not the project. Verify the dedicated scheduler account does not already possess broader unrelated privileges.

```sh
deploy_companion --phase cleanup-invoker --image-digest "$DEPLOY_DIGEST" --execute --confirm-reviewed
deploy_companion --phase cleanup-schedule --image-digest "$DEPLOY_DIGEST" --execute --confirm-reviewed
```

The hourly UTC scheduler sends an OAuth-authenticated POST to the named job's Run API. Its service account receives `roles/run.invoker` only on that job. The operator must have permission to act as that account; APIs/service-agent setup must already work. Existing scheduler names cause creation to fail rather than silently replacing another schedule. Inspect before deliberately updating a dedicated existing resource.

The demo registry holds at most 100 entries and demo authorization expires after two hours. Expired entries still occupy slots until cleanup. Limit 100 permits one successful hourly run to remove the full expired registry, but capacity is not guaranteed between runs or after a failure. Monitor both capacity responses and cleanup job completion. A successful Scheduler HTTP request starts a job; it does not prove that the job finished. Scheduled cleanup is required for ongoing demo availability, not an optional README promise.

## Publish only the dedicated Hosting site

After backend and cleanup checks actually pass:

```sh
deploy_companion --phase hosting --image-digest "$DEPLOY_DIGEST" \
  --execute --confirm-reviewed --confirm-live-checks
```

Then test the real `https://SITE.web.app` origin, including login/session forwarding, independent visitor isolation, booking and manager recovery on desktop/mobile. Hosting permits the specially named `__session` cookie to reach the backend; do not assume other cookies pass through. Verify actual headers and application behavior. `pinTag` ties the Hosting release to a backend revision, but does not roll back persisted data. A partial deployment failure does not justify deleting or resetting a database.

## Evidence, costs and limitations

Private per-phase records include accepted commit/tree, acceptance-report hash, exact nonsecret command arguments, image digest, exit status and redacted command logs. Standard CLI authentication is used without printing tokens or supplying secret values. Do not enable HTTP tracing or shell/environment dumps. Review private logs before publishing selected evidence. Never commit provider credentials, service-account keys, raw visitor data or private exports.

Before claiming a live deployment, publish sanitized evidence for the actual revision/digest, named database, IAM scope, deployed limits, no-store/session behavior, durable restart, visitor isolation, initial cleanup, scheduled execution and verified Hosting URL. Syntax/help checks of this script are not that evidence. The original graded service reports remain separate.

Scaling limits reduce exposure but are not a complete spending cap. Billing includes compute, requests, Firestore operations/storage, builds, artifact storage, Hosting bandwidth, Scheduler and cleanup execution. No free allowance or zero-cost claim is made. A named database may have `freeTier: false`; inspect the actual resource. Monitor usage and configure appropriate budget controls separately, without altering unrelated project resources. Actual billed spend remains unknown until observed.

Primary references: [Firebase named-database configuration](https://firebase.google.com/docs/cli#configuration_for_multiple_cloud_firestore_databases), [database selection and IAM](https://firebase.google.com/docs/firestore/manage-databases), [Hosting with Cloud Run](https://firebase.google.com/docs/hosting/cloud-run), [Hosting cookie/cache behavior](https://firebase.google.com/docs/hosting/manage-cache), [Cloud Run deployment flags](https://docs.cloud.google.com/sdk/gcloud/reference/run/deploy), [scheduled Cloud Run jobs](https://docs.cloud.google.com/run/docs/execute/jobs-on-schedule).
