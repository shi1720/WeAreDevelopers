# Independent verification findings

Original candidate: `70cf83c8de4c67babab92973264913c2ccc7b984`, rejected. Original results below remain unchanged as historical evidence. Final repaired source candidate is `d6194c8c9575f0a6b85ec2a322e8a65cbb9af740`, executed from a fresh local clone. Python3.12.14 and candidate hash-locked requirements, including Firestore2.21.0. Later driver revisions are separately recorded in each run JSON. Final disposition is in final-report.md.

| Finding | Evidence and result | Disposition |
|---|---|---|
| V01 operational validation | Valid-checksum envelope with `maintenance: "locked"` is accepted by decode; expected supported object/None validation. `acceptance_storage.py::test_operational_schema_corruption_rejected`, original full run 39pass/2fail. | Fixed1455368 and later schema hardening; independent regressions pass in final repaired run. |
| V02 HTTP header casing | Lowercase, uppercase and mixed-case Idempotency-Key each return400 missing_idempotency_key for valid booking. HTTP names are case-insensitive; `dict(headers)` in Companion loses that behavior. Three direct regressions failed. | Fixedeb9e521; all three regressions pass in final repaired run and browser recovery. |
| V03 proxy total body deadline | Four POST clients send a byte every4s; all remain open after24.036s because nginx buffers before bounded backend. Healthy booking still succeeds0.015s. Proxy idle5s does not enforce backend15s lifetime. | Fixedeb9e521 streaming; eight body/header tricklers close within24s and healthy booking14ms. Proxy configuration unchanged in final candidate. |
| V04 missing storage metadata | On30f1bbe, five unsupported SQLite schema/revision cases are accepted and Firestore root deletion leaves chunks but reports absent state. Six independent failures preserved. | Coordinator/author review prompted hardening8d00205; all six independent regressions pass in final repaired run. |
| V05 malformed setup owner | On30f1bbe, null/list owner reaches throttle label extraction and returns500 instead of bounded validation. Two failures preserved; five other invalid setup boundaries pass. | Fixed8d00205; all seven setup boundary tests pass in final repaired run. |

## Preserved test-driver corrections

- Initial Firestore counter test required all contended calls to succeed immediately. SDK exhausted five retries and safely returned StoreError, which the dispatch explicitly permits. Corrected driver gives each operation a stable identity, retries boundedly after unknown outcome and verifies20 distinct effects/revisions. Corrected check passed10.811174s. Original failure remains preserved; this correction does not establish full domain receipt correctness by itself.
- Initial browser lost-response forwarding returned400. A framing-header hypothesis prompted a driver change, but the error remained and exposed missing_idempotency_key. Direct case-variant tests confirmed V02. The framing hypothesis was incorrect, not an application repair. Both failed browser logs/commits remain intact.
- A driver edit briefly moved the password restart assertion into the new header test. Corrected before execution in separate commit382ff8c. No result from that unexecuted intermediate version is claimed.
- Playwright string evaluation for readiness was blocked by the application's CSP. Corrected to a locator wait without disabling CSP. Material-action recovery then passed.
- Demo expiry fixture initially changed only namespace expiry, leaving the cleanup registry live. Corrected both authoritative fixture timestamps; synchronous access denial and bounded cleanup then passed.
- Stricter configured-state validation made the old test marker `setup_consumed=True` invalid on an empty domain. Changed storage-only mutations to a neutral `acceptance_probe`; kept invalid schema assertions intact.
- A killed Firestore emulator transaction retained a lock for about60 seconds. Immediate and40-second recovery attempts failed. A diagnostic stable-key retry succeeded after60.96 seconds; the HTTP crash driver now retries the identical request boundedly across this interval. No reset or state deletion was used. This is an emulator observation, not deployed latency evidence.
- Browser series recovery asserted occurrence count immediately after the success banner, before the asynchronous refresh completed. Driver9f9de0f waits at most8 seconds for exactly two updated20:00 visits; the unchanged UI passed3.071293 seconds and was visually inspected.
- In final repaired two-process execution an unknown503 had already committed. Exact retries both returned200. Driver6e74d8e permits this only after observed503, retains receipt equality and one-effect assertions, and adds replay through both live processes. Original failing87-pass run remains preserved.

## Results already independently executed

| Gate | Result | Measured duration | Log prefix |
|---|---|---:|---|
| Storage, both adapters | 39pass,2fail as above |21.894984s|20260927T183933481034Z|
| Canonical HTTP |8pass|4.168789s|20260927T183933482996Z|
| Exact-candidate image build |exit0|2.721141s|20260927T183933485988Z|
| Corrected contention recovery |1pass|10.811174s|20260927T184201615127Z|
| Offline container/volume |exit0|2.701194s|20260927T184345467244Z|
| Real browser |setup/booking/list/edit/roster pass; lost-response blocked byV02|11.695066s|20260927T184201614904Z|
| Proxy trickle |failV03|24.865434s|20260927T184514627834Z|
| Header casing |3failV02|1.339680s|20260927T184621281282Z|
| Two-process Firestore HTTP |2pass|6.908616s|20260927T184854402490Z|
| Companion domain HTTP |5pass|2.431530s|20260927T184906020959Z|

Container image `sha256:43aff15ed555d9569b96c1a28e5247901dd746f11eac0f026313ee929adb5070` ran as65534:65534, network none,2CPU/2GiB. Actual setup, booking, policy, recurring adoption/amendment and closure application survived volume restart and backup/restore into a separate volume with exact original receipts and current identity/history/series comparisons. Proxy oversized body/header errors had private,no-store. Author image was not reused as acceptance identity.

Real Chromium screenshots under `screenshots/70cf83c` show synthetic data only. Automated no-overflow checks passed1440/375 for setup, confirmation, booking list, edit terms and roster. Verifier visually inspected desktop setup/confirmation and mobile edit/roster: typography, labels and action hierarchy remained legible; no clipping observed. At that original run, closure, recurring summary and recovery/account-switch flows were pending. They subsequently passed on repaired candidates, including final-d6194c8.

The table above records original70 execution only. Later repaired runs, screenshots and final disposition are in final-report.md and runs/*.json. Coverage.md distinguishes executed subsets, source review and remaining permutations. Production deployment, real Cloud IAM/Hosting forwarding and provider billing remain operator gates.
