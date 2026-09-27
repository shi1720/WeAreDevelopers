# Proofline

Proofline turns a written contract into independently checked releases through four persistent Band coding-agent seats. This run builds Tablekeeper: keep the promise, even when the floor changes.

Shivam Gupta supplied product direction, factory configuration and the single production dispatch. The agent seats authored implementation, tests and acceptance evidence. The operator finalized this report and submission materials after the run. No customer, revenue, certification or manual human implementation claims are made.

## Reproduce the factory

Create four distinct Band Desktop agent identities named Proofline Coordinator, Proofline Engineer, Proofline Experience and Proofline Verifier. Configure each with the corresponding file in `mandates/`, the Codex harness and model `gpt-6-astra`. All eight original and replacement provider-session epochs report model `gpt-6-astra` and reasoning effort `low`. This is runtime-reported metadata, not an independent serving-model attestation. The mandates describe reusable responsibilities rather than product endpoints.

Give every seat the same absolute clean result-repository path and filesystem, shell, Docker and browser access. Install Python 3.12 for the official harness, Git, a running Docker daemon and Playwright Chromium. Keep provider credentials outside the repository. Start a fresh Band room, add all four configured identities, verify membership and reciprocal addressed delivery, then send one complete production dispatch. `factory/run.json` records the exact identities and official contract revision for this run; `factory/tasks/dispatch.md` records the operator task.

Use the coordinator to distribute full contracts in numbered addressed messages. A path or room message ID alone is insufficient. Assign separate actual implementation files to Engineer and Experience; Verifier independently derives checks from the full specification. Confirm module interfaces before editing. Shared work cards track assignment; each runtime maintains its own private execution tasks.

The coordinator owns planning, release gates and factory documentation. Engineer owns domain writes, atomic state and deployment. Experience owns temporal/availability implementation initially, then the browser product and demonstration. Verifier owns independent tests and acceptance evidence. Seats commit only their owned files with per-command author identities. Original commits and failed checks remain in history; no amend, rebase or squash is used.

## Release gates

Each stage begins as a complete copy of its accepted predecessor, with the first built from no source. Future capabilities never move backward. Before acceptance, stop editing the candidate folder and identify a full committed revision. Verifier reviews source, executes independent boundary/adversarial checks and official inherited suites, confirms the expected next-stage overshoot failure, then checks isolated operation with no outbound network, two CPUs and two GiB. A failing requirement returns to its author with reproducible evidence; verification runs again against the repaired committed revision.

Final validation includes every stage in isolated mode and an independent clean clone. All harness output directories are new. Raw state exports can contain password hashes and bearer tokens and remain private outside Git. Only reviewed public-safe evidence enters `evidence/`. The operator exported authentic full `room.json` at 2026-09-27T18:01:32.735Z after the run: 3,540 messages, SHA-256 `5608a22b314bb25ddb46b8e1004581a3480c04f46bd3219f28483cf40eb22fbb`. Its only human text message is the original dispatch. Historical check logs that report a missing export predate this download; they remain unchanged. Final post-export packaging validation is separate.

## Design choices and tradeoffs

Separating implementation from acceptance makes the review accountable to a different seat. Explicit ownership avoids shared-file overwrites. Sequential freeze-and-copy preserves the development chain and limits regressions. Full handoffs cost context but make requirements available to every participant without depending on ambient room visibility. Spec-derived tests supplement the partial official suites; a green published suite alone is insufficient evidence of complete correctness.

## Measurement and status

The production dispatch timestamp is 2026-09-27T11:36:12.525834Z; the final report timestamp is 2026-09-27T18:00:17.507353Z, an elapsed **6 hours, 24 minutes, 4.981519 seconds**, including idle and recovery time. This is wall time, not continuous compute time. The post-acceptance runtime snapshot at 18:02:01.565269 UTC totals **119,443,159 tokens** across eight identified provider-session epochs. Cached input of 116,797,184 is already included; output is 335,630. Provider-billed spend remains unknown. [Sanitized accounting and method](evidence/final/runtime-usage-method.md) explain lineage, exclusions and cutoff.

