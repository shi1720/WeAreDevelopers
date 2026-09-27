# Exact lablab form copy

Validated against the observed form limits: title 5 to 50 characters, short description 50 to 255, long description 600 to 2,000. Counts below include whitespace and line breaks inside each block, excluding the code fences and their surrounding newlines. Copy only the contents of each block.

## Title (22 characters)

```text
Proofline: Tablekeeper
```

## Short description (132 characters)

```text
A BAND agent factory builds reliable reservations and seating repair, so restaurants can keep guest promises when the floor changes.
```

## Long description (1990 characters)

```text
Inspiration
A reservation is a promise. When a table closes before dinner, keeping it may require changing several bookings together.

What it does
Tablekeeper offers booking, recurring visits, dated policies and a manager's seating-repair preview. Apply moves bookings atomically while preserving guest times and accepted terms. The planner supports six tables, four declared pairs and six considered bookings; every confirmed booking overlapping the closure counts.

How we built it
Shivam Gupta directed the product and configured Proofline: four BAND seats with generic mandates. Coordinator planned, Engineer and Experience implemented, and Verifier checked committed results independently. One human task covered all four stages. Original commits, handoffs and the full room export are preserved.

Challenges
Verifier found that a corrupted restore could erase an individually changed recurring booking's permanent exception. It rejected the candidate; Engineer repaired history validation and independent rechecks passed. A daemon interruption required an operator restart of the same seats and room, with new provider sessions. No new task or implementation hints were sent.

Accomplishments
All four stages were accepted. Workspace and fresh-clone isolated runs each passed 120, 145, 152 and 158 required checks for stages one to four, including inherited suites. These are check executions, not distinct requirements. Published tests are partial; hidden-suite success is not claimed.

What we learned
Independent review matters after public tests pass. The frozen service has ephemeral state and judge controls, so it is not a public production deployment. Provider-billed spend is unknown.

Next
A separate durable companion is live, with verified backend and browser checks. Our first customer hypothesis is intimate four-to-six-table venues with direct or recurring groups. The proposed $79 per location monthly needs paid-pilot validation; no customers or revenue are claimed.
```

## Separate fields and finalization notes

These notes are outside the copiable description text.

- Creator: Shivam Gupta. Track: tablekeeper.
- Repository: https://github.com/shi1720/WeAreDevelopers. Public access and unauthenticated clone check are recorded; retain final push receipts.
- Website URL: https://tablekeeper-proofline.web.app. Companion accepted, cloud backend verified and Firebase Hosting deployed; public-origin HTTP and Chrome checks passed.
- Submission: https://lablab.ai/ai-hackathons/wearedevelopers-hackathon/proofline/proofline-tablekeeper. Lablab confirmed successful submission; the final MP4, PDF and cover are published. The public video loaded at 177.233 seconds. YouTube upload still awaits action-time confirmation; no YouTube watch URL exists yet.
- Suggested technologies: BAND Desktop, Codex, Python, Docker, automated testing; Firebase Hosting, Google Cloud Run and Firestore for the separate deployed companion.
- Full seven-section story: [PROJECT-STORY.md](PROJECT-STORY.md). Detailed original-run submission narrative: [SUBMISSION.md](SUBMISSION.md).
- Do not claim this deployment has a Firestore free allowance. The operator reports a dedicated named database in an existing billing project with `freeTier: false`. Usage and actual billing must be measured; generic platform allowances do not establish this database's entitlement.
- Hosted checks passed at source revision 053ae0d. Preserve the frozen-service boundary, one-task/restart disclosure and original test counts.
