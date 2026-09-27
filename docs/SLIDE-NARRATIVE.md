# Proofline / Tablekeeper presentation

Final eight-slide presentation for the Dark Factory hackathon. All four stages have acceptance evidence, including final isolated and fresh-clone isolated runs. The deck is not a substitute for the mandatory BAND room recording.

## Narrative and verbatim speaker notes

### 1. Tablekeeper

“I’m Shivam Gupta. I set the product direction and configured Proofline, a reusable software factory in BAND. The agent seats are building Tablekeeper, a reservation service with one clear promise: keep the guest’s agreement intact, even when the floor changes.”

### 2. A booking is a promise to a guest

“Imagine it is seven in the evening. One table becomes unusable, and the guests are already on their way. A host needs to know who must move, whether everyone can keep their time, and whether the original terms still hold. That is our demonstration scenario. We have not yet measured how often it happens in real restaurants.”

### 3. One dispatch. Four distinct seats.

“This is the actual BAND Desktop room during stage four review. Coordinator plans and accepts. Engineer owns the domain behavior. Experience builds the workflow. Verifier challenges the implementation independently. The screenshot shows a real handoff, with original commits and checks attached to the work. Generic standing mandates keep those roles reusable.”

The image is an authentic in-progress still captured 27 September 2026 at 17:49 UTC. Its app estimate is not a provider bill. This slide cannot replace the required recording of the real room.

### 4. Four accepted stages

“All four stages passed the required published checks in both the isolated run and a fresh-clone isolated run: one hundred and twenty, one hundred and forty-five, one hundred and fifty-two, and one hundred and fifty-eight. Each stage includes the earlier suites, so these are not distinct requirements. The repository preserves the exact commands, revisions and results.”

Exact tested repository: `aa816477c6a2a40b528a28c362a7ec67bfc566a1`. Stage 4 frozen implementation: `53617a341d21ebae3d76761f41b6ea4d38bc2a6c`. Source: `evidence/final/verification.md` at acceptance commit `330f1c8`. Both all-stage commands exited 0. Expected next-stage overshoot rejections remain preserved.

### 5. A real seating repair preview

“This is the actual manager preview with synthetic bookings at The Orangery. Closing Window nook proposes one move to Garden table. Three bookings are considered, with zero unused seats. The screen says not applied. The manager reviews before committing a change. The planner is bounded to six tables, four declared pairs and six considered bookings. The screenshot shows the workflow. Independent checks passed against the frozen implementation, including adversarial planning and retry scenarios.”

This screenshot retains its original author-stage capture provenance, before final independent acceptance. The same frozen service subsequently passed independent and final execution checks. The native slide crop enlarges the actual summary, table map and changed booking. The complete screenshot preserves other assignments and the apply control in `evidence/stage-4-experience/stage4-manager-desktop.png`.

### 6. Independent review caught a hidden failure

“The published checks passed, but independent review caught something they missed. A corrupted restore could erase the permanent exception on an individually changed recurring booking. Verifier rejected the candidate. Engineer repaired the history validation. Independent checks then passed, including the original regression. The failed review and original fix remain in the repository. This is why our verifier has authority to hold a release.”

Primary evidence: `evidence/stage-3/review-01.md` and `evidence/stage-3/verification.md`. Original rejected candidate `835401316b3feb1d845da13478e72b90def427a9`, regression `d2a871891627efdc5d34dab05bd6853686a49705`, repair `8a12344510a97d7ee20a4326935cacc3ab00798e`. 47 HTTP checks ran together and three additional tests ran separately. Do not call them a single 50-test run.

### 7. A small restaurant business to validate

“The commercial hypothesis is a seventy-nine-dollar monthly service for intimate venues with four to six tables that already attract their own guests. Direct reservations are the everyday job. Recovery is the memorable demonstration. We plan to test demand with five design partners. The economics are deliberately modest: our assumptions leave twenty-nine dollars and eighty cents per month before acquisition and overhead. At one support hour per venue, that drops to nine dollars and eighty cents. Support, adoption and reliability must earn the business.”

### 8. Reproducible, with clear limits

“The final run passed from a fresh clone without outbound runtime access. The service ran within two virtual CPUs and two gibibytes of memory. Independent HTTP verification passed sixty-nine checks, including twenty-four generated planner fixtures. That is finite evidence, not a universal proof. The run took six hours and twenty-four minutes from dispatch to final report, including idle time and recovery. After a daemon interruption, we restarted the same BAND seats in the same room. They acquired new provider sessions. We sent no new task or implementation hints. Actual provider-billed spend is unavailable. Before live use, the service needs durable state, disabled test controls and operational validation.”

The original challenge service has ephemeral state and test controls enabled by default. No public deployment is claimed. The authentic room export is complete. The recorded walkthrough remains a separate required submission asset. The BAND screenshot is a still, not the required video.

Exact timing: dispatch `2026-09-27T11:36:12.525834Z` to final report `2026-09-27T18:00:17.507353Z`, or `6h 24m 04.981519s`. Source: `evidence/dispatch.json` and final report message. The authentic `room.json` export completed at `18:01:32.735Z`, containing 3,540 messages and 4,953,277 bytes. SHA-256: `5608a22b314bb25ddb46b8e1004581a3480c04f46bd3219f28483cf40eb22fbb`. Publication audit is separate from export completion.

## Evidence and recording boundaries

The final service results above are verified. The room still on slide 3 shows an authentic in-progress moment at 17:49 UTC and retains that caption. Slide 5 shows a preview that has not applied changes, with synthetic data. Neither screenshot alone proves service atomicity or replaces the mandatory recording.

Keep the optimizer bound visible in the narration: 6 tables, 4 declared pairs and 6 considered bookings. All overlapping confirmed bookings count. Do not imply broad-floor production readiness. Retain the runtime-restart disclosure and do not claim uninterrupted execution or zero operator assistance.

The BAND catalog estimate of $131.32365 at 17:56 covers four attributed sessions, with restart-inclusive accounting uncertain. It is not provider-billed spend and is not a total-cost claim. Model counters require their own provenance and cutoff. This deck makes no token or billed-cost claim.

## Presentation files

The final [editable PowerPoint](../output/presentation/deliverables/proofline-tablekeeper.pptx) and [companion PDF](../output/pdf/proofline-tablekeeper.pdf) are included. Foreground text remains editable in the PowerPoint; the PDF preserves the reviewed rendered layout. The generation toolchain is workstation-specific and is not included in the published repository. Draft builds and intermediate renders are excluded.

## Credits and sources

Shivam Gupta: product direction and factory configuration. BAND coding-agent seats: implementation and verification, subject to the actual recorded run. No invented manual coding, customers, revenue, savings or benchmark results.

Sources: `factory/tasks/dispatch.md`, `docs/COMMERCIAL-THESIS.md`, and official stage specifications pinned to `803560d2a678ace1414465c098eb0ab5380ffade`. Relevant public source URLs appear in slide speaker notes. Restaurant artwork is generated illustration for this project.
