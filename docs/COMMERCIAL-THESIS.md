# Tablekeeper: keep the promise, even when the floor changes

Commercial thesis prepared for Shivam Gupta's Proofline factory project. Research checked **27 September 2026**. Proposed prices, demand, savings and operating costs below are hypotheses, not customers, revenue, measured production results or vendor quotes.

## The customer and the job

Start discovery with **intimate 4–6-table venues**: supper clubs, tasting rooms and small owner-operated restaurants that attract their own guests and manage direct or recurring group bookings. The buyer is the owner or general manager; the daily user is the host. This is a proposed interview cohort, not demonstrated demand or a list of existing customers.

Pilot eligibility must fit the actual planning boundary: **at most 6 tables, 4 declared combinable pairs and 6 considered bookings**. Considered bookings are every confirmed booking overlapping the proposed closure interval, not only bookings currently assigned to the closed table. A six-table venue can still exceed the booking bound across several seatings. Screen real schedules and closure intervals before offering recovery; where a plan exceeds the supported problem, report the limit and use the venue's established manual process. Splitting an arbitrary overlapping schedule into smaller plans does not establish a globally safe or optimal result. Larger-floor or higher-volume optimization requires separate development and validation.

The proposed job: **When a table becomes unusable, show me the smallest safe seating change that keeps my guests' times and agreed terms intact. Let me review it, then apply it together.** A damaged table or closed dining area is an illustrative scenario, not evidence of how frequently this happens.

Closure rescue is the memorable demonstration. Recurring group bookings, safe amendments and reliable direct reservations are the everyday reasons to return. A closure-only subscription may be too infrequently useful; discovery must test that objection first.

## What the market evidence does:and does not:establish

