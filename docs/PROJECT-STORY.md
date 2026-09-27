# Proofline: Tablekeeper

## Inspiration

A reservation is a promise: a place, a time and agreed terms. If a table becomes unusable before dinner, a host may need to change several bookings while guests are already on their way. We chose that moment because a software failure becomes a human problem immediately.

Tablekeeper is the restaurant product. Proofline is the reusable agent factory behind it. The hackathon gave us a concrete way to test whether agents could share implementation work, reject a flawed result and repair it without another human task.

## What it does

Tablekeeper lets guests sign up, search availability, book and manage reservations, and arrange recurring visits. Restaurants can offer approved table combinations and publish dated policies. Each booking retains the terms its guest accepted.

When a table closes, the manager previews a seating repair. The planner first minimizes moved bookings, then unused seats, with a deterministic tie-break. Applying a valid plan changes the seating together. A stale plan requires a new preview. An impossible plan cannot quietly cancel a guest.

The supported planning problem contains at most six tables, four declared pairs and six considered bookings. Every confirmed booking overlapping the closure interval counts, including bookings on other tables. The demonstration uses synthetic guests and a synthetic restaurant, The Orangery.

## How we built it

Shivam Gupta directed the product and configured four coding-agent seats in BAND Desktop. Coordinator owned planning and acceptance. Engineer and Experience shared substantive implementation work. Verifier reviewed committed candidates and developed independent checks.

Their standing mandates describe reusable responsibilities. The restaurant contract belongs in the task. A single production dispatch covered all four stages, with each accepted service copied forward into the next complete, independently buildable folder.

The graded service uses Python, a standard-library HTTP server, local browser assets and an in-memory state model. Mutations operate on a copy under a lock and publish only on success. Docker makes the runtime reproducible without outbound network access. The repository preserves the original seat commits, handoffs, failures and test evidence.

## Challenges we ran into

The strongest review finding came after the published checks passed. A corrupted import could remove a permanent exception from a manually changed recurring booking. Verifier rejected the candidate and preserved the failing regression. Engineer repaired the history validation, and independent verification confirmed the fix.

Infrastructure also needed recovery. Registry access through the local VM failed, and the runtime later suffered a daemon interruption. The operator restarted the same BAND seats in the same room. They received new provider sessions, with no new task or implementation hints. We disclose these interventions instead of calling the run uninterrupted.

## Accomplishments that we're proud of

All four service stages are accepted. Both the final isolated run and a fresh-clone isolated run passed the required published checks: 120, 145, 152 and 158 for stages one through four. These counts include inherited suites and are not distinct requirements.

The stage-four independent HTTP suite passed 69 checks on the host and with networking disabled, including 24 generated planner fixtures. Those are finite checks, not a proof of every possible input. The authentic BAND room export and original commit history make the work inspectable.

## What we learned

A public test pass is useful evidence, but independent review still matters. State restoration must preserve the meaning of a guest's history, not merely accept a structurally valid document. Clear ownership and complete handoffs helped the seats turn a rejection into a verified repair.

We also learned to separate a working challenge service from an operational business. The graded stages use ephemeral state and enable judge controls by default. They should not be exposed publicly as a production system.

## What's next for the project

A separate cloud companion is underway for a hosted demonstration. It is outside the original graded run and does not inherit the graded test results automatically. Its live URL, storage behavior and deployment checks will be reported only after verification.

Our customer hypothesis is intimate venues with four to six tables and direct or recurring groups. The proposed price is $79 per location per month, subject to observed trials and paid decisions. No customers, revenue or savings are claimed. Before authoritative restaurant use, we need operational authentication, durable storage, restore testing and a support model that works economically.

## Evidence

- Final acceptance and exact revisions: `evidence/final/verification.md`
- Independent review and repair: `evidence/stage-3/review-01.md` and `evidence/stage-3/verification.md`
- Stage-four independent results: `evidence/stage-4/independent/verification.md`
- Generic mandates and dispatch: `factory/`
- Commercial assumptions: `docs/COMMERCIAL-THESIS.md`
