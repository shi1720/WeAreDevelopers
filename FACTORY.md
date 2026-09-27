# Proofline

Proofline turns a written contract into independently checked releases through four persistent Band coding-agent seats. This run builds Tablekeeper: keep the promise, even when the floor changes.

Shivam Gupta supplied product direction, factory configuration and the single production dispatch. The agent seats author implementation, tests and this report. No customer, revenue, certification or manual human implementation claims are made.

## Reproduce the factory

Create four distinct Band Desktop agent identities named Proofline Coordinator, Proofline Engineer, Proofline Experience and Proofline Verifier. Configure each with the corresponding file in `mandates/`, the Codex harness and model `gpt-6-astra`. These are the configured model identifiers; the runtime does not independently expose a serving-model attestation. The mandates describe reusable responsibilities rather than product endpoints.

Give every seat the same absolute clean result-repository path and filesystem, shell, Docker and browser access. Install Python 3.12+ for the official harness, Git, a running Docker daemon and Playwright Chromium. Keep provider credentials outside the repository. Start a fresh Band room, add all four configured identities, verify membership and reciprocal addressed delivery, then send one complete production dispatch. `factory/run.json` records the exact identities and official contract revision for this run; `factory/tasks/dispatch.md` records the operator task.

Use the coordinator to distribute full contracts in numbered addressed messages. A path or room message ID alone is insufficient. Assign separate actual implementation files to Engineer and Experience; Verifier independently derives checks from the full specification. Confirm module interfaces before editing. Shared work cards track assignment; each runtime maintains its own private execution tasks.

The coordinator owns planning, release gates and factory documentation. Engineer owns domain writes, atomic state and deployment. Experience owns temporal/availability implementation initially, then the browser product and demonstration. Verifier owns independent tests and acceptance evidence. Seats commit only their owned files with per-command author identities. Original commits and failed checks remain in history; no amend, rebase or squash is used.

## Release gates

Each stage begins as a complete copy of its accepted predecessor, with the first built from no source. Future capabilities never move backward. Before acceptance, stop editing the candidate folder and identify a full committed revision. Verifier reviews source, executes independent boundary/adversarial checks and official inherited suites, confirms the expected next-stage overshoot failure, then checks isolated operation with no outbound network, two CPUs and two GiB. A failing requirement returns to its author with reproducible evidence; verification runs again against the repaired committed revision.

Final validation includes every stage in isolated mode and an independent clean clone. All harness output directories are new. Raw state exports can contain password hashes and bearer tokens and remain private outside Git. Only reviewed public-safe evidence enters `evidence/`. Authentic `room.json` is exported by the operator after the run; its absence is a pending submission gate, never replaced with fabricated messages.

## Design choices and tradeoffs

Separating implementation from acceptance makes the review accountable to a different seat. Explicit ownership avoids shared-file overwrites. Sequential freeze-and-copy preserves the development chain and limits regressions. Full handoffs cost context but make requirements available to every participant without depending on ambient room visibility. Spec-derived tests supplement the partial official suites; a green published suite alone is insufficient evidence of complete correctness.

## Measurement and status

The production dispatch was observed at 2026-09-27 11:36:24 UTC; coordinator execution began approximately 11:37 UTC. Final elapsed time and accepted revisions will be recorded after completion. Tool durations and verifier command logs provide measured execution times. Provider-billed spend and a reliable per-run token total are currently unknown; any available Band catalog estimate will be labelled an estimate rather than a bill.

Stage 1 is accepted at implementation `8a2a07abfe972815cfea7c02176a075b8b2accaf`, independent evidence `3813508b5624b4ae89a346b68611a595f83cfde5`. Official host and isolated 120/120; independent HTTP/offline 23/23; independently rerun implementation tests 24/24. Stage 2 has been dispatched as a complete copy-forward. Infrastructure rehearsal is a separate room and is not product-build evidence.

## Observed recovery

The initial two container builds timed out fetching Python image metadata through Colima, while host HTTPS reached the registry. A mirror pull from Colima also timed out. Coordinator downloaded the official image through the host using `crane`, loaded it into Docker, and returned the build to Engineer/Verifier without changing service or harness code. A temporary public-only Docker configuration avoided a missing credential helper without changing the user's configuration. [Recovery evidence](evidence/factory/registry-recovery.md) preserves the failed attempts and successful commands. Passing local tests were explicitly kept separate from pending container acceptance.