Stage 1 is accepted at implementation `8a2a07abfe972815cfea7c02176a075b8b2accaf`, independent evidence `3813508b5624b4ae89a346b68611a595f83cfde5`. Official host and isolated 120/120; independent HTTP/offline 23/23; independently rerun implementation tests 24/24. Stage 2 is accepted at implementation `e4fc1c5bf52769927b50e139be1d380b1c044aeb`, evidence `f2e3189db5f113f9b38509cc57241d9e50d91330`: official host/isolated 120+25, independent HTTP 30 plus 2 review cases, browser 7 and author tests 41 passed. Stages3 and4 subsequently completed independent review; see the final evidence below. Infrastructure rehearsal is a separate room and is not product-build evidence.

## Observed recovery

Independent stage-3 review caught a material portable-state bug after published checks passed: an edited export could erase a permanent diner exception. Verifier committed the failing HTTP regression against `835401316b3feb1d845da13478e72b90def427a9`; Engineer fixed adoption-revision/history validation in original commit `8a12344510a97d7ee20a4326935cacc3ab00798e`. Valid pre-adoption anchor edits remain nonexceptions, while reverted post-adoption edits remain exceptions. Independent revalidation passed, including final host/isolated 152 checks. Complete accepted evidence is `0e302c79de3521fc0993cb6ed0b6f21a52d493e4`; Stage4 followed as a copy-forward. This is an observed rejection-and-repair cycle, not a manufactured disagreement.

The initial two container builds timed out fetching Python image metadata through Colima, while host HTTPS reached the registry. A mirror pull from Colima also timed out. Coordinator downloaded the official image through the host using `crane`, loaded it into Docker, and returned the build to Engineer/Verifier without changing service or harness code. A temporary public-only Docker configuration avoided a missing credential helper without changing the user's configuration. [Recovery evidence](evidence/factory/registry-recovery.md) preserves the failed attempts and successful commands. Passing local tests were explicitly kept separate from pending container acceptance.

## Final Stage 4 review and measurement

Frozen service candidate `53617a341d21ebae3d76761f41b6ea4d38bc2a6c` passed independent review recorded in `aa816477c6a2a40b528a28c362a7ec67bfc566a1`: 69 independent HTTP checks both host and isolated, genuine stages1–3 migrations, inherited and new browser flows, and 24 generated exhaustive optimizer cases. Coordinator official host passed158/158; all four folders passed isolated inherited suites with expected next-stage rejections. Final clean-clone results and acceptance are recorded in [final evidence](evidence/final/verification.md).

The Stage4 backend-only candidate failed closure availability because server and availability signatures differed. Independent review preserved the failure; the Experience integration commit fixed it, and the committed candidate passed independent reruns. Browser contract-shape failures and corrected test assumptions are preserved separately. No service changes were made during final review.

The older four-session BAND catalog snapshot remains as historical evidence, but it omits the verified eight-epoch lineage and has unvalidated cache/pricing semantics. Its approximately $131.32 is not used as final cost. The sanitized accounting supersedes its token total without rewriting the historical snapshot.

## Operator-assisted runtime recovery

At 17:33:15 UTC, the operator found the BAND daemon unreachable. The exact stop time and cause are unknown. The operator restarted the bundled daemon and the same four seats in the same room. All four later acquired new provider sessions. No new task, implementation hints, approvals or stage-source changes were supplied by the operator. This was **operator-assisted runtime recovery**, not an uninterrupted autonomous run. The narrower claim is one human production dispatch and no implementation steering. We leave the scoring interpretation to the judges.

## Deployment and scope

The frozen graded service has ephemeral in-memory state and judge controls enabled by default. It is not suitable for direct public exposure. A separately commissioned operational companion and Firebase deployment remain pending, and will have separate provenance. They do not retroactively change the original four-stage result. The optimizer remains bounded to six tables, four declared pairs and six considered bookings, including every confirmed booking overlapping the closure interval. No arbitrary partition workaround or unlimited venue scale is claimed.

Python3.12 is the verified/deployed runtime. Python3.14 accepts an hour24 input that3.12 rejects; this is a documented portability limitation. Finite generated cases do not prove every optimizer input; oversized-limit rejection was source-reviewed only. Chromium desktop/mobile checks do not constitute a screen-reader or cross-engine audit.

## Portable reproduction appendix

Commands below describe a new run, not mutations to the completed submission. Checked against BAND 0.4.12 CLI help and Codex CLI 0.158.0-alpha.2.1. Recheck help if versions differ.

