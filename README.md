# Tablekeeper

**Keep the promise, even when the floor changes.** A reservation is a promise to a guest. Tablekeeper helps a restaurant keep that promise through booking changes, evolving policies and table closures.

This repository is the Tablekeeper-track output of **Proofline**, a four-seat software factory. Shivam Gupta supplied product direction and factory configuration; Proofline's coding-agent seats implement and independently verify the software. See [FACTORY.md](FACTORY.md) for setup, responsibilities and release gates.

## Read the repository

- `stage-1/`: clean-room reservation API, retry receipts, atomic multi-booking moves and state transfer.
- `stage-2/`: the accepted predecessor extended with combined tables and a resilient browser booking experience.
- `stage-3/`: effective-dated policies, accepted terms, history and recurring bookings.
- `stage-4/`: optimal closure planning, atomic seating repair and recurring amendments.
- `mandates/` and `factory/`: reusable seat instructions, identities and the original production dispatch.
- [Release ledger](docs/RELEASE-GATES.md): requirement families, accepted revisions and evidence status.
- [Security boundaries](docs/SECURITY.md): judge controls, private exports and deployment limitations.

The four folders are complete, independently buildable sequential releases. Each extends its accepted predecessor. Exact accepted revisions, independent review and final execution results are in the [release ledger](docs/RELEASE-GATES.md) and [final verification report](evidence/final/verification.md). The authentic full [BAND room export](room.json) contains 3,540 messages and was exported after completion. The original run needed an operator daemon/session restart, disclosed in [FACTORY.md](FACTORY.md); no additional human implementation task or hint was sent.

## Verification

The official contracts are from kickoff revision `803560d2a678ace1414465c098eb0ab5380ffade`. From that checkout, with its prepared Python environment and Docker running:

```sh
.venv/bin/python -m harness run --track tablekeeper \
  --repo /absolute/path/to/this/repository --all --mode isolated \
  --out /absolute/path/to/a/new/check-directory
.venv/bin/python -m harness check /absolute/path/to/this/repository --track tablekeeper
```

Every run needs a new output directory. Published checks are partial; independent specification-derived checks and source review are also required. Final isolated execution passed 120, 145, 152 and 158 required checks for stages 1 through 4 respectively, both in the workspace and a fresh local clone: 575 check executions per run, not 575 distinct requirements. The published suites are partial. Historical submission-check logs predate the final room export; final post-export packaging validation remains a separate gate.

Run the accepted browser product locally:

```sh
docker build -t tablekeeper-stage-4 stage-4
docker run --rm -e PORT=8080 -p 127.0.0.1:8080:8080 tablekeeper-stage-4
```

Open `http://localhost:8080`. See [demo runbook](docs/DEMO-RUNBOOK.md) for the exact synthetic account and scenario, and each stage's `RUN.md` for options. The judge image intentionally enables unauthenticated test controls. It must not be exposed publicly in that mode.

## Product boundary and next step

The accepted stage-4 product includes guest signup/login, booking and lookup, recurring administration, manager closure preview/apply, and responsive browser flows. Its recovery planner supports at most **6 tables, 4 declared pairs and 6 considered bookings**. All confirmed bookings overlapping the closure count, including those on unaffected tables; splitting arbitrary overlapping plans is not a validated extension.

The graded service keeps state in memory and enables judge test controls by default. It is a local demonstration and contract implementation, not a durable public restaurant service. A separate operational companion and Firebase deployment are pending. No hosted URL, durable cloud storage or production certification is claimed here. Individual booking amendment is API-only in the frozen product, and amended-series summary refresh has a documented UX limitation.

Our proposed first pilots are intimate four-to-six-table venues with direct or recurring groups. The proposed $79/location/month is a hypothesis, not customer revenue. Read the [commercial thesis](docs/COMMERCIAL-THESIS.md), [submission copy](docs/SUBMISSION.md), and [video script](docs/VIDEO-SCRIPT.md).

Original project code is [MIT](LICENSE). Official specification text retained in the room export keeps its upstream license; see [third-party notices](THIRD-PARTY-NOTICES.md).
