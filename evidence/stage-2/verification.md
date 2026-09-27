# Stage 2 independent acceptance

Reviewer recommendation: **PASS**. Coordinator controls acceptance and copy-forward.

Tested implementation/root revision: `e4fc1c5bf52769927b50e139be1d380b1c044aeb`; full stage-2 tree `e8230b65ae7a84a48e1d659c1c4f6999b1105898`. Source stayed unchanged during review. Reviewer additions after execution contain only independent tests/evidence/coverage. Stage 1 remains byte-identical to accepted `3813508b5624b4ae89a346b68611a595f83cfde5`.

| Check | Result | Measured duration |
|---|---|---|
| Independent HTTP suite | 30/30, exit 0 | unittest 8.142s; wrapper 8.302s |
| Source-review HTTP boundaries | 2/2, exit 0 | unittest 0.441s |
| Independent browser scenarios | 7/7, exit 0 | per scenario below |
| Author implementation tests, independently executed | 41/41, exit 0 | unittest 8.244s |
| Official host suites 1 + 2 | 120/120 + 25/25, exit 0 | wrapper 46.109s |
| Official isolated suites 1 + 2 | 120/120 + 25/25, exit 0 | time real 41.18s |
| Next-stage overshoot, both modes | expected first stage-3 failure; 7 collected, 1 failed before stop | see preserved logs |

Browser scenario durations: routes/grid/mobile/desktop/assets 1.010s; single lost response 0.803s; pair lost response 0.828s; single conflict refresh 0.749s; pair conflict refresh 0.710s; stale search 0.691s; live stage-1 upgrade pending retry 0.836s. Total process duration was not separately measured. No stage-2 acceptance failures occurred. Earlier stage-1 infrastructure failures remain in stage-1 evidence.

## Reproduction

From repository root, against disposable stage-2 target and genuine stage-1 source:

```sh
TABLEKEEPER_BASE_URL=http://127.0.0.1:18092 /tmp/proofline-official-spec/.venv/bin/python -m unittest discover -s stage-2/tests -p 'independent_*.py' -v
TABLEKEEPER_BASE_URL=http://127.0.0.1:18092 TABLEKEEPER_STAGE1_URL=http://127.0.0.1:18091 TABLEKEEPER_SCREENSHOTS=evidence/stage-2 /tmp/proofline-official-spec/.venv/bin/python stage-2/tests/independent_browser.py
```

The recorded initial HTTP run had 30 cases; the source-review file added two separately executed cases afterward. Current discovery therefore has 32 cases, not a claim of a second 32-case execution.

From stage-2: `/tmp/proofline-official-spec/.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v`.

From `/tmp/proofline-official-spec`, official commit `803560d2a678ace1414465c098eb0ab5380ffade`:

```sh
.venv/bin/python -m harness run --track tablekeeper --repo /Users/shivamgupta/Downloads/we-are-developers --stage 2 --out /Users/shivamgupta/.cache/proofline-checks/s2-host-01
.venv/bin/python -m harness run --track tablekeeper --repo /Users/shivamgupta/Downloads/we-are-developers --stage 2 --mode isolated --out /Users/shivamgupta/.cache/proofline-checks/s2-isolated-01
```

Use NEW output directories when reproducing. Environment: PATH=/tmp/proofline-docker-build-tools:/opt/homebrew/bin:/usr/local/bin:/Users/shivamgupta/.local/bin:/usr/bin:/bin; DOCKER_CONFIG=/tmp/proofline-public-docker-config; DOCKER_HOST=unix:///Users/shivamgupta/.colima/default/docker.sock. Inherited HTTP(S)/ALL proxy variables removed. The inspected adapter injects proxy build args only; all non-build Docker commands delegate unchanged. See factory recovery documentation. All 65 tracked official mirror files independently byte-compared identical; harness/tests untouched.

During isolated execution, network `df-run-a619df00392e4af5b981483f4ab29ccc` was inspected `Internal=true`; service `df-svc-ad85df499780` had NanoCpus=2000000000 and Memory=2147483648. Both service and runner environment had no proxy variables. Runner resource limits are those of the official harness (not constrained like service). Reviewer HTTP target image `e8d8da26d0f4` was built from the frozen candidate. Screenshots are real rendered synthetic fixtures, inspected at 375px and desktop.

## Review findings and limits

Reviewed inherited source plus all stage-2 changed service modules, static assets and demo/bootstrap/deployment boundaries. No material contract violation found. Tests cover immutable original receipts vs canonical table-set order, malformed set/member types, nontransitivity, cancellation of both members, atomic swaps/rollback, 50-way contention, old credential/session replacement, and actual stage-1 export migration while the browser retains an uncertain request. Exports/tokens remain in memory and outside repository artifacts.

The product uses human table names and restaurant timezone, visible labels/focus, a coherent local illustration and clear available/selected/refused/uncertain states. Screenshots have no horizontal overflow at 375px. This is not a formal accessibility certification or exhaustive device/browser audit. Verification uses Chromium; arbitrary interleavings cannot be exhaustively tested. Published checks are partial contract evidence, supplemented by source review and independent tests. No persistence across restart is claimed. Test controls are enabled by default for judging; hardened mode is not an internet-production certification. Later-stage policies/history/series are intentionally absent.
