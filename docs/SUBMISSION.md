# Proofline submission pack

**Verified original-run copy; final packaging, hosted companion and platform submission are pending.** Reconcile this status with actual upload receipts before submitting. Do not substitute future companion results for the original graded run.

## Form fields

**Project title:** Proofline: Tablekeeper

**Short description (120 characters):**

> A BAND agent factory builds Tablekeeper: reliable reservations and a plan to keep guest promises when the floor changes.

**Team / creator:** Shivam Gupta

**Track:** tablekeeper

**Technology tags:** BAND Desktop, Codex, Python, Docker, Automated testing, Multi-agent systems

**Category tags:** Developer tools, Hospitality, Workflow automation, Reliability

Use the platform's available choices. Do not add Firebase or durable-database implementation tags before the separate companion is actually verified and deployed.

## Long description

A reservation is a promise: a place, a time, and agreed terms. When a table becomes unusable before dinner service, keeping that promise can mean changing several bookings together. Tablekeeper is our clean-room restaurant reservation product built around that moment: keep the promise, even when the floor changes. Proofline is the reusable BAND software factory that built and independently checked it.

Shivam Gupta directed the product and configured four distinct coding-agent seats: Coordinator, Engineer, Experience and Verifier. Their standing mandates describe responsibilities, complete handoffs and rejection criteria without naming restaurant endpoints or challenge-specific fields. Product details belong in the dispatched task. Engineer and Experience both implemented substantive parts of the product; Verifier derived independent checks and reviewed committed candidates. The authentic full BAND room export connects the work to its handoffs and decisions.

The original run received one human text dispatch covering all four stages in sequence. It did require operator-assisted infrastructure recovery: after the BAND daemon became unreachable, the operator restarted the same four seats in the same room. They acquired replacement provider sessions. No new task, implementation hints or approvals were sent. We disclose this intervention rather than describe an uninterrupted run or decide its autonomy score ourselves.

All four stages completed independent acceptance. Each has its own complete buildable folder, copied forward from its accepted predecessor. Final workspace and fresh-clone isolated runs each passed 575 required check executions: 120, 145, 152 and 158 for stages one through four. These totals include inherited suites, not 575 distinct requirements. Runtime inspection confirmed the official CPU, memory and no-outbound-network controls. Independent stage-four review also passed 69 HTTP checks in host and isolated modes and 24 generated exhaustive optimizer cases. Published tests are partial; hidden-test success and universal correctness are not claimed.

Independent review changed the result. In stage three, a malformed state restore could erase the permanent exception on an individually changed recurring booking, allowing later series edits to treat that visit incorrectly. Verifier preserved a failing regression and rejected the candidate. Engineer repaired adoption-history validation; independent revalidation passed. The failed candidate, repair and review remain in the repository rather than being replaced by a polished success-only transcript.

The browser product supports signup, login, availability, booking lookup, recurring administration and a manager closure-repair workflow. In the synthetic Orangery scenario, closing Window nook considers three bookings and proposes one move to Garden table, with zero unused seats. Preview changes nothing. Applying the plan keeps guest times, party sizes and accepted terms while updating the affected seating atomically. A stale plan must be rejected and refreshed.

The planner is deliberately bounded to six tables, four declared combinable pairs and six considered bookings. Every confirmed booking overlapping the closure interval counts, including bookings on unaffected tables. Splitting arbitrary overlapping plans is not a validated way around that boundary. Our first customer hypothesis is intimate four-to-six-table supper clubs, tasting rooms and owner-operated restaurants with direct or recurring groups. The proposed $79 per location per month requires discovery and paid-pilot validation. Competitors already offer table management; no interviews, customers, revenue or measured savings are invented.

From dispatch at 11:36:12.525834 UTC to the final report at 18:00:17.507353 UTC on September 27, the original run took 6 hours, 24 minutes and 4.981519 seconds of wall time, including recovery. A post-acceptance snapshot across eight identified provider-session epochs reports 119,443,159 runtime tokens, mostly cached input. These are repeated-request counters, not unique generated text or an invoice. Provider-billed spend is unknown; the repository explains the cutoff and exclusions instead of presenting an incomplete catalog estimate as cost.

The frozen graded service uses ephemeral state and judge controls, so it is a local demonstration rather than an internet-production deployment. Individual booking amendments remain API-only, and amended-series summary refresh has a documented UX limitation. A separate durable operational companion and Firebase deployment are pending. The submission preserves the original factory, full room, accepted stages, measured evidence and remaining limits so judges can inspect both the result and the process that produced it.

## Submission field checklist

| Field or gate | Evidence / current state |
|---|---|
| Title and descriptions | Verified original-run copy above; confirm platform limits |
| Public repository | Confirm final pushed URL and public clean clone |
| Stage folders | All four accepted; frozen implementation and independent reports linked in FACTORY.md |
| Factory setup | FACTORY.md includes portable commands, recovery and measured usage limitations |
| Generic mandates | Actual files preserved; run final official package check |
| Room export | Authentic root room.json; full export, 3,540 messages, exported 18:01:32 UTC |
| Cover and slide presentation | Local assets need final editorial/visual review and upload confirmation |
| Video | Evidence-finalized script; genuine BAND Desktop recording, final audio/captions and public YouTube URL still need verification |
| Security/licensing | Best-effort export review complete; final staged-file/history scan and third-party notices required |
| Service checks | Original workspace and fresh-clone isolated tests passed; historical package check predates export |
| Final package check | Post-export official checker and final public clone remain distinct finalization gates |
| Hosted companion | Pending; no public deployment or durable operation claim |
| Submission receipt | Not submitted; retain actual lablab confirmation |

The original room export and old checker logs are historical records. Keep them unchanged; add later package-check evidence separately. Platform publication, team creation and submission require their actual successful results, not this checklist alone.
