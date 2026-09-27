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

The folders are sequential releases, each complete and independently buildable after acceptance. **Stage 1 is accepted** at implementation `8a2a07abfe972815cfea7c02176a075b8b2accaf`, with independent evidence at `3813508b5624b4ae89a346b68611a595f83cfde5`: official host/isolated checks 120/120 and independent HTTP/offline checks 23/23. Stage 2 is also accepted; stage 3 is accepted and stage 4 is underway. A folder's presence during development is not an acceptance claim. The ledger records exact reviewed revisions and commands.

## Verification

The official contracts are from kickoff revision `803560d2a678ace1414465c098eb0ab5380ffade`. From that checkout, with its prepared Python environment and Docker running:

```sh
.venv/bin/python -m harness run --track tablekeeper \
  --repo /absolute/path/to/this/repository --all --mode isolated \
  --out /absolute/path/to/a/new/check-directory
.venv/bin/python -m harness check /absolute/path/to/this/repository --track tablekeeper
```

Every run needs a new output directory. Published checks are partial; independent specification-derived checks and source review are also required. The operator exports the authentic complete Band room as `room.json` after the autonomous run. Until then the room-log submission gate remains pending.

Stage 2 is also accepted at `e4fc1c5bf52769927b50e139be1d380b1c044aeb`, evidence `f2e3189db5f113f9b38509cc57241d9e50d91330`: official host/isolated 120+25 checks pass. Stage 3 is accepted at `8a12344510a97d7ee20a4326935cacc3ab00798e`, evidence `0e302c79de3521fc0993cb6ed0b6f21a52d493e4`, with all 152 official checks passing host/isolated. Stage 4 is underway.

Run the accepted browser product locally:

```sh
docker build -t tablekeeper-stage-2 stage-2
docker run --rm -e PORT=8080 -p 127.0.0.1:8080:8080 tablekeeper-stage-2
```

Open `http://localhost:8080`. See [demo runbook](docs/DEMO-RUNBOOK.md) for the exact synthetic account and scenario, and each stage's `RUN.md` for options. The judge image intentionally enables unauthenticated test controls. It must not be exposed publicly in that mode.

Licensed under [MIT](LICENSE). This is a hackathon service, not a production certification or claim of customer adoption.
