# Stage 4 experience author verification

Implementation revision: `98abd1cd5262ac684c4c17a35d1553786691020d`.
This is author evidence against the concurrent, mutable Stage 4 backend, not an
independent acceptance or exclusive-snapshot claim. Earlier stage folders were not edited.

## Commands and outcomes

Working directory: `/Users/shivamgupta/Downloads/we-are-developers/stage-4`.
Interpreter: `/tmp/proofline-official-spec/.venv/bin/python`.
Durations below are unittest-reported elapsed durations.

| Command after interpreter | Exit | Duration | Result |
| --- | --- | --- | --- |
| `-m unittest discover -s tests -p test_availability.py -v` | 0 | 0.003s | 11 passed |
| `-m unittest discover -s tests -p test_browser.py -v` (initial integration) | 1 | 27.835s | 13 tests; 3 errors and 1 teardown failure |
| `-m unittest tests.test_browser.BrowserTests.test_series_amend_lost_response_and_refresh -v` | 0 | 2.072s | 1 passed after correcting status expectation |
| `-m unittest tests.test_browser.BrowserTests.test_series_stale_revision_and_cancelled_eligibility -v` | 0 | 1.557s | 1 passed |
| `-m unittest discover -s tests -p test_browser.py -v` (corrected integration) | 0 | 8.929s | 15 passed |
| `-m unittest tests.test_browser.BrowserTests.test_deterministic_demo_and_accessible_preview -v` | 0 | 1.158s | 1 additional demo/visual case passed |

The last command used `TABLEKEEPER_SCREENSHOTS=/Users/shivamgupta/Downloads/we-are-developers/evidence/stage-4-experience`.
Desktop 1440px and mobile 375px full-page PNGs were inspected visually. The manager
workspace remains readable with wrapped controls, a two-column mobile table map and
no horizontal overflow. Visible fields have programmatic labels and Apply is keyboard
focusable. The synthetic demo produces three considered bookings, one move from
Window nook to Garden table, and zero unused seats; application succeeds.

## Preserved integration failures

The first browser run timed out waiting for two closure previews: the backend helper
had changed from the agreed `{plan,reservations}` envelope to flattened preview fields
plus `before_reservations`. The UI now normalizes both observed shapes. The recurring
lost-response interceptor incorrectly expected 200 for a new write; the specification
requires 201. That assertion also caused the teardown failure. The test now expects
201 before dropping the committed response. No server success was fabricated.

## Owned clause coverage

| Requirement | Implementation and verification |
| --- | --- |
| Half-open closures exclude singles and pairs; other restaurants remain unaffected | `availability.py`; focused closure tests, exact-end boundary and independent `no_overlap` explanations |
| Preserve booking promises while reviewing repair | `repairs.js`; before/after tables, unchanged time/party/terms, moved count, unused seats and all considered records |
| Preview purity and empty plan | Preview uses preview route; zero-booking preview tested; backend atomicity remains Engineer/Verifier scope |
| Explicit-offset closure inputs in restaurant timezone | Local-time conversion; browser checks Berlin normal time, first fold occurrence and rejection of gap |
| Stale and impossible plan recovery | Real competing booking, stale Apply, fresh preview and impossible large-party closure |
| Exact uncertain preview/apply retry | Drop successful 201 response; compare body and key on retry; render success only after confirmed server response |
| Recurring amendments and revision recovery | Owner screen, starting index, local time, eligibility list, stale revision and explicit refresh |
| Cancelled/exception visibility | Eligibility explicitly marks cancelled and exception visits; real cancelled-visit skip verified; independent exception API coverage belongs to Verifier |
| Atomic amendment uncertainty | Drop successful amendment response, retry exact revision/body/key; refreshed agreement shows revision 2 |
| Inherited experiences | Existing 10 booking/policy/series browser cases still pass |
| Demonstration assets | Deterministic synthetic fixture, three-minute runbook, actual desktop/mobile screenshots |

Limits: retry identity survives within the open page, not reload; the UI offers one
closure per preview and surfaces backend planning bounds. The optimizer, transaction
atomicity, imports and concurrency require independent verification. No real customer
data, bearer tokens or exported credentials were saved in these artifacts.