## What is reusable, and what records one run

`factory/mandates/proofline-*.md` archives the standing instructions used by the original seats. They describe generic ownership, complete handoffs, independent review and evidence. The submission's `mandates/` files must match the actual seat names and actual runtime/model configuration.

`factory/tasks/dispatch.md` is the **original task archive**, not a portable mandate. It intentionally contains Tablekeeper requirements, original absolute paths, original seat IDs and handles, a machine-specific PATH/Docker socket, and run-specific infrastructure statements. Preserve that archive in the original submission. Make a separate adapted task for a new run; check every path, identity and claim before dispatch. For a different product, replace the task and contracts, not the reusable mandate logic.

The factory's desired model is `gpt-6-astra`. The host configuration specifies that model and reasoning effort `low`; production-session Codex `turn_context` records also report `gpt-6-astra` and `low` for all four seats. This is attributable **runtime-reported metadata**, not independent provider serving-model attestation. BAND's own nullable/inherited settings and configuration generation 0 do not contradict the more specific session records. The reproduction commands explicitly set `--runtime-effort low`, a flag supported by the inspected BAND 0.4.12 create/attach help. Availability depends on the reproducer's account. If a different model is chosen, change the new mandates' Model lines before starting and disclose the change.

## 1. Prerequisites and pinned inputs

