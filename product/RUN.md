# Tablekeeper companion

Start with [operations and deployment](docs/operations.md), [the user guide](docs/user-guide.md), or [the isolated synthetic demo](docs/demo.md). Use Python 3.12.

This companion requires durable storage and explicit setup. Production defaults contain no synthetic accounts, and every `/_test/` route is unavailable. SQLite is the local adapter; Firestore is the hosted authority. The initial unchanged copy and original historical documentation remain in the recorded baseline commit.

For local development, from this folder, configure a private state path and exact public origin:

```sh
export TABLEKEEPER_MODE=development
export TABLEKEEPER_PUBLIC_ORIGIN=http://localhost:8080
export TABLEKEEPER_DB=/private/tablekeeper/venue.sqlite3
export TABLEKEEPER_SETUP_SECRET_FILE=/private/tablekeeper/setup-secret
python3.12 -m tablekeeper.server
```

Create a high-entropy setup secret in a protected 0600 file first, as described in the operations guide. To explore only synthetic data, omit the setup secret and explicitly set `TABLEKEEPER_PUBLIC_DEMO=1`; open `/demo`. Internet deployments use the bundled nginx container boundary and TLS, not the local Python entry point alone.

The original judge reset/bearer/ephemeral-storage harness assumptions no longer apply. Run scoped companion tests, and consult `evidence/product/` outside this folder for revision-specific independent acceptance. Do not run all inherited HTTP tests unchanged and describe that as companion acceptance.
