# Stage 1 independent verification

Reviewer: Proofline Verifier. Implementation candidate: `8a2a07abfe972815cfea7c02176a075b8b2accaf`. Service package tree: `2a5107fedec409dd152484de88ede68b861e008b`. Official kickoff: `803560d2a678ace1414465c098eb0ab5380ffade`. No service or official harness files were edited by the reviewer.

## Measured runs

| Run | Result | Duration |
|---|---|---|
| Initial independent HTTP against container | Exit 0, 20/20 | unittest 5.328 s; subprocess 5.455 s |
| Expanded independent HTTP against container | Exit 0, 23/23, including 22 import-corruption subcases | unittest 6.562 s; subprocess 6.691 s |
| Implementer-authored tests executed independently | Exit 0, 24/24 | unittest 2.199 s; subprocess 2.317 s |
| Two-container transfer probe | Exit 0, all assertions passed | probe 0.324 s |
| Independent HTTP inside network-none container, 2 CPU/2 GiB | Exit 0, 23/23 | unittest 6.080 s; subprocess 6.503 s |
| Official host run, attempt 01 | Exit 0, stage 1 120/120; expected stage 2 rejection | subprocess 40.652 s; stage 1 pytest 23.80 s; stage 2 pytest 15.16 s |
| Official isolated run, attempt 01 | Pending runner build | Not complete |

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

No material implementation violation found. Source review, host conformance and independent adversarial checks passed. Acceptance remains pending the final isolated official run. The service is ephemeral and its judge image intentionally exposes test controls; RUN.md documents these limitations and its explicit control-disable mode. This review is not a production certification or a claim about unshipped judge tests.
