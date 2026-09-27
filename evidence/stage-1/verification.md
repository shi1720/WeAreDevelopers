# Stage 1 independent verification

Reviewer: Proofline Verifier. Implementation candidate: `8a2a07abfe972815cfea7c02176a075b8b2accaf`. Service package tree: `2a5107fedec409dd152484de88ede68b861e008b`. Official kickoff: `803560d2a678ace1414465c098eb0ab5380ffade`. No service or official harness files were edited by the reviewer.

**Final reviewer decision: PASS recommendation.** The required isolated attempt 04 passed all 120 stage-1 checks, with expected next-stage rejection and no skipped/error/deselected tests. Coordinator alone accepts and authorizes the next stage. Earlier failed/interrupted attempts are retained below.

## Measured runs

| Run | Result | Duration |
|---|---|---|
| Initial independent HTTP against container | Exit 0, 20/20 | unittest 5.328 s; subprocess 5.455 s |
| Expanded independent HTTP against container | Exit 0, 23/23, including 22 import-corruption subcases | unittest 6.562 s; subprocess 6.691 s |
| Implementer-authored tests executed independently | Exit 0, 24/24 | unittest 2.199 s; subprocess 2.317 s |
| Two-container transfer probe | Exit 0, all assertions passed | probe 0.324 s |
| Independent HTTP inside network-none container, 2 CPU/2 GiB | Exit 0, 23/23 | unittest 6.080 s; subprocess 6.503 s |
| Official host run, attempt 01 | Exit 0, stage 1 120/120; expected stage 2 rejection | subprocess 40.652 s; stage 1 pytest 23.80 s; stage 2 pytest 15.16 s |
| Official isolated run, attempt 01 | Exit 3; official runner build failed before tests: PyPI connection timeout fetching httpx 0.28.1 | subprocess 370.334 s |
| Official isolated run, attempt 02 | Exit 3 after reviewer interrupted owned build to obtain buffered logs; logs showed download progress, not a confirmed stall | subprocess 85.979 s |
| Official isolated run, attempt 03 | Exit 4; runner built, but bind mount lacked /work/tablekeeper/test and pytest did not execute | subprocess 436.655 s |
| Official isolated run, attempt 04 | Exit 0; stage 1 120/120; expected stage 2 absent-UI rejection | subprocess 46.061 s; stage 1 pytest 26.73 s; stage 2 pytest 14.17 s |
| Explicit test-control-disable mode | Exit 0; health 200, export/reset/import all 404 not_found | in-container probe 0.015 s |

Official host report records root revision `19628383096d045f67c5653b8477afeb22601cf6`: coordinator evidence-only commits followed the frozen candidate. `git diff 8a2a07abfe972815cfea7c02176a075b8b2accaf -- stage-1` was empty before reviewer test additions. The only subsequent stage change is the verifier-owned boundary test file, committed at `5fb91092752dc97fe4df6b17bd0659a0a5c1fe28`. Docker excludes tests. Stage-2 overshoot uses `-x`: 25 collected, zero passed, one expected failure at route `/` waiting for `[data-testid='search-button']`; it did not run all stage-2 cases.

## Reproduction commands

Use these environment settings on the verification host (public Docker configuration contains no registry credentials):

```sh
export PATH=/opt/homebrew/bin:/usr/local/bin:$PATH
export DOCKER_CONFIG=/tmp/proofline-public-docker-config
export DOCKER_HOST=unix:///Users/shivamgupta/.colima/default/docker.sock
```

Independent container was image `proofline-tablekeeper-stage1`, built from the frozen stage-1 source by Engineer. Reviewer also let the official harness build stage-1 independently. Start disposable instances:

```sh
docker run --rm -d --cpus 2 --memory 2g -e PORT=8091 -p 127.0.0.1:18091:8091 --name proofline-verifier-stage1 proofline-tablekeeper-stage1
docker run --rm -d --cpus 2 --memory 2g -e PORT=8092 -p 127.0.0.1:18092:8092 --name proofline-verifier-transfer-stage1 proofline-tablekeeper-stage1
TABLEKEEPER_BASE_URL=http://127.0.0.1:18091 /tmp/proofline-official-spec/.venv/bin/python -m unittest discover -s stage-1/tests -p 'independent_*.py' -v
/tmp/proofline-official-spec/.venv/bin/python evidence/stage-1/transfer_probe.py
```

From `stage-1/`, implementation checks:

```sh
/tmp/proofline-official-spec/.venv/bin/python -m unittest discover -s tests -v
```

From `/tmp/proofline-official-spec`:

```sh
/tmp/proofline-official-spec/.venv/bin/python -m harness run --track tablekeeper --repo /Users/shivamgupta/Downloads/we-are-developers --stage 1 --out /tmp/proofline-verifier-s1-host-01
/tmp/proofline-official-spec/.venv/bin/python -m harness run --track tablekeeper --repo /Users/shivamgupta/Downloads/we-are-developers --stage 1 --mode isolated --out /tmp/proofline-verifier-s1-isolated-01
```

Each output directory was new. Choose new names on rerun. Command durations were measured with `time.monotonic()` around `subprocess.run`; unittest/pytest durations are their separately reported values. Raw exports and bearer tokens remained in process memory. Published log copies are checked for credential-bearing data; source synthetic fixture passwords in official failure traces are not user credentials.

