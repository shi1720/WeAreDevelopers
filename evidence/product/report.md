# Tablekeeper companion factory report

Release gate: accepted for the bounded local/emulator pilot at 2026-09-27T19:23:13Z. The documented private-secret delivery and real owner setup also passed. This is a separate post-graded companion, not another graded stage or an original submission rerun.

## Provenance and ownership

- Source baseline: `330f1c8321670ca7d34b6b7127c0fb73df84ca25`.
- First unchanged copy: `1448eea24239a59e03941fc3a1a691b86bad19d9`. Source stage-4 and copied product trees both equal `53912d0263085f441225f962351d8876fef68ca1`; see [baseline.json](baseline.json).
- Independently checked runtime: `d6194c8c9575f0a6b85ec2a322e8a65cbb9af740`, including implementation repair `8d00205c67f2769240f65f24d3afe39fcf8fccb4`.
- Corrected independent contention driver: `6e74d8e42294dd85ea724729c7e68b322593ca1f`. It changes test expectations only for an explicitly observed unknown committed outcome, and strengthens exact-receipt assertions.
- Independent evidence commit: `8f749427004a35e6ac25ed34abb7997515ec4354`.

Accepted code/test deliverable revision: `8f749427004a35e6ac25ed34abb7997515ec4354`. Its only product difference from the independently tested runtime revision is the corrected, independently executed multiprocess test driver. Product implementation is frozen; subsequent coordinator commits contain reporting evidence and factual factory metadata only.

Shivam Gupta leads the project, product and factory configuration. Proofline Pilot Engineer authored backend/storage/operations/deployment; Proofline Pilot Experience authored UI and user/demo documentation; Proofline Pilot Verifier independently authored and ran acceptance checks; Proofline Pilot Coordinator distributed work, reviewed source and visuals, managed repair/release gates and authored this report. Implementation is agent-generated. Original author commits and failures remain preserved. No original graded folder, mandate, original evidence, root packaging or original commit was modified; no push, merge, rebase, squash, publication or cloud provisioning was performed.

## What ships

One venue per namespace, Python 3.12, local SQLite and hosted Firestore adapters, atomic candidate-state commits and exact retry receipts, protected one-time setup, durable cookie sessions/CSRF/revocation, isolated bounded synthetic demos, private backup and maintenance/CAS restore, booking list/edit, narrow manager roster, and browser recovery after uncertain booking/amendment/repair requests. The original cream/forest/terracotta identity, history, policy, recurring and closure screens remain.

Supported bounds are 1-6 tables, at most four declared pairs and six overlapping confirmed bookings in closure planning, counting all overlaps. No larger closure is split with a claim of global correctness. Hosted storage uses workload ADC and Firestore, never Cloud Run's ephemeral SQLite disk. Firestore chunks are <=512KiB, serialized namespace state <=4MiB, and encoded requests/documents have conservative margins. Capacity errors do not truncate history or receipts.

## Independent evidence

