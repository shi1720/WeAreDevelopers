# Tablekeeper

**Keep the promise, even when the floor changes.** A reservation is a promise to a guest. Tablekeeper is being built to help a restaurant keep that promise through booking changes, evolving policies and table closures.

This repository is the Tablekeeper-track output of **Proofline**, a four-seat software factory. Shivam Gupta supplied product direction and factory configuration; Proofline's coding-agent seats implement and independently verify the software. See [FACTORY.md](FACTORY.md) for setup, responsibilities and release gates.

## Read the repository

- `stage-1/`: clean-room reservation API, retry receipts, atomic multi-booking moves and state transfer.
- `stage-2/`: the accepted predecessor extended with combined tables and a resilient browser booking experience.
- `stage-3/`: effective-dated policies, accepted terms, history and recurring bookings.
- `stage-4/`: optimal closure planning, atomic seating repair and recurring amendments.
- `mandates/` and `factory/`: reusable seat instructions, identities and the original production dispatch.
- [Release ledger](docs/RELEASE-GATES.md): requirement families, accepted revisions and evidence status.
- [Security boundaries](docs/SECURITY.md): judge controls, private exports and deployment limitations.

The folders are sequential releases, each complete and independently buildable after acceptance. At this point the production run is underway and **no stage has been accepted**. A folder's presence during development is not an acceptance claim. The ledger will record exact reviewed revisions and commands as they pass.

## Verification

The official contracts are from kickoff revision `803560d2a678ace1414465c098eb0ab5380ffade`. From that checkout, with its prepared Python environment and Docker running:

```sh
.venv/bin/python -m harness run --track tablekeeper \
  --repo /absolute/path/to/this/repository --all --mode isolated \
  --out /absolute/path/to/a/new/check-directory
.venv/bin/python -m harness check /absolute/path/to/this/repository --track tablekeeper
```

Every run needs a new output directory. Published checks are partial; independent specification-derived checks and source review are also required. The operator exports the authentic complete Band room as `room.json` after the autonomous run. Until then the room-log submission gate remains pending.

Run and synthetic-demo commands will be documented in each accepted stage's `RUN.md` and `docs/DEMO-RUNBOOK.md`. The judge image intentionally enables unauthenticated test controls. It must not be exposed publicly in that mode.

Licensed under [MIT](LICENSE). This is a hackathon service, not a production certification or claim of customer adoption.