Additional independent offline run:

```sh
docker run --rm -d --network none --cpus 2 --memory 2g -e PORT=8093 --name proofline-verifier-offline-stage1 proofline-tablekeeper-stage1
docker cp stage-1/tests proofline-verifier-offline-stage1:/tmp/independent-tests
docker exec -e TABLEKEEPER_BASE_URL=http://127.0.0.1:8093 proofline-verifier-offline-stage1 python -m unittest discover -s /tmp/independent-tests -p 'independent_*.py' -v
```

Runner-build diagnosis: a separate default-network `python:3.12-slim` container could not connect to `https://pypi.org/simple/pytest/` using `urllib.request.urlopen(..., timeout=8)`; exit 1, `URLError` caused by connection timeout. Exact elapsed time of that diagnostic was not captured. This was reported to the coordinator for VM infrastructure recovery. It is distinct from the passing network-none service checks and is not a service defect.

## Current outcome

No material implementation violation found. Source review, host conformance, independent adversarial checks and the final isolated gate passed. Frozen source remains `8a2a07abfe972815cfea7c02176a075b8b2accaf`; final harness report root revision is `dbffe820bdd65fce156e82a1c7b39b2eed96eaee`, which includes evidence/test additions but no service changes. Package tree equality and the empty diff for service, Dockerfile, RUN.md and .dockerignore were rechecked after the run. Independent additions are test-only; Docker excludes tests.

The service is ephemeral and its judge image intentionally exposes test controls; RUN.md documents these limitations and its explicit control-disable mode. An independent container started with `--network none -e PORT=8094 -e TABLEKEEPER_TEST_CONTROLS=0` returned health 200 and 404 `not_found` for all three test routes. All verifier-created service containers were stopped. This review is not a production certification or a claim about unshipped judge tests.

Recovery follow-up: coordinator built the unchanged official runner with build-only proxy arguments and stopped the temporary proxy. Attempt 02 explicitly removed inherited proxy variables and used the public proxy-free Docker config. The normal legacy Docker builder did not reuse its dependency RUN layer. The reviewer interrupted that owned build after 85.979 s to retrieve buffered output after `docker logs` was unsupported by the build container's logging driver. The captured output showed successful metadata downloads and an in-progress 47.9 MB Playwright wheel download. That interruption was premature; it is preserved as a reviewer process-control error, **not** a service defect or proven network failure.

Attempt 03 was allowed to finish. Its unchanged runner dependency command exited 0 and the image built. The subsequent isolated pytest process failed before collecting checks: `ERROR: Directory '/work/tablekeeper/test' not found. Check your '--rootdir' option.` The official command bound host `/private/tmp/proofline-official-spec:/work:ro` and `/private/tmp/proofline-verifier-s1-isolated-03:/out`. Colima could not see those host temporary paths. Harness exit 4 after 436.655 s; full log/report preserved.

## Successful isolated recovery and runtime verification

Coordinator created an exact git archive under shared `/Users/shivamgupta/.cache/proofline-official-803560d2`, then bind-mounted it read-only within Colima at the unchanged `/private/tmp/proofline-official-spec` path. Reviewer compared SHA256 for **all 65 tracked official files** against the original checkout: zero mismatches. Original checkout `git status --short` was empty at official revision `803560d2a678ace1414465c098eb0ab5380ffade`.

The inspected temporary `/tmp/proofline-docker-build-tools/docker` adapter adds four HTTP(S)_PROXY build arguments only when its first argument is `build`, then delegates to `/opt/homebrew/bin/docker`. Every non-build command is delegated unchanged. This addresses the legacy builder cache signature; it does not change official files or runtime settings. The public Docker config contains no runtime proxy configuration, and inherited HTTP/HTTPS/ALL/NO_PROXY variables were removed from the harness environment.

Final command, run from original `/tmp/proofline-official-spec` with a new shared output directory:

```sh
PATH=/tmp/proofline-docker-build-tools:/opt/homebrew/bin:/usr/local/bin:/Users/shivamgupta/.local/bin:/usr/bin:/bin \
DOCKER_CONFIG=/tmp/proofline-public-docker-config \
DOCKER_HOST=unix:///Users/shivamgupta/.colima/default/docker.sock \
/tmp/proofline-official-spec/.venv/bin/python -m harness run --track tablekeeper \
  --repo /Users/shivamgupta/Downloads/we-are-developers --stage 1 --mode isolated \
  --out /Users/shivamgupta/.cache/proofline-checks/s1-isolated-04
```

While tests ran, Docker inspection confirmed both runner and service joined only network `df-run-dcefa0f494d84c83884a74e199ddcb17`, whose `Internal` value was true. Both had zero proxy environment keys. Service limits were `NanoCpus=2000000000` and `Memory=2147483648`. The runner is not resource-limited by the official harness; the service is. Machine-readable inspection is preserved in `isolated-04-runtime.json`. Final output: highest contiguous stage 1, claimed stage 1, stage-1 120/120 passed, stage-2 expected absent browser screen failure after one check (`-x`). Pytest emitted cache-write warnings because the official checkout was correctly mounted read-only; they did not skip or fail checks. No claim is made about unshipped judge checks or future stages.
