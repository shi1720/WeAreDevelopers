# Stage 3 first independent review

Candidate `835401316b3feb1d845da13478e72b90def427a9`: **REJECT pending repair**.

45 prepared HTTP checks passed in10.747s. Official host inherited/current suites passed; expected stage4 overshoot failed. Harness exit0, time real46.52s. Final isolated gate not yet run.

Additional source-review regression `independent_import_relations.py` failed: create anchor, adopt3 weekly occurrences, individually PATCH occurrence1 party_size2→1, export, change only that occurrence exception true→false, import. Actual204 and state changed; expected422 validation_failed and unchanged destination. Stage3 makes real individual PATCH exceptions permanent; stage1 requires invalid-state import rejection atomically. A clearing exception changes future series eligibility. The source validates nonexception scheduled date but does not relate the flag to historical amendments. The test keeps credentials/export in memory. One failing test,0.187s; unittest failure status1 (the shell's trailing tail returned0). Reproduction:

```sh
TABLEKEEPER_BASE_URL=http://127.0.0.1:18093 /tmp/proofline-official-spec/.venv/bin/python -m unittest discover -s stage-3/tests -p independent_import_relations.py -v
```

Official host command from immutable official checkout:

```sh
.venv/bin/python -m harness run --track tablekeeper --repo /Users/shivamgupta/Downloads/we-are-developers --stage 3 --out /Users/shivamgupta/.cache/proofline-checks/s3-host-01
```

Environment and build-only adapter are unchanged from stage2 evidence. Reviewer container image60f04d3dd025, host port18093,2CPU2GiB. No service edits made. Finding sent to coordinator and engineer for controlled repair. Acceptance and remaining migration/browser/isolated gates stay pending.
