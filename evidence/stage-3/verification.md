# Stage 3 final independent gate

Recommendation **PASS** at frozen implementation `8a12344510a97d7ee20a4326935cacc3ab00798e`; package tree `482f720f3c23f8a6291f90d18ecf6d0c31dd042d`. Coordinator controls acceptance. Service/static/deployment files remained unchanged during review; accepted stages1/2 match `f2e3189db5f113f9b38509cc57241d9e50d91330`. Reviewer changes are tests/evidence/coverage only.

| Independently executed check | Result | Duration |
|---|---|---|
| HTTP suite including original import regression and expanded relations |47/47|11.427s unittest|
| Additional cutoff/counter/first-failing-occurrence tests |3/3|0.908s unittest|
| Actual stage1 export/import, adoption, session and original create/batch receipts |pass|0.372s|
| Actual stage2 export/import, adoption, session and original create/batch receipts |pass|0.387s|
| Browser inherited scenarios |7/7|per-scenario log|
| New manager/history/series product walkthrough |3/3|1.62s process real|
| Implementation tests independently rerun |62/62|13.632s unittest|
| Official host02 suites1/2/3 |120+25+7 all pass|46.57s real|
| Official isolated01 suites1/2/3 |120+25+7 all pass|43.46s real|
| Official isolated02 repeated for runtime inspection |120+25+7 all pass|43.5s wrapper|

All successful commands exited0. The final HTTP source now discovers50 cases:47 executed together plus3 additional separately; no combined50-case run is claimed. Official stage4 overshoot rejected as intended (6 collected,4 passed,1 failed before stop). No required-suite skips/errors. Repeated isolated run was justified because initial containers exited before live inspection completed.

## Failure and repair

Original candidate `835401316b3feb1d845da13478e72b90def427a9` accepted an invalid import clearing a permanent series exception. Rejected review and failing HTTP regression remain in `review-01.md`, `import-failure-01.log` and original commit `d2a871891627efdc5d34dab05bd6853686a49705`. Engineer's original fix commit validates exception flags against changed history after the adoption receipt's recorded revision. Independent verification confirms pre-adoption anchor edits are valid, reverted changes remain exceptions, cancellation preserves flags, and corrupt history/sequence/terms/membership/adoption receipts reject without replacing any state. No reviewer service edits.

The first browser run passed6/7 and failed migration setup: it loaded the new stage3 page against stage1 APIs, so its policy request failed. This is not the retained-old-browser upgrade scenario. Reviewer corrected only the routing setup to serve actual stage2 HTML/assets while stage1 API commits the pending request; then imports into stage3 and retries on the same page. The original exact-body/key/receipt/session assertions remain unchanged. Both logs are retained. Final7/7 passes include stage1 lost-response upgrade without reload.

## Commands

From repository root, disposable frozen image `9112e9906545` at localhost18094, genuine accepted predecessor images at18091/18092:

```sh
TABLEKEEPER_BASE_URL=http://127.0.0.1:18094 /tmp/proofline-official-spec/.venv/bin/python -m unittest discover -s stage-3/tests -p 'independent_*.py' -v
TABLEKEEPER_BASE_URL=http://127.0.0.1:18094 /tmp/proofline-official-spec/.venv/bin/python stage-3/tests/independent_upgrade.py
TABLEKEEPER_BASE_URL=http://127.0.0.1:18094 TABLEKEEPER_STAGE1_URL=http://127.0.0.1:18091 TABLEKEEPER_STAGE2_URL=http://127.0.0.1:18092 TABLEKEEPER_SCREENSHOTS=evidence/stage-3 /tmp/proofline-official-spec/.venv/bin/python stage-3/tests/independent_browser.py
TABLEKEEPER_BASE_URL=http://127.0.0.1:18094 /tmp/proofline-official-spec/.venv/bin/python stage-3/tests/independent_product.py
```

From stage3: `/tmp/proofline-official-spec/.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v`.

From immutable official `/tmp/proofline-official-spec` at `803560d2a678ace1414465c098eb0ab5380ffade`:

```sh
.venv/bin/python -m harness run --track tablekeeper --repo /Users/shivamgupta/Downloads/we-are-developers --stage 3 --out /Users/shivamgupta/.cache/proofline-checks/s3-host-02
.venv/bin/python -m harness run --track tablekeeper --repo /Users/shivamgupta/Downloads/we-are-developers --stage 3 --mode isolated --out /Users/shivamgupta/.cache/proofline-checks/s3-isolated-02
```

Use fresh output directories. Environment matches stage2: PATH begins `/tmp/proofline-docker-build-tools:/opt/homebrew/bin:/usr/local/bin:/Users/shivamgupta/.local/bin:/usr/bin:/bin`; DOCKER_CONFIG=/tmp/proofline-public-docker-config; DOCKER_HOST=unix:///Users/shivamgupta/.colima/default/docker.sock; inherited proxy variables removed. Inspected adapter adds only build args. All65 tracked official mirror files independently compared byte-identical, no harness/test edits.

Actual runtime inspection is in `isolated-runtime.json`: every observed harness network internal=true, service NanoCpus2000000000/Memory2147483648, all runner/service proxy-key lists empty. Official runner itself is not service-resource-constrained. No exported credentials/tokens are written to repository; screenshot references are synthetic disposable bookings.

## Coverage and limits

Full new implementation/source/assets plus inherited unchanged modules reviewed. New tests cover immutable terms, permissions, effective-date ties, selected capacity,50-way CAS, no-op/replay silence, history transitions, recurrence bounds/DST/failure atomicity, permanent exceptions, once-per-operation restaurant/multiple-series counters, accepted-cutoff retention and first-failing-occurrence precedence. Actual predecessor migrations preserve changed current bookings, old receipts and sessions before adoption and native re-export/import.

Manager and recurring screens visually inspected at375px and1440px, no horizontal overflow; labels, visible focus, human table names and timezone are clear. Browser assets remain local. Product tests exercise manager publish replay, guest accepted terms/history/adoption and diner exclusion from manager controls.

No known material violation remains. This is not exhaustive model checking or a formal accessibility/security certification. Browser verification uses Chromium. State is ephemeral as permitted; judge controls default enabled, with documented disabling mode. Opaque import validation is tested through representative structural/relational corruptions, not every possible bit change. Earlier legacy history is a documented imported baseline; nonexistent historical events are not fabricated. No stage4 behavior claimed.
