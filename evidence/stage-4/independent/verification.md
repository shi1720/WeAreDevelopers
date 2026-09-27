# Frozen Stage 4 independent review

Service revision `53617a341d21ebae3d76761f41b6ea4d38bc2a6c`; exact Git archive snapshot `/var/folders/vw/nb62dcpx661fyvd3p005p5jw0000gn/T/proofline-review-53617a3-t1c3935b`. Additional verifier tests were copied in; service/static files stayed frozen. Shared service/static diff against this revision was empty. Genuine predecessor servers used this revision's frozen stage1/2/3 folders. No known material specification violation remains from these checks; official coordinator gates and release acceptance remain pending.

| Check | Result | Duration | Exit |
|---|---|---|---|
| Independent HTTP, explicit modules |69/69|11.774s unittest;11.837s process|0|
| Same HTTP, network-none2CPU/2GiB |69/69|17.905s unittest;18.257s process|0|
| Genuine stages1–3 migration |3/3 sources|0.732s process|0|
| Inherited browser |7/7|5.113s process|0|
| Inherited product |3/3|1.379s process|0|
| New manager repair → guest amendment |Pass,375/1440|1.616s process|0|
| Author browser suite independently executed |16/16|9.526s unittest|0|
| Preliminary integrated replan/amend subset |13/13|5.080s unittest|0|

Host Python `/tmp/proofline-official-spec/.venv/bin/python` is prepared3.12. Each archived service started using `PORT=<ephemeral> <python> -m tablekeeper.server` in its stage directory. Tests set `TABLEKEEPER_BASE_URL=http://127.0.0.1:<ephemeral>`; migration/browser scripts also set `TABLEKEEPER_STAGE1_URL`, `TABLEKEEPER_STAGE2_URL`, `TABLEKEEPER_STAGE3_URL` to genuine disposable source services. No shared live service reset.

Exact API command, cwd archived stage-4/tests:

```sh
/tmp/proofline-official-spec/.venv/bin/python -m unittest independent_contract independent_boundaries independent_combinations independent_review independent_policies independent_series independent_deep independent_import_relations independent_replans independent_series_amend independent_stage4_edges -v
```

Exact script commands, cwd archived stage-4:

```sh
/tmp/proofline-official-spec/.venv/bin/python tests/independent_stage4_upgrade.py
/tmp/proofline-official-spec/.venv/bin/python tests/independent_browser.py
/tmp/proofline-official-spec/.venv/bin/python tests/independent_product.py
/tmp/proofline-official-spec/.venv/bin/python tests/independent_stage4_product.py
/tmp/proofline-official-spec/.venv/bin/python -m unittest discover -s tests -p test_browser.py -v
```

Offline commands:

```sh
docker build --pull=false --network=none -t proofline-verifier-stage4:53617a3 /var/folders/vw/nb62dcpx661fyvd3p005p5jw0000gn/T/proofline-review-53617a3-t1c3935b/stage-4
docker run -d --name proofline-verifier-stage4-offline-53617a3 --network none --cpus 2 --memory 2g proofline-verifier-stage4:53617a3
docker cp /var/folders/vw/nb62dcpx661fyvd3p005p5jw0000gn/T/proofline-review-53617a3-t1c3935b/stage-4/tests proofline-verifier-stage4-offline-53617a3:/checks
docker exec -w /checks proofline-verifier-stage4-offline-53617a3 python -m unittest independent_contract independent_boundaries independent_combinations independent_review independent_policies independent_series independent_deep independent_import_relations independent_replans independent_series_amend independent_stage4_edges -v
docker rm -f proofline-verifier-stage4-offline-53617a3
```

Build exit0,0.795s. Runtime/image recorded in offline-runtime.json: network none, NanoCpus2000000000, Memory2147483648, no proxy environment keys. Test files alone copied into container. Initial bind-mount run failed exit125 because Colima could not resolve the host temporary directory; recovered with docker cp. No restrictions relaxed.

## Preserved failures

- backend-7045048-failed.log: revision `70450487b1b9ef4baec8cb2ae134af21ee5ae083`,12/13 pass,4.611s,exit1. Server passed closures keyword to incompatible committed availability signature, returning400. Cleared on frozen integration.
- extended-checks.log:96 executions,16.569s,exit1. Two test setup errors: scheduled_date belongs to private state, not public series output; adoption after cutoff correctly fails. Corrected to compare private membership and acquire stricter cutoff through a prior collective amendment. Discovery also duplicated inherited cases via imported test classes; final explicit69-case run avoids this.
- edges-02.log: corrected5 edge checks pass,0.892s,exit0.
- api-final.log:68/69 pass,11.738s,exit1. A new conflict test selected22:00 with120-minute duration exceeding23:59 closing; expected nonoccupancy error correctly won. Corrected to21:30; final69/69 pass.
- stage4-product.log:exit1,31.503s. Test used `/series/<id>` instead of public `/series?series_id=<id>`. Corrected script passes; service unchanged.

## Coverage and limitations

See docs/coverage-stage-4.md for clause matrix. Source review confirmed one-lock serialization and isolated candidate publication on success, accepted-capacity lexicographic planner, full-span conflicts, import receipt/provenance cross-checks, and amendment nonoccupancy validation before occupancy. Independent oracle enumerates24 seeded fixture spaces; it is not a proof over all possible inputs. Oversized planning rejection was source-reviewed but not separately executed.

Manager screenshots375/1440 and series375 were visually inspected: readable labels, no horizontal overflow. After amendment the original summary remains until explicit “View updated visits”/refresh; success and retained original retry revision coexist. This is a UX limitation, not a blocking contract finding. Screen-reader and other browser engines not audited. Python3.14's externally reported24:00 parsing difference remains a portability limitation; review and deployment use3.12. Exports/tokens remain in memory; service logs were not copied into evidence.

Official stage1–4 host/isolated and final clean-clone gates belong to the coordinator and remain pending. This report is independent evidence, not release acceptance.
