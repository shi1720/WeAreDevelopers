# Tablekeeper companion operations

This separately traced companion starts from the unchanged stage-4 copy recorded in `evidence/product/baseline.json`. It supports one venue per namespace, 1-6 tables, at most four declared pairs, and closure repair considering at most six overlapping confirmed bookings. The commercial target is a small 4-6-table venue. Every overlap counts, even if its current table is unaffected. Do not split a larger closure into independent plans and describe that as a globally optimal solution.

Shivam Gupta leads product direction and factory configuration. The coding seats authored implementation and verification. This is a pilot, without a production certification, unlimited-scale claim or SLA. The acceptance report outside this folder identifies executed checks and remaining operator gates.

## Local Python 3.12

From a fresh clone, enter `product/`. SQLite mode needs only Python 3.12 and the standard library. Use a private directory outside the checkout for state and secrets. Do not use Python 3.9 or assume an untested Python version has identical timezone/parser behavior.

```sh
umask 077
mkdir -p "$HOME/.local/share/tablekeeper"
python3.12 -c 'import secrets,pathlib; pathlib.Path.home().joinpath(".local/share/tablekeeper/setup-secret").write_text(secrets.token_urlsafe(32))'
export TABLEKEEPER_MODE=development
export TABLEKEEPER_PUBLIC_ORIGIN=http://localhost:8080
export TABLEKEEPER_DB="$HOME/.local/share/tablekeeper/venue.sqlite3"
export TABLEKEEPER_SETUP_SECRET_FILE="$HOME/.local/share/tablekeeper/setup-secret"
python3.12 -m tablekeeper.server
```

Visit the exact configured origin and use the setup screen. Read the protected secret locally when entering it; do not place it in a URL, chat, command argument, screenshot or browser storage. Setup atomically creates the owner and venue and consumes setup. Remove the configured setup secret after setup. Inventory and timezone are fixed thereafter; the manager policy screen publishes effective-dated hours, capacities, grid, duration and cutoff. Setup bounds are not a promise of unlimited booking history: storage capacity errors stop writes without discarding history or receipts.

The default mode is production, with no synthetic accounts and no test routes. It refuses startup without an explicit HTTPS public origin. Development mode explicitly permits HTTP. `TABLEKEEPER_PUBLIC_DEMO=1` separately enables the isolated synthetic demo; it is never inferred from absent or corrupt state. See `demo.md`. Keep real guest data out of public demos.

The Python server is a local verification entry point. Internet deployments use the bundled nginx container boundary, with TLS supplied by Cloud Run/Hosting or a separately managed trusted TLS proxy. Do not expose the Python port directly as a general internet server.

## Container and durable local volume

```sh
docker build -t tablekeeper-companion .
docker volume create tablekeeper-data
docker run --name tablekeeper --cpus 2 --memory 2g \
  -p 8080:8080 -v tablekeeper-data:/data \
  -e TABLEKEEPER_MODE=development \
  -e TABLEKEEPER_PUBLIC_ORIGIN=http://localhost:8080 \
  -v "$HOME/.local/share/tablekeeper/setup-secret:/run/setup-secret:ro" \
  -e TABLEKEEPER_SETUP_SECRET_FILE=/run/setup-secret \
  tablekeeper-companion
```

The image runs as UID 65534. A bind-mounted state directory and setup file must be readable/writable as appropriate by that UID; private file permissions must remain 0600. A named volume is initialized with the image directory's ownership. For offline acceptance, use `--network none`, omit port publication, and drive localhost from `docker exec` with Python's standard library. SQLite runtime has no outbound dependency. The build downloads pinned Python dependencies and Debian nginx packages; the base tag and Debian security packages can advance, so retain tested image digests in execution evidence. Python dependencies are version/hash locked in `requirements.txt`.

`PORT` controls the public listener (8080 default; 8081 reserved for the private backend). The container runs nginx and the backend under a supervisor and propagates termination. nginx buffers and limits request bodies to 64KiB, header/body timeouts to five seconds, per-client connections to 16, and upstream waits to 20 seconds. The backend independently limits bodies to 64KiB, headers to 16KiB, path length to 4096, active request threads to 32, socket inactivity to five seconds and connection lifetime to 15 seconds. A timed-out write can still have committed: retry the exact saved request/key. Routine HTTP access logging is disabled to avoid guest references in paths. Forwarded headers cannot change origin checks, secure-cookie policy or throttling.

## Storage guarantees and limits

SQLite uses WAL, synchronous FULL commits and an OS ownership lock for a single writer process. Candidate state is committed before returning; exceptions roll back. A second writer/restore process refuses the same store. Read-only backup/status processes may coexist with the owner. Do not bypass the ownership lock with another implementation. Keep the database, WAL and shared-memory files on a reliable local filesystem, not an object bucket or network mount with uncertain locking semantics.

