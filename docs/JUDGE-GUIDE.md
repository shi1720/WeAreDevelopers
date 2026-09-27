# Inspect Proofline in three minutes

**Tablekeeper is the restaurant product. Proofline is the reusable four-seat BAND factory that built and checked it.** This route covers the original completed four-stage run. The [captioned demo video](../output/video/final/proofline-tablekeeper-demo.mp4) includes an authentic BAND Desktop room recording captured after completion. The separately verified hosted companion remains pending; a reserved website address is not a live deployment.

## 0:00 to 0:40: the task and the team

Open the [factory record](../factory/run.json), [generic mandates](../mandates/) and [original task](../factory/tasks/dispatch.md). Coordinator planned; Engineer and Experience shared implementation; Verifier independently checked committed candidates. Product requirements belong in the task, not the standing mandates.

The authentic [full BAND room export](../room.json) contains 3,540 messages from room `d82b4197-09c0-4af3-aabf-fa336747ff95`. Search message IDs `27cef353-ee6c-45ed-80bd-78684731ad14` for the single human text dispatch and `f8efe972-4b54-4280-8194-5c8c952a77ea` for the final report. Full addressed handoffs, replies and original failures remain in between; this guide does not replace the export.

## 0:40 to 1:20: a review that changed the result

Read the [stage-3 rejection](../evidence/stage-3/review-01.md), then the [independent recheck](../evidence/stage-3/verification.md). A corrupted restore could erase the marker protecting an individually changed recurring booking from later group edits. Verifier rejected the candidate; Engineer repaired history validation; independent checks confirmed the repair.

| Evidence | Original revision |
|---|---|
| Rejected candidate | `835401316b3feb1d845da13478e72b90def427a9` |
| Failing regression | `d2a871891627efdc5d34dab05bd6853686a49705` |
| Author repair | `8a12344510a97d7ee20a4326935cacc3ab00798e` |
| Independent evidence | `0e302c79de3521fc0993cb6ed0b6f21a52d493e4` |

This is an observed rejection and repair, not a staged disagreement.

## 1:20 to 2:00: the frozen results

The [release ledger](RELEASE-GATES.md) links the sequential acceptance chain. Each complete `stage-1/` through `stage-4/` folder copied its accepted predecessor forward before extension; later features were not copied backward.

The [final execution report](../evidence/final/verification.md) records the frozen stage-4 implementation `53617a341d21ebae3d76761f41b6ea4d38bc2a6c` and tested repository `aa816477c6a2a40b528a28c362a7ec67bfc566a1`. No service/static files changed between these revisions. Workspace and fresh local clone isolated runs each passed **120 / 145 / 152 / 158** required checks for stages 1 / 2 / 3 / 4. These include inherited suites: 575 executions per run, not 575 distinct requirements.

[Runtime inspection](../evidence/final/isolated-runtime.json) records two CPUs, two GiB and an internal network. [Independent stage-4 review](../evidence/stage-4/independent/verification.md) also ran 69 HTTP checks with networking disabled. Published tests are partial; hidden-suite success is not claimed.

The [post-export package check](../evidence/final/package-check.md) passed. The [unauthenticated public-clone check](../evidence/final/public-clone-check.txt) at `fb76fd0487212119f5b0fa7e6f7722057b93ddd7` confirmed public access, matching stage trees, the room fingerprint and checker exit 0. Packaging checks and isolated service executions establish different things.

## 2:00 to 3:00: try the promise, see the boundaries

Follow the [local demo runbook](DEMO-RUNBOOK.md): preview the Window nook closure at The Orangery, inspect one proposed move among three synthetic bookings, apply it, then view the guest's unchanged arrival time and accepted terms. The preview alone changes nothing. [README](../README.md) gives the Docker start commands; [FACTORY](../FACTORY.md) gives pinned harness and new-factory reproduction steps.

The planner supports **6 tables, 4 declared pairs and 6 considered bookings**. Every confirmed booking overlapping the closure counts. The frozen graded service is ephemeral and enables judge controls by default; run it locally, not as a public production service. Individual booking amendment is API-only, and amended-series summary refresh has a documented UX limitation.

The run required an **operator daemon/seat restart in the same room**, with new provider sessions and no new human task or implementation hints. It was not uninterrupted autonomy. Exact dispatch-to-final-report wall time was **6h 24m 04.981519s**, including recovery. [Usage accounting](../evidence/final/runtime-usage-method.md) distinguishes eight-session runtime counters from unknown provider-billed spend. No customers or revenue are claimed; the [commercial thesis](COMMERCIAL-THESIS.md) describes the small-venue hypothesis and validation gates.
