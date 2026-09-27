# Verification preparation

No companion candidate accepted or tested yet.

Independent baseline provenance inspection returned the same Git tree `53912d0263085f441225f962351d8876fef68ca1` for `330f1c8321670ca7d34b6b7127c0fb73df84ca25:stage-4` and `1448eea24239a59e03941fc3a1a691b86bad19d9:product`. This is the unchanged-copy commit, before any verifier product writes.

Official contracts read: all four `tablekeeper/spec/stage-N.md` files in pinned `/tmp/proofline-official-spec`; independent cases are mapped in `coverage.md`. These are planned cases, not results.

## Infrastructure

Firestore emulator v1.22.0 was already cached. `/usr/bin/java -version` failed because the default launcher has no selected runtime. Recovery used existing Java 21 directly:

```
/opt/homebrew/Cellar/openjdk@21/21.0.12.1/libexec/openjdk.jdk/Contents/Home/bin/java -jar /Users/shivamgupta/.cache/firebase/emulators/cloud-firestore-emulator-v1.22.0.jar --host 127.0.0.1 --port 18980 --project_id demo-proofline-pilot --single_project_mode true
```

The emulator started and remains a local synthetic-only service. Verifier uses `verifier-*` namespaces; Engineer was asked to use `engineer-*`. No cloud account or project was accessed.

A separate Python3.12 environment at `/Users/shivamgupta/.cache/proofline-pilot-verifier/venv` contains google-cloud-firestore2.32.0, httpx0.28.1 and pytest9.1.1. The original prepared environment was not modified. Browser execution will use its existing Playwright installation.

`runs/20260927T182135797195Z-infrastructure.json` and adjacent log record a successful real SDK emulator transaction/read/delete and cached Python3.12 container with `--network=none --cpus=2 --memory=2g` plus verified read-only repository mount. Exit0, measured1.766552seconds. This probe ran during active author edits, is infrastructure evidence only, and does not claim an immutable product acceptance result.

Next dependency: Engineer's committed adapter/auth interfaces and fault-injection protocol. Candidate execution will use a separate immutable committed checkout. The coverage matrix records outstanding gates, including actual browser recovery and multi-process Firestore product checks.