| Primary source | Verified published fact | Implication for our positioning |
|---|---|---|
| [OpenTable US plans](https://www.opentable.com/restaurant-solutions/plans/) | Basic $149/month, Core $299, Pro $499; network covers incur additional fees. Direct website bookings are included on Core/Pro. The matrix includes Smart Assign, floor plans and inventory controls. | Restaurants already buy operations tools. We must not claim every OpenTable booking incurs a fee, or imply it lacks seating intelligence. Its discovery network is value we do not replace. |
| [Resy plans](https://resy.com/join/plans-pricing/) | Platform is $289/month and Platform 360 $459. Resy states no per-cover fees; table management, guest alerts and integrations are listed. Tock's pricing URL redirects here. | Flat pricing is already common. Reliability, adoption and the specific recovery workflow must justify switching; “no cover fees” alone is not differentiation. |
| [Tablein pricing](https://www.tablein.com/pricing) | The displayed EUR plans are €67, €117 and €177 per restaurant/month; Success lists unlimited reservations. Floor plans, guest records, notifications and deposits are advertised. | Smaller-venue alternatives exist. We compete with established lower-cost tools as well as large networks. The page has inconsistent overage figures between its plan cards and FAQ; no overage comparison is used here. |

These sources establish competition and published offers, **not** underserved demand or willingness to pay. We have not verified that competitors lack recurring agreements, policy history or atomic closure recovery. A feature absence claim would require demonstrations and documentation review, not an empty search result.

## A credible wedge

Lead with a visible recovery workflow: before/after assignments, how many bookings move, unchanged guest times, and the terms each booking accepted. Refuse an impossible plan clearly. Never quietly cancel a guest to make the picture look successful.

The candidate advantage is an understandable promise backed by verifiable behavior: retried bookings remain one booking; group moves are all-or-nothing; historic terms survive policy changes; stale rescue plans cannot overwrite a newer floor. These are engineering properties required by the challenge. Claim them as achieved only where the shipped stage and recorded checks substantiate them.

The initial distribution hypothesis is owner referrals and local restaurant website agencies, not paid consumer acquisition. Target restaurants moving from a manual book or a direct-booking tool. Avoid promising effortless migration from a marketplace-dependent business. There is no implemented marketplace synchronization; running two independent sources of booking inventory would introduce a serious operational risk. Any future integration needs a documented source of truth and conflict handling.

## Offer and economics to test

Proposed offer after operational validation: **$79 per location per month**, direct reservations and recovery tools within the disclosed planning bounds, no per-cover charge. Seek five eligible design partners for a 30-day assisted evaluation, followed by an explicit paid decision. Offer the MIT source for self-hosting; proposed paid value is managed operation, backups, support and onboarding. This managed service is a future offer: a production companion is privately planned after the graded run, not implemented. Durable storage, hosted deployment or working backups must not be inferred from this pricing model. Do not hide costly SMS in an “unlimited” promise. SMS, deposits and subscription billing are not assumed to exist in the competition build.

Illustrative monthly economics for one separately hosted venue:

| Item | Planning allowance (USD) | Basis |
|---|---:|---|
| Revenue | 79.00 | Proposed price; no sales yet |
| Compute | 24.00 | Budget allowance, not a chosen deployment or capacity measurement |
| Daily image backups | 7.20 | 30% of assumed $24 compute, using [DigitalOcean's published backup rule](https://docs.digitalocean.com/products/backups/details/pricing/) |
| Monitoring, transactional email, independent data backup | 5.00 | Internal allowance; needs provider selection and restore testing |
| Payment collection | 3.00 | Conservative allowance; US domestic Stripe card baseline is about $2.59 on $79, with country/currency and optional billing costs to confirm |
| Support | 10.00 | Assumption: 20 minutes/month at $30/hour |
| Contribution after these costs | **29.80 (37.7%)** | Before development, acquisition, tax, incident response and general overhead |

[DigitalOcean lists a 2 GiB/1 vCPU basic VM at $12/month](https://www.digitalocean.com/pricing/droplets), but that is a price reference, not proof it meets our workload or recovery needs. The $24 allowance avoids pretending free-tier hosting is a sustainable service. [Stripe's published US domestic-card rate is 2.9% + $0.30](https://stripe.com/pricing); Shivam's actual seller jurisdiction, tax treatment, international cards and billing configuration must be established before using it as a quote.

Support dominates the downside. At one hour per venue/month instead of 20 minutes, contribution falls to **$9.80 (12.4%)**. Two hours of onboarding at $30/hour cost another $60 once. At 37.7% contribution, a hypothetical $120 acquisition cost plus $60 onboarding takes approximately six paid months to recover, before churn. This is a modest business to validate, not an assumed high-margin SaaS.

An illustrative customer value threshold: at an assumed $20 contribution per retained diner, four genuinely rescued diners cover a $79 fee. Alternatively, at an assumed $25/hour operator time value, about 3.2 hours saved does so. Use actual restaurant margins and observed time in a pilot; neither dinner spend nor all moved bookings should be counted as incremental profit.

## Validation before scaling

1. **Ten discovery interviews.** Recruit the proposed 4–6-table cohort and ask hosts to reconstruct their last disrupted service and repeat-booking amendment. Record frequency, workaround, minutes, errors and consequences; check table/pair counts and all bookings overlapping plausible closures. Interview existing-tool users too. Do not start by selling “AI.” Proceed only if at least five report recurring relevant work and three agree to an observed trial. If most relevant incidents exceed the six-considered-bookings bound, the current recovery offer does not fit this cohort: narrow the use case or validate a larger planner before pilots.
2. **Five observed prototype sessions.** Use anonymized schedules and scripted disruptions. Compare completion time and mistakes with the current workflow. Target at least four users finishing without facilitator rescue and no silent booking loss. Label scripted and real scenarios separately.
3. **Five controlled pilots, after readiness work.** Recruit only venues whose trial scenarios fit all three planning bounds. Start in shadow mode, without becoming the authoritative booking system. Measure safe completed amendments, recovery time, operator overrides, unsupported scenarios and support minutes. A preview alone is not a saved booking. Obtain consent before any real guest data is used. These pilots and interviews have not occurred.
4. **Paid decision.** Seek at least three explicit $79/month conversions and eight-week retention. No paid conversion or persistent support above one hour per venue/month triggers a pricing/scope review. If disruptions are rare, test recurring-booking administration as the lead; do not invent a larger market estimate.

Before authoritative live use, independently review authentication and tenant boundaries, protect or remove test/reset/import interfaces, add account recovery and session revocation, verify backups and restoration, establish retention/privacy practices, test accessibility and expected load, and define incident response. Challenge-conformant behavior and a container startup are not production certification. Email/SMS delivery, payments, external inventory integrations, high availability and broad-floor optimization remain separate product decisions unless explicitly built and verified.

## Where Proofline fits

**Tablekeeper sells dependable hospitality operations. Proofline is the reusable factory that builds and checks them.** Proofline's standing mandates, complete handoffs, independent review and evidence gates are the hackathon's principal engineering contribution. Factory execution cost is development spend, not a model charge on every reservation. Its actual time and model cost must come from the recorded run.

There is no durable moat in generic agent prompts or a small seating solver alone. A possible advantage would accumulate through trusted operations, well-tested migration, distribution relationships and a consented corpus of real failure cases converted into regression tests. None exists yet. Keep the restaurant offer and any later developer-tool commercialization separate until one has demonstrated demand.
