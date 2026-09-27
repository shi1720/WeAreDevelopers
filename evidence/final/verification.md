# Final coordinator acceptance

All four service stages are accepted. Stage4 frozen implementation `53617a341d21ebae3d76761f41b6ea4d38bc2a6c` was independently reviewed; verifier tests/evidence commit `aa816477c6a2a40b528a28c362a7ec67bfc566a1` is the exact repository revision used for final coordinator executions. No service/static files changed between these revisions. Stages1–3 remain byte-identical to their accepted predecessor folders.

Official Stage4 host run passed120+25+7+6=158 checks, exit0,37.174s. All-stage isolated and fresh `git clone --no-local` isolated runs each passed575 required checks in total, with expected next-stage failures for stages1–3. These are executions, not575 distinct requirements. Every suite report/count/log is retained below. Both all-stage commands exited0.

| Run | Required passed | Harness interval | Exit |
|---|---:|---:|---:|
| all-isolated stage-1 | 120 | 29.383s | 0 |
| all-isolated stage-2 | 145 | 36.865s | 0 |
| all-isolated stage-3 | 152 | 40.600s | 0 |
| all-isolated stage-4 | 158 | 46.152s | 0 |
| clean-isolated stage-1 | 120 | 31.078s | 0 |
| clean-isolated stage-2 | 145 | 38.412s | 0 |
| clean-isolated stage-3 | 152 | 44.091s | 0 |
| clean-isolated stage-4 | 158 | 42.443s | 0 |

## Exact commands and controls

Working directory `/tmp/proofline-official-spec`, official revision `803560d2a678ace1414465c098eb0ab5380ffade`. All65 tracked official files compared byte-identical; see harness-integrity.json. Each output directory was new.

```sh
.venv/bin/python -m harness run --track tablekeeper --repo /Users/shivamgupta/Downloads/we-are-developers --stage 4 --out /Users/shivamgupta/.cache/proofline-checks/s4-host-01
.venv/bin/python -m harness run --track tablekeeper --repo /Users/shivamgupta/Downloads/we-are-developers --all --mode isolated --out /Users/shivamgupta/.cache/proofline-checks/final-all-isolated-01
git clone --no-local /Users/shivamgupta/Downloads/we-are-developers /Users/shivamgupta/.cache/proofline-clean-final-20260927
.venv/bin/python -m harness run --track tablekeeper --repo /Users/shivamgupta/.cache/proofline-clean-final-20260927 --all --mode isolated --out /Users/shivamgupta/.cache/proofline-checks/final-clean-isolated-01
.venv/bin/python -m harness check /Users/shivamgupta/Downloads/we-are-developers --track tablekeeper
.venv/bin/python -m harness check /Users/shivamgupta/.cache/proofline-clean-final-20260927 --track tablekeeper
```

Harness commands used env with HTTP_PROXY,HTTPS_PROXY,ALL_PROXY and lowercase equivalents removed; PATH=/tmp/proofline-docker-build-tools:/opt/homebrew/bin:/usr/local/bin:/Users/shivamgupta/.local/bin:/usr/bin:/bin; DOCKER_CONFIG=/tmp/proofline-public-docker-config; DOCKER_HOST=unix:///Users/shivamgupta/.colima/default/docker.sock. Existing build adapter is the previously inspected metadata-fetch workaround; harness source unchanged. Runtime inspection captured service NanoCpus2000000000,Memory2147483648,internal network=true and no proxy keys. Independent reviewer additionally passed69/69 HTTP checks with network=none.

## Submission check and preserved failures

Offline checks in workspace and clean clone exit1 solely because authentic `room.json` is absent. Operator full-session export remains the expected pending submission gate; no room history was fabricated. The first workspace scan also flagged an untracked `.private/exports/interim-room.json` for an env-assignment pattern. Its contents were not printed; it was moved outside the submission to private host storage, and the rerun reported only the missing authentic export. It was not Git-tracked. This scanner finding does not establish that a live credential existed, and no rotation is claimed.

Earlier implementation and test-development failures remain in stage-specific evidence, including Stage3 imported-exception rejection and Stage4 backend availability400 plus preview shape failures. The Python3.14 hour24 parsing difference remains documented; verified Docker/prepared runtime is3.12. No known material defect remains from executed checks. Hidden tests, exhaustive proof, screen-reader/cross-engine certification and internet-production readiness are not claimed. Planner oversized-limit rejection was source-reviewed only. Current amended series summary refresh is an acknowledged UX limitation.

Independent Stage4 evidence: [review](../stage-4/independent/verification.md), [coverage](../../docs/coverage-stage-4.md). Service uses ephemeral state and judge controls enabled by default; see security guidance before any public deployment.

Completion observation: 2026-09-27T17:59:15.571570+00:00; elapsed since production dispatch 6:22:51.571570 (includes idle/recovery). Band catalog estimate and raw room-only token telemetry are in usage-snapshot.json; actual provider bill remains unknown.
