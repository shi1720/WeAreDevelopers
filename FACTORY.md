# Proofline

Proofline turns a written contract into independently checked releases through four persistent Band coding-agent seats. This run builds Tablekeeper: keep the promise, even when the floor changes.

Shivam Gupta supplied product direction, factory configuration and the single production dispatch. The agent seats author implementation, tests and this report. No customer, revenue, certification or manual human implementation claims are made.

## Reproduce the factory

Create four distinct Band Desktop agent identities named Proofline Coordinator, Proofline Engineer, Proofline Experience and Proofline Verifier. Configure each with the corresponding file in `mandates/`, the Codex harness and model `gpt-6-astra`. These are the configured model identifiers; the runtime does not independently expose a serving-model attestation. The mandates describe reusable responsibilities rather than product endpoints.

Give every seat the same absolute clean result-repository path and filesystem, shell, Docker and browser access. Install Python 3.12 for the official harness, Git, a running Docker daemon and Playwright Chromium. Keep provider credentials outside the repository. Start a fresh Band room, add all four configured identities, verify membership and reciprocal addressed delivery, then send one complete production dispatch. `factory/run.json` records the exact identities and official contract revision for this run; `factory/tasks/dispatch.md` records the operator task.

Use the coordinator to distribute full contracts in numbered addressed messages. A path or room message ID alone is insufficient. Assign separate actual implementation files to Engineer and Experience; Verifier independently derives checks from the full specification. Confirm module interfaces before editing. Shared work cards track assignment; each runtime maintains its own private execution tasks.

The coordinator owns planning, release gates and factory documentation. Engineer owns domain writes, atomic state and deployment. Experience owns temporal/availability implementation initially, then the browser product and demonstration. Verifier owns independent tests and acceptance evidence. Seats commit only their owned files with per-command author identities. Original commits and failed checks remain in history; no amend, rebase or squash is used.

## Release gates

Each stage begins as a complete copy of its accepted predecessor, with the first built from no source. Future capabilities never move backward. Before acceptance, stop editing the candidate folder and identify a full committed revision. Verifier reviews source, executes independent boundary/adversarial checks and official inherited suites, confirms the expected next-stage overshoot failure, then checks isolated operation with no outbound network, two CPUs and two GiB. A failing requirement returns to its author with reproducible evidence; verification runs again against the repaired committed revision.

Final validation includes every stage in isolated mode and an independent clean clone. All harness output directories are new. Raw state exports can contain password hashes and bearer tokens and remain private outside Git. Only reviewed public-safe evidence enters `evidence/`. Authentic `room.json` is exported by the operator after the run; its absence is a pending submission gate, never replaced with fabricated messages.

## Design choices and tradeoffs

Separating implementation from acceptance makes the review accountable to a different seat. Explicit ownership avoids shared-file overwrites. Sequential freeze-and-copy preserves the development chain and limits regressions. Full handoffs cost context but make requirements available to every participant without depending on ambient room visibility. Spec-derived tests supplement the partial official suites; a green published suite alone is insufficient evidence of complete correctness.

## Measurement and status

The production dispatch was observed at 2026-09-27 11:36:24 UTC; coordinator execution began approximately 11:37 UTC. Final elapsed time and accepted revisions will be recorded after completion. Tool durations and verifier command logs provide measured execution times. Provider-billed spend and a reliable per-run token total are currently unknown; any available Band catalog estimate will be labelled an estimate rather than a bill.

Stage 1 is accepted at implementation `8a2a07abfe972815cfea7c02176a075b8b2accaf`, independent evidence `3813508b5624b4ae89a346b68611a595f83cfde5`. Official host and isolated 120/120; independent HTTP/offline 23/23; independently rerun implementation tests 24/24. Stage 2 is accepted at implementation `e4fc1c5bf52769927b50e139be1d380b1c044aeb`, evidence `f2e3189db5f113f9b38509cc57241d9e50d91330`: official host/isolated 120+25, independent HTTP 30 plus 2 review cases, browser 7 and author tests 41 passed. Stages3 and4 subsequently completed independent review; see the final evidence below. Infrastructure rehearsal is a separate room and is not product-build evidence.

## Observed recovery

Independent stage-3 review caught a material portable-state bug after published checks passed: an edited export could erase a permanent diner exception. Verifier committed the failing HTTP regression against `835401316b3feb1d845da13478e72b90def427a9`; Engineer fixed adoption-revision/history validation in original commit `8a12344510a97d7ee20a4326935cacc3ab00798e`. Valid pre-adoption anchor edits remain nonexceptions, while reverted post-adoption edits remain exceptions. Independent revalidation passed, including final host/isolated 152 checks. Complete accepted evidence is `0e302c79de3521fc0993cb6ed0b6f21a52d493e4`; Stage4 followed as a copy-forward. This is an observed rejection-and-repair cycle, not a manufactured disagreement.

The initial two container builds timed out fetching Python image metadata through Colima, while host HTTPS reached the registry. A mirror pull from Colima also timed out. Coordinator downloaded the official image through the host using `crane`, loaded it into Docker, and returned the build to Engineer/Verifier without changing service or harness code. A temporary public-only Docker configuration avoided a missing credential helper without changing the user's configuration. [Recovery evidence](evidence/factory/registry-recovery.md) preserves the failed attempts and successful commands. Passing local tests were explicitly kept separate from pending container acceptance.

## Final Stage 4 review and measurement

Frozen service candidate `53617a341d21ebae3d76761f41b6ea4d38bc2a6c` passed independent review recorded in `aa816477c6a2a40b528a28c362a7ec67bfc566a1`: 69 independent HTTP checks both host and isolated, genuine stages1–3 migrations, inherited and new browser flows, and 24 generated exhaustive optimizer cases. Coordinator official host passed158/158; all four folders passed isolated inherited suites with expected next-stage rejections. Final clean-clone results and acceptance are recorded in [final evidence](evidence/final/verification.md).

The Stage4 backend-only candidate failed closure availability because server and availability signatures differed. Independent review preserved the failure; the Experience integration commit fixed it, and the committed candidate passed independent reruns. Browser contract-shape failures and corrected test assumptions are preserved separately. No service changes were made during final review.

Band room usage snapshot at final verification reported102,262,893 tokens and an approximately$131.32 catalog-estimated equivalent for this production room. This is local telemetry, not a provider bill; accounting semantics, cache treatment and completeness are not independently verified. Actual billed spend and a reliable final token total remain unknown. The room-only raw snapshot is in `evidence/final/usage-snapshot.json`; rehearsal and unrelated sessions are excluded. The run began at11:36:24UTC on2026-09-27; final evidence records the completion observation, including idle/recovery time rather than claiming continuous compute time.

Python3.12 is the verified/deployed runtime. Python3.14 accepts an hour24 input that3.12 rejects; this is a documented portability limitation. Finite generated cases do not prove every optimizer input; oversized-limit rejection was source-reviewed only. Chromium desktop/mobile checks do not constitute a screen-reader or cross-engine audit.
