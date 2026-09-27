# Experience implementation and author verification

Product source tested: `48c45d0b63bc7c4e6aba582b381e7be5262ca3ff` in isolated detached checkout `/Users/shivamgupta/.cache/tablekeeper-experience-48c45d0`. Browser driver: `cbd4ef3b39e3574699116fb1975409f754e62864`. Only the corrected test driver was copied into that checkout; implementation files remained at the product revision. Generated evidence made its Git status dirty and is reported separately. This is author verification, not Verifier's independent acceptance.

Full browser command:

```sh
/tmp/proofline-official-spec/.venv/bin/python product/tests/experience_run.py /tmp/proofline-official-spec/.venv/bin/python product/tests/experience_browser.py
```

Final result: five tests passed, exit 0, measured 8.807323583998368 seconds. Exact source context and full output are in `20260927T185447568121Z.json` and `.log`. Focused recovery boundary command `node product/tests/experience_recovery.cjs` passed 26 checks in 0.1229947079991689 seconds, exit 0, recorded in `20260927T185328673515Z.json` and `.log`.

| Requirement | Implemented behavior | Executed author evidence |
| --- | --- | --- |
| Safe one-time setup | Owner/venue form, IANA timezone, hours, initial policy, 1-6 labelled tables, <=4 declared pairs; secret never persisted | Real setup on fresh SQLite store; desktop/mobile captures; HttpOnly cookie assertion |
| Cookie and CSRF boundary | Server session boot, same-origin cookies, header CSRF, no browser bearer credential | Real signup/login/logout; absent old credential storage; wrong CSRF 403 and revoked session 401 retain pending request |
| Account care | Password-change form and server logout; honest absence of email recovery | Implemented and source reviewed; password-change browser flow remains independently verified outside this author suite |
| Owner booking list | Upcoming/past, 25-row pagination, labels/timezone, reference lookup retained | Booking appears without reference input; real detail navigation and 1440/375 inspection |
| Individual edit | Owner-excluded availability, proposed terms, explicit accept, revision/CAS keyed PATCH | Real table/time edit; keyboard Enter activates confirmation; current saved detail and manager roster reflect it |
| Narrow manager roster | Venue/date scoping, 50-row pagination, operational fields only | Real date roster with synthetic guest, booking reference/time/table; desktop/mobile captures |
| Existing recurring/closure flows | Preserved adoption/history/terms/policies/repair; series summary refreshes after amendment | Real adoption, changed visits show updated times; closure preview and atomic apply complete |
| Persistent uncertain request | Exact body/key saved before send, one material request per account, explicit recover/discard, storage failure refuses send | Real dropped committed booking response, reload and real service restart, exact request tuple replay and one booking; 26 boundary checks |
| Material amendment/repair recovery | Same recovery layer protects series amendment and closure application | Both committed responses dropped, browser reloaded, server restarted, original body/key recovered; updated series rows checked |
| User and demo reset isolation | Opaque scope required, stable across reauthentication, reset generation distinct | Different account sees no original pending attempt; original owner recovers after login; reset hides old namespace-generation attempt |
| Presentation and CSP | Cream/forest/terracotta identity, labelled controls, external styles, no new em dashes | 1440px and 375px screenshot inspections, no horizontal overflow assertions, zero page exceptions and CSP console errors |

## Repair evidence retained

- Initial three integration timeouts predated canonical route alignment and remain in `checks.json`.
- `20260927T183900450221Z`: setup/demo routes aligned; two driver waits incorrectly expected native `<option>` visibility. Corrected to attached-state wait. Its early recorder field `immutable_acceptance: true` meant only clean Git status at start and does **not** represent independent acceptance. Later recorder fields separate `clean_at_start` and `independent_acceptance`.
- `20260927T184012186775Z` and `20260927T184058225464Z`: lowercase idempotency header lost by backend forwarding; product defect independently confirmed and repaired by Engineer. No test header capitalization workaround was used.
- `20260927T185321354750Z`: booking recovery passed; reset assertion raced navigation and material-operation status incorrectly expected 200. Corrected navigation wait and exact inherited 201 expectation in driver commit `3c3f73c`.
- `20260927T185359960385Z`: reset isolation passed; series assertion ran before asynchronous refresh rows arrived. Added row wait without changing expected count/time in driver `cbd4ef3`.
- `20260927T185426614516Z`: corrected amendment/repair recovery passed before the full five-case run.

No failed log or original author commit was rewritten. No implementation edits were made after the freeze for these driver corrections.

## Visual evidence

All PNGs here contain synthetic data only. Inspected setup, booking list, edit review, manager roster, recurring updated summary, closure preview and restart recovery at 375px, plus desktop setup/list/roster/recurring/closure at 1440px. Forms, cards and recovery actions remain within the viewport; typography and the original color system are preserved. Screenshot hashes and source/driver revisions are in `screenshots.json`.

## Scope and limits

Owned implementation: `product/static/**`, `product/docs/user-guide.md`, `product/docs/demo.md`; owned tests: `product/tests/experience_*`; owned evidence: this directory. Backend, storage, deployment and independent acceptance remain other seats' responsibilities. This author suite does not claim deployed Cloud Run/Firestore, Firestore emulator, exhaustive security/accessibility certification, load capacity, backup/restore or original official harness acceptance. Those gates belong to the combined independent release evidence. No cloud account, real guest data or provider secret was used.

Shivam Gupta leads product and factory direction. Proofline Pilot Experience authored the scoped UI and these tests; the configured Engineer and Verifier seats own their separately attributed work. No known remaining scoped UI implementation defect was identified at this handoff.