Firestore mode uses `TABLEKEEPER_STORAGE=firestore`, explicit `GOOGLE_CLOUD_PROJECT`, optional `TABLEKEEPER_COLLECTION=tablekeeper`, and optional `TABLEKEEPER_DATABASE=(default)`. Workload ADC authenticates the backend; no browser SDK or service-account key is used. Each namespace root is a contention boundary. Its revision and up to eight unindexed byte chunks are read transactionally; the callback derives a private candidate; domain state, original receipts and session metadata commit atomically. SDK retries can rerun the callback. No process-local published state is authoritative. Five transaction attempts bound contention retries; an uncertain transport outcome returns an honest retry error. Clients recover with unchanged body and idempotency key.

Serialized namespace state is capped at 4MiB. Chunks are at most 512KiB, with SHA-256, schema, revision and length checks. Actual protobuf writes are measured against an 8MiB request ceiling and 768KiB document ceiling, below Firestore's 10MiB request and 1MiB document limits. Both old and new unindexed bounded state fit the transaction margin. Capacity errors preserve existing state and history. Unsupported/corrupt state fails closed and is never replaced with empty/demo data. Do not modify chunk documents manually.

The wrapped domain schema retains UTC half-open occupancy, IANA gaps/folds, declared pairs, immutable accepted policy terms and histories, recurring exceptions, atomic collective CAS, deterministic bounded closure optimization and original successful retry receipts. PATCH/cancel receipts live in companion metadata and are validated against historical records. The original graded HTTP harness assumptions of bearer auth, unauthenticated test reset/import/export, synthetic initialization, no setup, and ephemeral storage no longer apply. Those harnesses have not thereby been rerun or claimed passing against this companion. Original folders remain unchanged.

## Sessions and security boundaries

The only browser credential is `__session`, HttpOnly, SameSite=Lax and Secure in production. Firebase forwards this cookie name. `/auth/session` returns the CSRF token in private, no-store JSON; writes send `X-CSRF-Token` and the exact configured `Origin`. No wildcard credentialed CORS is enabled. Authentication is still required at the public Cloud Run URL, regardless of Origin. Session tokens and CSRF tokens are digested in durable state. Namespace locators in cookies are not authority; the secret must match a live session inside that namespace.

Authenticated sessions last at most 12 hours and expire after two hours of inactivity. Anonymous pre-auth sessions last 30 minutes. A user has at most eight active sessions; a namespace has at most 1024 session entries. Expiry is enforced during each request. Logout revokes server-side. Password change revokes all prior sessions and issues one replacement. Login/signup/setup attempts are bounded to eight per account label per minute and 60 per namespace per minute; password checks are bounded to eight per user per minute. Throttle state is durable and bounded to 1024 entries. Booking operations have no dependency on authentication-attempt quotas. As with any small pilot, sustained distributed denial-of-service remains an operator concern.

Dynamic, authentication, error and session responses use `Cache-Control: private, no-store`. The service adds restrictive local-asset CSP, frame denial, no-referrer, nosniff and production HSTS. Keep pending browser requests private: they contain synthetic or guest booking details but no credentials, are account/namespace scoped, and require explicit recovery/discard after uncertainty. Backup files include password hashes, sessions and guest data and must remain private.

Email addresses are account identifiers only. There is no verification email, recovery email, SMS or payment integration. The operator may assist account recovery only after independently confirming identity outside this application. Write a new random temporary password to a 0600 protected file, stop SQLite's writer if applicable, and run:

```sh
python3.12 -m tablekeeper.operations --namespace main reset-password \
  --user-id owner --password-file /private/new-password
```

The command changes the hash and revokes that user's sessions atomically. Share the temporary password through an appropriate private channel, require a password change, and remove the temporary file. Never claim an email was sent. Application managers cannot use this operator CLI through HTTP.

## Backup, restore and incident recovery

All commands run from `product/` under the configured storage environment. Backup takes one consistent namespace snapshot even during writes. Output creation is exclusive with mode 0600 and fsync; it never overwrites an existing backup. Use a new destination each time:

```sh
python3.12 -m tablekeeper.operations --namespace main status
python3.12 -m tablekeeper.operations --namespace main backup /private/backups/venue-2026-09-28.json
```

Back up nightly and before releases/policy maintenance; copy encrypted backups to a separate private off-host location with limited operator access, keep a defined retention window, and rehearse restoration. A local volume is not an off-host backup. A nightly schedule can lose up to the changes since the last successful backup; this is not zero-data-loss replication.

For SQLite, stop the server before maintenance/restore and point `TABLEKEEPER_DB` at the target. For Firestore, the same commands use ADC and an explicit namespace. To restore into a separate test target, use a new SQLite path or Firestore collection, with no public traffic. Maintenance-on can initialize that empty target. Keep the returned current revision:

```sh
python3.12 -m tablekeeper.operations --namespace main maintenance on
python3.12 -m tablekeeper.operations --namespace main restore /private/backups/venue-2026-09-28.json \
  --expected-revision 1 --revoke-sessions
python3.12 -m tablekeeper.operations --namespace main maintenance off
```