Install BAND Desktop from [official documentation](https://docs.band.ai/band-desktop), complete sign-in/CLI setup, and keep the app/daemon available. Use Python 3.12, Git, Docker with a running daemon, a working Codex CLI and model-provider access. The host must reach BAND and the model provider during generation. The no-outbound rule applies to the **service being tested**, not to the coding seats.

Run the following in one shell, editing the source path. `PROOFLINE_SOURCE` is an existing checkout of the published Proofline repository; `PROOFLINE_ROOT` must be a new workspace, not the submitted result checkout. Put **the specification checkout, result and check outputs under paths shared with the Docker daemon**. A directory under the user's home is a practical starting point on desktop Docker/Colima, but must still pass the bind-mount probe below. Do not use `/tmp` or `/private/tmp` merely because the host can read them. For a remote daemon, its bind sources refer to the daemon host; use a correctly shared/remote workspace rather than assuming local paths are visible.

```sh
export PROOFLINE_SOURCE='/absolute/path/to/proofline-submission'
export PROOFLINE_ROOT="$HOME/proofline-new-run"
export PROOFLINE_SPEC="$PROOFLINE_ROOT/official"
export PROOFLINE_RESULT="$PROOFLINE_ROOT/result"
export PROOFLINE_CHECKS="$PROOFLINE_ROOT/checks"
export PROOFLINE_CODEX="$(command -v codex)"
test -x "$PROOFLINE_CODEX"
test ! -e "$PROOFLINE_ROOT"
mkdir -p "$PROOFLINE_ROOT" "$PROOFLINE_CHECKS"
git clone https://github.com/band-ai/dark-factory-wearedevs.git "$PROOFLINE_SPEC"
git -C "$PROOFLINE_SPEC" checkout --detach 803560d2a678ace1414465c098eb0ab5380ffade
test "$(git -C "$PROOFLINE_SPEC" rev-parse HEAD)" = 803560d2a678ace1414465c098eb0ab5380ffade
python3.12 --version
python3.12 -m venv "$PROOFLINE_SPEC/.venv"
"$PROOFLINE_SPEC/.venv/bin/python" -m pip install -r "$PROOFLINE_SPEC/harness/requirements.txt"
"$PROOFLINE_SPEC/.venv/bin/python" -m playwright install chromium
docker info
mkdir -p "$PROOFLINE_RESULT/mandates" "$PROOFLINE_RESULT/factory/tasks"
cp "$PROOFLINE_SOURCE"/factory/mandates/proofline-*.md "$PROOFLINE_RESULT/mandates/"
git -C "$PROOFLINE_RESULT" init -b main
```

Check the Python version output before creating the virtual environment. On Linux, Playwright may additionally require `python -m playwright install --with-deps chromium` inside that virtual environment. Do not copy any `stage-*` source, prior room export or prior evidence into the new result. The service starts from no implementation.

The original explicit executable was `/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex`. It is not portable. The `PROOFLINE_CODEX` variable above resolves the executable installed on the new host and passes its absolute path explicitly to BAND.

Authenticate before an unattended run:

```sh
band --version
band preflight
"$PROOFLINE_CODEX" --version
"$PROOFLINE_CODEX" login status
```

If BAND is not signed in, run `band init` and finish its browser flow. If Codex is not authenticated, run `"$PROOFLINE_CODEX" login` and finish its sign-in flow, then recheck status. BAND and Codex have separate authentication. `--runtime-auth inherit` below uses the runtime's available host authentication; it is not an API key and does not prove a particular billing plan. Keep credentials outside the result repository. [Official Codex authentication documentation](https://learn.chatgpt.com/docs/auth) explains supported sign-in modes.

## 1a. Prove Docker infrastructure works before dispatch

The original run exposed two independent infrastructure faults. Colima could not fetch the official Python image and runner dependencies directly, despite host HTTPS connectivity. After host-assisted image loading and a build-only proxy recovery, the runner built successfully. An isolated attempt then failed with `Directory '/work/tablekeeper/test' not found` because the `/private/tmp/...` bind-mounted specification was absent inside the container. Host-mode success did not establish Docker bind visibility. See `evidence/factory/registry-recovery.md`, `evidence/stage-1/isolated-01-console.log` and `evidence/stage-1/isolated-03-stage-1.log` for preserved observations.

Complete this infrastructure preflight before creating the final room or dispatching work. The commands below prepare a **new** environment; they are not evidence that any Tablekeeper stage passes.

```sh
# Uses the selected daemon/context and its normal network path.
docker pull python:3.12-slim
docker image inspect python:3.12-slim --format '{{.Id}} {{.Os}}/{{.Architecture}}'

# Build the exact official runner, with dependencies and Chromium, unchanged.
docker build -t df-harness-runner \
  -f "$PROOFLINE_SPEC/harness/Dockerfile" "$PROOFLINE_SPEC/harness"

# Exercise its browser and imports without an outbound network.
docker run --rm --network none df-harness-runner python -c \
  'import httpx, pytest; from playwright.sync_api import sync_playwright; p=sync_playwright().start(); b=p.chromium.launch(); print("runner imports and Chromium launch OK", b.version); b.close(); p.stop()'
```

The image pull and runner build deliberately have network access. A connectivity error during `pip install` is not evidence that the pinned package is unavailable. Fix network, proxy, credential-helper or daemon configuration before continuing; preserve the original failure. No alternative package versions or patched official Dockerfiles are justified by a timeout.

Create a small local marker in the new check directory, then inspect the actual Docker-visible contents through **read-only mounts**. `--mount` is intentional: unlike an accidentally missing source passed to `-v`, a missing daemon-side bind source should fail explicitly.

```sh
python3 - <<'PY'
import os, pathlib
root = pathlib.Path(os.environ['PROOFLINE_ROOT']).resolve()
assert root.is_absolute()
marker = pathlib.Path(os.environ['PROOFLINE_CHECKS']) / 'bind-preflight.txt'
marker.write_text('proofline Docker-visible checks\n')
PY

docker run --rm --network none \
  --mount "type=bind,source=$PROOFLINE_SPEC,target=/work,readonly" \
  --mount "type=bind,source=$PROOFLINE_RESULT,target=/result,readonly" \
  --mount "type=bind,source=$PROOFLINE_CHECKS,target=/out,readonly" \
  df-harness-runner python -c \
  'from pathlib import Path; assert Path("/work/tablekeeper/test/stage_1/test_sample.py").is_file(); assert Path("/work/tablekeeper/spec/stage-4.md").is_file(); assert Path("/result/mandates/proofline-coordinator.md").is_file(); assert Path("/out/bind-preflight.txt").read_text() == "proofline Docker-visible checks\n"; print("spec, result and checks bind visibility OK")'
```

This smoke probe reads the container mounts and does not edit the spec, result or output files from inside Docker. It proves source visibility, not that a writable harness output mount has the correct permissions. If the host uses differing container-user ownership, validate that output-write policy separately before the scored run. Rerun the probe after changing a context, VM, share configuration or any of these paths.

On the affected original Colima installation, recovery used a host-fetched **official** image, then a temporary host proxy for build-time traffic. A task-local Docker wrapper inserted proxy build arguments for `docker build` only and forwarded all other commands unchanged. It was necessary because a normal legacy build invocation did not reuse the recovered proxy-build cache. Do not copy its original private temporary path or host address: those are machine-specific and may no longer exist. For a reproduction, either repair direct daemon egress or document and rehearse an equivalent build-only proxy with the exact ordinary build invocation the harness will issue. Settle this before dispatch.

If an approved local build proxy is needed, this is the standard explicit build form; set the URL to an address actually reachable **from the Docker build environment**, without embedded credentials:

```sh
export PROOFLINE_BUILD_PROXY='http://docker-reachable-host:port'
docker build \
  --build-arg "HTTP_PROXY=$PROOFLINE_BUILD_PROXY" \
  --build-arg "HTTPS_PROXY=$PROOFLINE_BUILD_PROXY" \
  --build-arg "http_proxy=$PROOFLINE_BUILD_PROXY" \
  --build-arg "https_proxy=$PROOFLINE_BUILD_PROXY" \
  -t df-harness-runner \
  -f "$PROOFLINE_SPEC/harness/Dockerfile" "$PROOFLINE_SPEC/harness"
```

This optional command does not configure the later harness builds automatically. If a wrapper is required, inspect it and verify it changes only build arguments; the Verifier must know its exact path before dispatch. Do not introduce `--network host`, proxy environment variables or host routing into **service/runner runtime commands**. Inspect the resulting runner and service image runtime environment for proxy variables and verify the harness-created network is internal. A prebuilt image or warm cache alone does not prove a later clean build will work.

Environment preparation is complete only when official image acquisition, ordinary official-runner build, browser launch and bind visibility all succeed under the selected daemon/context. Service correctness, resource caps, no-outbound behavior and stage acceptance still require the official isolated suite after implementation. Keep infrastructure failures separate from product-check counts.

## 2. Create four seats with explicit host-runtime settings

These are mutations for a **new reproduction only**. Do not execute them against the already-dispatched production room. Use a fresh account/namespace if these display names already exist. If the CLI rejects an existing name, inspect the existing identity instead of creating ambiguous duplicates; new IDs must go in the new run record.

```sh
for role in coordinator engineer experience verifier; do
  case "$role" in
    coordinator) display='Proofline Coordinator' ;;
    engineer) display='Proofline Engineer' ;;
    experience) display='Proofline Experience' ;;
    verifier) display='Proofline Verifier' ;;
  esac
  band --session "proofline-new-$role" agent create \
    --name "$display" \
    --cwd "$PROOFLINE_RESULT" \
    --transport codex-app-server \
    --spawn-command "$PROOFLINE_CODEX" \
    --runtime-auth inherit \
    --runtime-model gpt-6-astra \
    --runtime-effort low \
    --runtime-approval never \
    --runtime-sandbox danger-full-access \
    --no-spawn-sandbox \
    --codex-channel stdio \
    --instructions-file "$PROOFLINE_RESULT/mandates/proofline-$role.md" \
    --json
done
```

`--instructions-file` is **live-linked**, as documented by BAND's help. Do not edit the linked mandates during a scored run. Capture the resulting nonsecret names, handles and identity IDs. Inspect credentials only through supported login/status tools; do not print stores or environment dumps. If the app daemon cannot see Docker or the runtime, fix that setup before dispatch. Do not copy the original macOS PATH or Colima socket onto a different host.

Record the actual returned handles/IDs in variables below. The values shown are placeholders, not the original account's identities:

```sh
export PROOFLINE_COORD_HANDLE='your-owner/returned-coordinator-handle'
export PROOFLINE_ENGINEER_HANDLE='your-owner/returned-engineer-handle'
export PROOFLINE_EXPERIENCE_HANDLE='your-owner/returned-experience-handle'
export PROOFLINE_VERIFIER_HANDLE='your-owner/returned-verifier-handle'
export PROOFLINE_COORD_ID='returned-coordinator-identity-uuid'
export PROOFLINE_ENGINEER_ID='returned-engineer-identity-uuid'
export PROOFLINE_EXPERIENCE_ID='returned-experience-identity-uuid'
export PROOFLINE_VERIFIER_ID='returned-verifier-identity-uuid'
```

Rehearse readiness and reciprocal addressed delivery in a separate practice room before the final run, as the official guide recommends. Do not use rehearsal messages as product-build evidence.

## 3. Create a fresh room and attach all four owned runtimes

```sh
band --as "$PROOFLINE_COORD_HANDLE" chat new \
  --with "$PROOFLINE_ENGINEER_HANDLE" \
  --with "$PROOFLINE_EXPERIENCE_HANDLE" \
  --with "$PROOFLINE_VERIFIER_HANDLE"
```

Copy the returned room UUID exactly; do not infer one from its title:

```sh
export PROOFLINE_ROOM='returned-new-room-uuid'
band --as "$PROOFLINE_COORD_HANDLE" chat participants "$PROOFLINE_ROOM" --json
```

If a seat is missing, add it with `band --as "$PROOFLINE_COORD_HANDLE" chat add "$PROOFLINE_ROOM" "$PROOFLINE_ENGINEER_HANDLE"` (substitute the missing handle), then inspect membership again. A command error alone is not proof that a mutation failed: the original BAND 0.4.12 setup sometimes reported a decoding error after successful membership addition.

Bind the new room explicitly. If the desktop automatically activated a room session, inspect `band --as <handle> sessions --json` first and use the existing exact host-session ID instead of spawning a duplicate. The following loop is for seats that still need their new owned session attached:

```sh
for handle in "$PROOFLINE_COORD_HANDLE" "$PROOFLINE_ENGINEER_HANDLE" \
              "$PROOFLINE_EXPERIENCE_HANDLE" "$PROOFLINE_VERIFIER_HANDLE"; do
  band --as "$handle" attach \
    --room "$PROOFLINE_ROOM" \
    --host-session "proofline-$PROOFLINE_ROOM" \
    --runtime owned \
    --transport codex-app-server \
    --spawn-command "$PROOFLINE_CODEX" \
    --spawn-cwd "$PROOFLINE_RESULT" \
    --runtime-auth inherit \
    --runtime-model gpt-6-astra \
    --runtime-effort low \
    --runtime-approval never \
    --runtime-sandbox danger-full-access \
    --no-spawn-sandbox \
    --codex-channel stdio \
    --json
done
```

Check the actual room sessions before dispatch:

```sh
band --as "$PROOFLINE_COORD_HANDLE" sessions --json
band --as "$PROOFLINE_COORD_HANDLE" runtime policy --host-session "proofline-$PROOFLINE_ROOM"
band --as "$PROOFLINE_COORD_HANDLE" runtime settings --host-session "proofline-$PROOFLINE_ROOM"
band --as "$PROOFLINE_COORD_HANDLE" chat participants "$PROOFLINE_ROOM" --json
```

Repeat the settings/policy checks for the other three handles. A nullable setting can mean inherited configuration; distinguish those values from the actual session's `turn_context` model/effort metadata. Neither is an independent provider attestation. Confirm each seat can access the same result path, specification checkout and Docker daemon during rehearsal.

## 4. Adapt the task archive before sending it once

Create a new copy, retaining the original:

```sh
cp "$PROOFLINE_SOURCE/factory/tasks/dispatch.md" "$PROOFLINE_RESULT/factory/tasks/dispatch.md"
```

Before dispatch, edit **only this new copy** to replace:

- Original result path with `PROOFLINE_RESULT`; original `/tmp/proofline-official-spec` with `PROOFLINE_SPEC`; harness interpreter with its new virtual-environment path.
- All original handles and UUIDs with the four returned identities above, and the original team attribution with the actual reproducer.
- Original PATH and Colima socket instructions with the actual host environment, or remove them if unnecessary.
- Statements claiming installed tools, pre-existing room membership or readiness with facts checked on the new host.
- Any output-directory conventions so logs go to new directories and raw state exports stay private.

Keep the complete product brief, exact pinned contract reference, full inherited-spec handoff rule, stage sequencing, original-commit rule, independent checks and autonomy constraints. Add a new `factory/run.json` with this room, these seats, the same official commit and the actual desired runtime settings. The archived `dispatch.md` is readable source, not an executable command; never evaluate its contents as shell code.

The guide permits the initial lead dispatch to reference the local complete specs. Every **delegated** handoff still needs their complete contents. Send the reviewed task as the human using Python argument passing because `band room send` has no `--body-file` option in this version:

```sh
python3 - <<'PY'
import os, pathlib, subprocess
task = pathlib.Path(os.environ['PROOFLINE_RESULT']) / 'factory/tasks/dispatch.md'
body = task.read_text()
if not body.strip():
    raise SystemExit('Refusing an empty dispatch')
subprocess.run([
    'band', 'room', 'send', os.environ['PROOFLINE_ROOM'], body,
    '--mention', os.environ['PROOFLINE_COORD_ID'],
], check=True)
PY
```

The task is passed as one literal argument; dollar signs/backticks in it are not evaluated. Record the acknowledged message ID and time. If the send result is ambiguous, inspect the room before retrying: dispatching the same scored stage again would be a rerun. After dispatch, do not supply hints, approvals, “continue” messages or fixes. The seats must discover and repair their own failures or record a blocker.

## 5. Official checks and final export

During the autonomous run, these are commands for the Verifier to execute independently. The operator may also perform final read-only validation after the Coordinator's final outcome, without rewriting stage source or representing a new run as the original one.

```sh
cd "$PROOFLINE_SPEC"
"$PROOFLINE_SPEC/.venv/bin/python" -m harness run \
  --track tablekeeper --repo "$PROOFLINE_RESULT" --stage 1 \
  --mode isolated --out "$PROOFLINE_CHECKS/stage-1-final-01"
"$PROOFLINE_SPEC/.venv/bin/python" -m harness run \
  --track tablekeeper --repo "$PROOFLINE_RESULT" --all \
  --mode isolated --out "$PROOFLINE_CHECKS/all-final-01"
"$PROOFLINE_SPEC/.venv/bin/python" -m harness check "$PROOFLINE_RESULT" --track tablekeeper
```

Use the corresponding `--stage 2`, `3` and `4` only as those stages are produced; preserve every output directory and choose a new suffix for each check. Each stage runs earlier suites and the applicable next-stage overshoot probe. A passing full next-stage probe invalidates the earlier-stage claim; do not “repair” that by copying final code backwards. Official public tests are partial. The final result is not a guarantee of hidden-suite success.

At completion, open the real room in BAND Desktop, choose **Open in Band**, then the console room menu **Download → Download full session**. Save it as root `room.json`; do not fabricate a CLI export or use the filtered download. Review it for private credentials; follow the official guide's rotation/redaction exception if needed. Complete README/FACTORY and presentation artifacts, run the offline check again, preserve seat history, and push the actual repository.

Validate a fresh clone after all required files are committed:

```sh
git clone --no-local "$PROOFLINE_RESULT" "$PROOFLINE_ROOT/fresh-clone"
cd "$PROOFLINE_SPEC"
"$PROOFLINE_SPEC/.venv/bin/python" -m harness check "$PROOFLINE_ROOT/fresh-clone" --track tablekeeper
"$PROOFLINE_SPEC/.venv/bin/python" -m harness run \
  --track tablekeeper --repo "$PROOFLINE_ROOT/fresh-clone" --all \
  --mode isolated --out "$PROOFLINE_CHECKS/fresh-clone-final-01"
```

Also clone the pushed public GitHub URL in a separate clean location to confirm judge access, and follow each RUN.md manually. A local clone checks tracked content but does not prove public access.

## Runtime scope and measurement limits

The original operator selected host-native coding runtimes, `approval=never`, `sandbox=danger-full-access`, and inherited authentication. This is a permissive local execution configuration: seats can run shell commands with the host user's authority and access files/services available to that account. The working directory is an organizational boundary, not a security sandbox. No Docker Sandbox microVM isolation is claimed. The official harness's isolated containers protect the **tested-service network boundary**; they do not retroactively sandbox the coding agents.

This configuration was chosen for the explicitly authorized unattended local build. A reproducer wanting a different trust boundary should configure and rehearse a disposable environment before dispatch, and document that as a different runtime configuration. Do not silently retrofit sandbox claims onto this run.


For usage accounting, identify every provider-session epoch, including replacements, and follow the [published measurement method](evidence/final/runtime-usage-method.md). Never publish raw provider rollouts.
