# Proofline: three-minute presentation

**Evidence-finalized narration; recording and publication remain pending.** This script describes the frozen graded stage-4 product. It does not claim that a hosted companion, narration track, final video or YouTube upload already exists. At approximately 135 words per minute, allow about three minutes; time captions against the actual final audio.

## Word-for-word narration

Hi, I'm Shivam Gupta. A reservation is a promise: a place, a time, and agreed terms. If a table becomes unusable before dinner, keeping that promise can mean changing several bookings together. We built Tablekeeper around that moment: keep the promise, even when the floor changes.

Behind it is Proofline, our software factory in BAND Desktop. I directed the product and configured four coding-agent seats: Coordinator, Engineer, Experience and Verifier. The agents wrote and checked the implementation. Their standing mandates describe reusable responsibilities; restaurant requirements belong in the task.

Here is the single production dispatch, and a real handoff between seats. Engineer and Experience share implementation work. Verifier checks committed revisions independently. The room connects each decision to the work it produced.

That separation caught something the published checks missed. In stage three, a corrupted restore could erase the exception on an individually changed recurring booking. Verifier rejected the candidate. Engineer repaired the history validation, and independent checks passed, including the original regression. The failed review and repair remain in the repository.

The run also needed operator assistance: after a daemon interruption, the same BAND seats were restarted in the same room. They acquired new provider sessions. No new task or implementation hints were sent. We disclose that recovery rather than call this an uninterrupted run.

Now look at the accepted product. These are three synthetic bookings at The Orangery. Closing Window nook proposes one move to Garden table, with zero unused seats. The other bookings stay put. Nothing has moved yet. The manager reviews, then applies the plan. The guest's arrival time, party size and accepted terms stay the same.

The planner supports six tables, four declared pairs and six considered bookings. Every confirmed booking overlapping the closure counts. This is a bounded small-venue workflow.

All four stages were accepted. A fresh-clone isolated run passed five hundred and seventy-five required check executions, with outbound networking disabled. Published tests are partial. Provider-billed spend is unknown, and the repository separates runtime counters from cost estimates.

The frozen service is a local demonstration with ephemeral state, not a production certification. A durable hosted companion is pending. Our first customer hypothesis is intimate four-to-six-table venues with direct or recurring groups. Seventy-nine dollars per location per month is a price to test; no adoption or revenue is claimed. Tablekeeper keeps guest promises. Proofline makes the work behind those promises inspectable.

## Editor shot list

| Approximate time | Actual material to show |
|---|---|
| 0:00 to 0:22 | Shivam or title and booking interface; use the accepted stage-4 local demo |
| 0:22 to 0:53 | Actual BAND Desktop submission room, four seat names, original dispatch and one complete addressed handoff |
| 0:53 to 1:19 | Stage-3 rejection, history-validation fix and passing independent review; preserve the original sequence |
| 1:19 to 1:40 | Same room with a brief legible operator-restart disclosure |
| 1:40 to 2:14 | Follow DEMO-RUNBOOK: three bookings, Window nook closure, one proposed move, preview, apply, then guest lookup |
| 2:14 to 2:30 | Planner-bound caption, then actual final isolated report and fresh-clone results |
| 2:30 to 3:05 | Ephemeral-state boundary, proposed pilot cohort/$79, repository link and closing |

## Evidence and recording boundaries

- Actual room: `d82b4197-09c0-4af3-aabf-fa336747ff95`; full export at root `room.json`. The video must contain a genuine BAND Desktop room recording, not only screenshots or an animated mock conversation.
- Stage-3 rejected candidate: `835401316b3feb1d845da13478e72b90def427a9`; regression `d2a871891627efdc5d34dab05bd6853686a49705`; fix `8a12344510a97d7ee20a4326935cacc3ab00798e`. See `evidence/stage-3/review-01.md` and `verification.md`.
- Frozen stage-4 implementation: `53617a341d21ebae3d76761f41b6ea4d38bc2a6c`. Independent tests/evidence revision: `aa816477c6a2a40b528a28c362a7ec67bfc566a1`; no service changes between them. See `evidence/final/verification.md`.
- The 575 total is 120 + 145 + 152 + 158 inherited-suite executions across four stages, not 575 distinct requirements. Independent stage-4 checks were 69 HTTP cases in both host and isolated modes, plus 24 generated exhaustive optimizer cases.
- Record the full preview/apply/guest-lookup sequence using `docs/DEMO-RUNBOOK.md`. A development screenshot alone does not support narrated application. If footage omits apply, shorten narration to describe the preview rather than imply the missing action is visible.
- Use synthetic fixtures only. Hide provider credentials, tokens, unrelated notifications and raw state exports. Retain the restart disclosure in both narration and captions.
- Use Shivam's recorded voice or an explicitly authorized synthetic narrator. If a narrator other than Shivam speaks, replace the opening with “This is Tablekeeper, directed and configured by Shivam Gupta” and change first-person attribution throughout. Do not imply synthetic speech is a recording of his voice.
- Re-time captions to the final audio, check proper names and numbers, inspect the entire exported video, then verify the public YouTube watch URL. No upload is considered complete merely because this script exists.