Replace `1` with the actual maintenance revision. Restore validates schema/checksum/domain relations before modifying existing state, requires maintenance and CAS, and keeps maintenance active until explicitly cleared. Concurrent writes cannot be silently discarded. Bad restore leaves the prior state usable (clear a previously enabled maintenance lock when appropriate). Restoring without `--revoke-sessions` preserves sessions for controlled continuity but can resurrect sessions revoked after the backup. Use `--revoke-sessions` for incidents; it retains booking identities, history and receipts while requiring fresh login. Absolute expiration is never extended. After restore, verify readiness, owner access, original receipt replay and a small booking/history sample before admitting traffic.

`GET /health/live` and `/health` report process liveness; `/health/ready` reads and validates durable main state and refuses maintenance. A live process alone is not ready. Shutdown drains bounded active requests before closing the store. Public storage failures disclose no payload and instruct unchanged-request retry.

## Public demo operations

Explicit demo mode permits at most 100 registered namespaces, ten creations per minute globally, a two-hour namespace lifetime and no real account signup/password change within demos. Each visitor gets a cryptographically random namespace and synthetic seeded identities. Role switches and resets remain in that namespace; expiry rejects access synchronously. Run bounded cleanup at least hourly and more often for a busy demonstration:

```sh
python3.12 -m tablekeeper.operations cleanup --limit 20
```

For SQLite, stop its writer for cleanup; for Firestore cleanup can run alongside service traffic. It deletes only expired namespaces and then removes registry entries. At capacity the service refuses new demos until cleanup; it does not evict a live visitor. Do not use demo mode for real venue operation.

## Hosting deployment, performed later by the operator

The requested preferred site is `proofline-tablekeeper.web.app`; availability is not claimed. Provision the Firebase/GCP project, billing, a supported Cloud Run region, Firestore Native database, Artifact Registry/build APIs, Firebase Hosting site and a dedicated backend service identity. Grant only backend database access (for example `roles/datastore.user`) and access to the one setup secret. Grant build/deploy permissions separately. Browser rules deny all. Retain the index exemptions in `firestore.indexes.json` for unindexed byte chunks. Cloud mode refuses SQLite on Cloud Run. Do not mount object storage as its database.

Create the high-entropy setup secret in Secret Manager out of band and pin its numeric version. With authenticated operator CLIs installed, run:

```sh
python3.12 deploy/deploy.py --project YOUR_PROJECT --region us-central1 \
  --service-identity tablekeeper-backend@YOUR_PROJECT.iam.gserviceaccount.com \
  --setup-secret tablekeeper-setup:1 --site proofline-tablekeeper
```

The script deploys min instances 0, max instances 2, concurrency 16, 2 CPU/2GiB, 30-second request timeout, workload identity and the exact HTTPS origin. It then deploys Hosting rewrites, deny-all rules and chunk index exemptions. Hosting routes every request to the actual backend, including unknown API routes; there is no SPA fallback that disguises API errors as HTML success. All local assets ship in the image. The public Cloud Run invoker permission is necessary for Hosting but does not bypass application authentication. Setup is done once through Hosting; remove the setup secret binding afterwards.

Cloud Run plus Hosting requires billing linkage and may incur charges. Hosted Firestore necessarily uses Google API network access and is not an offline runtime. After room acceptance, the operator must test real deployed Firestore contention, restart/rolling revision behavior, setup, cookie forwarding, CSRF, backup/restore, quotas and logs; configure budget alerts, backup scheduling and monitoring; then decide whether to admit real guests. This room does not access credentials, create resources, deploy, publish or claim deployed acceptance.

Primary references: [Hosting with Cloud Run](https://firebase.google.com/docs/hosting/cloud-run), [Hosting cache and cookies](https://firebase.google.com/docs/hosting/manage-cache), [Firestore transactions](https://firebase.google.com/docs/firestore/manage-data/transactions), [contention](https://firebase.google.com/docs/firestore/transaction-data-contention), and [quotas](https://firebase.google.com/docs/firestore/quotas).

## Development failure controls and tests

Only explicit `TABLEKEEPER_MODE=development` honors `TABLEKEEPER_FAULT=before_commit`, `after_commit`, or `commit_failure`, paired with `TABLEKEEPER_FAULT_ARM_FILE=/private/marker`. Create the marker after setup/session preparation. The next transaction removes it once, then exits with 86 before commit, exits with 87 after commit/before response, or raises a persistence error. Production ignores these variables. There is no HTTP fault endpoint. Any committed transaction can consume the marker, so acceptance drivers must coordinate exclusive traffic.

Author unit checks: `PYTHONPATH=. python3.12 -m pytest -q tests/author_companion.py`. Firestore tests require the locked dependency and `FIRESTORE_EMULATOR_HOST`; independent acceptance scripts and evidence are maintained by Verifier. Do not label author checks independent verification.