The authoritative detail is [Verifier's final report](verification/final-report.md), [clause coverage](verification/coverage.md), [failures and driver corrections](verification/findings.md), and [exact command records](verification/runs/). Every run record identifies the source and driver revisions, command, exit status and measured duration. Do not add overlapping run durations or reinterpret historical results as companion passes.

| Final gate | Observed result | Measured runner time |
|---|---|---:|
| Both storage adapters, HTTP, domain, security, multiprocess and crash cases | 87 passed; one driver status assertion failed after unknown committed outcome | 105.230903s |
| Corrected multiprocess receipt/auth cases | 2 passed, preserving one effect and exact original receipts; resolves that driver failure | 18.875995s |
| Real Chromium plus inherited pure domain tests | 23 passed: 5 browser scenarios and 18 pure tests; 14 additional subtests | 11.321539s |
| Clean-clone image build | Exit 0, cached build with network disabled | 3.074906s |
| Empty-volume offline container, restart and separate restore | Exit 0; identities, accepted terms, histories, series, policies, closures and original receipts retained | 2.410410s |
| Eight slow header/body clients on unchanged repaired proxy | All closed within observation window; healthy booking about 14ms | 24.860701s |
| Real proxy upstream timeout | 504 retained private,no-store and security headers | 20.774200s |
| Coordinator runbook secret-file check | Host-owned 0600 file, non-root offline empty-volume container: readiness 200 and actual owner setup 201 | 2.528866s |

The first two rows collectively cover all 88 operational cases; they are not a fabricated single 88-pass run. Final image: `sha256:ad581e03b6a305dd34f6f08149f6fc5e7fe6cf768f7d45108bcbd951ee754c79`. SQLite ran as UID/GID65534 with `--network none --cpus 2 --memory 2g`. Python3.12.14 and shipping Firestore SDK2.21.0 were independently exercised. Emulator Firestore uses network access; hosted Firestore is not an offline runtime.

The supplemental runbook command was `/tmp/proofline-official-spec/.venv/bin/python evidence/product/secret-smoke.py`, exit0. Its [exact Docker commands and result](secret-smoke-setup.json) contain no secret value. This was tested on the supplied Colima host; the runbook's ownership requirement still applies on other hosts. The reviewer cleaned its own container, volume and temporary synthetic secret afterward. An earlier readiness-only pass is retained in [secret-smoke.json](secret-smoke.json).

Browser gates deliberately discarded committed responses, reloaded and restarted the service, then recovered the exact body/key/receipt for booking, individual edits, recurring amendments and closure apply. They checked account switching, current series summaries, keyboard interaction and no overflow at 1440px/375px. Synthetic captures are in [independent screenshots](verification/screenshots/final-d6194c8/) and [Experience's screenshot manifest](experience/screenshots.json). Coordinator additionally inspected setup, booking list, roster, closure preview and recurring summary captures.

## Genuine review and repair

[Coordinator review notes](review-notes.md) and Verifier findings preserve the work: case-sensitive idempotency header conversion; insufficient maintenance/setup/demo metadata validation; anonymous session pressure and reset recovery scope; proxy buffering that bypassed total read deadlines; orphan Firestore locks and unbounded SDK work; partial SQLite/Firestore schema corruption mistaken for new state; malformed setup owner handling. Authors repaired these in separate commits and Verifier rechecked them. Driver mistakes involving HTML option visibility, CSP string evaluation, asynchronous refresh, expiry fixtures and unknown-outcome status expectations remain recorded separately. No domain assertion was weakened to disguise an application defect.

## Limits and operator gates

This is a defensible bounded pilot, not security certification, an SLA, unlimited scale or deployed acceptance. Per-namespace Firestore roots are contention boundaries. SDK work has an eight-second network budget, four-second RPC ceiling and bounded transaction retries, with a separate rollback cleanup allowance. The emulator retained a killed transaction lock for about61 seconds; unchanged-request recovery eventually succeeded without resetting state. That is not a claim about deployed latency.

The original official HTTP harness was not rerun against production companion transport. Its unauthenticated reset/import/export, synthetic fixture initialization, immortal bearer sessions and ephemeral storage assumptions intentionally no longer apply. Original domain algorithms remain, with independent selected contract checks and planner-oracle comparisons; every old swap/error-order/no-op/series permutation was not exhaustively ported. Sustained distributed denial-of-service, every capacity permutation, exhaustive accessibility and all browsers were not tested. These residuals are disclosed in the coverage matrix.

The operator still provisions billing, project, Firestore Native database, service identity/IAM and setup secret; verifies preferred `proofline-tablekeeper.web.app` availability; runs the parameterized deployment script; independently tests real Hosting cookie forwarding/TLS and deployed Firestore contention/revisions/recovery; configures monitoring, budgets and off-host backups; exports this room and publishes/merges preserved commits. Those actions were not performed here. Firebase Hosting plus Cloud Run can incur charges. No real guest data or provider credentials were used.

There is no email verification, automated recovery email, payment or SMS integration. Safe owner assistance and incident restore revocation are documented. A nightly backup may lose changes since the last successful backup; a local volume is not an off-host backup. Restoring old sessions can resurrect later revocations unless incident restore revokes them.

## Run the synthetic demo

From `product/`, with Python3.12 and a private empty state location:

```sh
TABLEKEEPER_MODE=development \
TABLEKEEPER_PUBLIC_ORIGIN=http://localhost:8080 \
TABLEKEEPER_PUBLIC_DEMO=1 \
TABLEKEEPER_DB="$HOME/.local/share/tablekeeper-demo/venue.sqlite3" \
python3.12 -m tablekeeper.server
```

Open `http://localhost:8080/demo` and create an isolated synthetic visit. On the prepared task host, `/tmp/proofline-official-spec/.venv/bin/python` is the verified Python3.12 executable if `python3.12` is not on PATH. No setup secret is needed for demo-only exploration. The [demo runbook](../../product/docs/demo.md), [operations/deployment guide](../../product/docs/operations.md) and [user guide](../../product/docs/user-guide.md) give the complete flow. Internet use requires the documented TLS/proxy configuration; the command above is explicit local development.

## Time and usage

Dispatch was received at 2026-09-27T18:17:09.759Z; acceptance was recorded at 2026-09-27T19:23:13Z. Measured dispatch-to-acceptance elapsed time: 3963.241 seconds, about 66 minutes. Reporting/publication preparation follows that checkpoint. Room-attributed usage queries returned no row for this fresh room. Token usage and provider-billed spend are therefore unknown; unrelated/unattributed totals are not assigned to this task and no cost estimate or zero-cost claim is made.
