# Tablekeeper local demo

This runbook describes the stage-4 closure-repair scenario and recurring amendments.
Final execution evidence and independent acceptance are recorded separately below.
All people, restaurant names and account details below are synthetic fixtures.

## Start a fresh local demo

From the repository root:

```sh
docker build -t tablekeeper-stage4 ./stage-4
docker run --rm --name tablekeeper-demo -p 127.0.0.1:8080:8080 -e PORT=8080 tablekeeper-stage4
```

Open `http://localhost:8080`. The initial startup loads `stage-4/tablekeeper/demo.py`:

| Fixture | Value |
| --- | --- |
| Restaurant | The Orangery (`the_orangery`) |
| Timezone | Europe/London |
| Hours | Every day, 17:00–23:00 |
| Grid / duration / cancellation cutoff | 30 / 90 / 60 minutes |
| Window nook / Garden table | 2 seats each; declared pair, 4 seats together |
| The round table / Quiet alcove | 4 / 6 seats; declared pair, 10 together |
| Demo guest | Alex, `guest@tablekeeper.test` |
| Demo password | `a lovely evening` — deliberately public synthetic demo credential |
| Demo manager | Sam, `manager@tablekeeper.test`, password `a thoughtful service` — also public and synthetic |
| Initial reservations, 2035-06-14 | `EVENING1`: Window nook, 19:00, 2 guests; `FRIENDS1`: The round table, 19:00, 4 guests; `LATER001`: Garden table, 20:30, 2 guests. All belong to demo guest Alex. |

The fixture is deterministic. Use 2035-06-14 for the closure walkthrough; operator
repairs work even after a diner's cutoff. For guest cancellation or recurring amendments,
use a future reservation if that date has passed. Restarting a fresh container
restores the initial fixture. A test reset/import replaces it; it is not silently reloaded.
`TABLEKEEPER_DEMO=0` starts empty instead.

## Three-minute walkthrough

1. **0:00–0:35 — A booking is a promise.** Sign in as the demo guest at `/login`.
   Open `/lookup`, enter `EVENING1`, and show Window nook, 19:00, 2 guests, policy 0
   and 90 minutes. The current guest history contains the original creation.
2. **0:35–1:00 — The floor changes.** Sign out and sign in as the demo manager.
   Open **For restaurants** (`/manager`). In the closure workspace, choose Window nook,
   2035-06-14 from 19:00 until 21:00. Times are Europe/London, not the browser's timezone.
3. **1:00–1:45 — Review the smallest safe change.** Select **Preview seating repair**.
   Expect three considered bookings and exactly one move: `EVENING1` from Window nook
   to Garden table. `FRIENDS1` and `LATER001` stay put. The first Garden visit ends at
   20:30, exactly when `LATER001` begins. Unused seats total 0. Preview changes nothing.
4. **1:45–2:15 — Keep the promise atomically.** Select **Apply seating repair**.
   The success state appears only after the server confirms. All guests keep their
   original references, arrival times, party sizes and accepted terms. The Window nook
   closure now prevents new overlapping reservations.
5. **2:15–3:00 — Show the guest's truth.** Sign out and back in as Alex. Look up
   `EVENING1`: Garden table, still 19:00 and 2 guests, still policy 0 and 90 minutes.
   The history adds one seating-reassignment event. Briefly show the responsive manager
   view or explain the automated stale-plan, impossible-plan and lost-response checks.

Optional recurring demonstration: from a confirmed future reservation's lookup, adopt
three weekly visits, then open **Regular evenings**. Choose a starting visit and new
local time. The amendment panel lists eligible and skipped visits. Submit once; all
eligible changes commit together. If another edit changes the agreement revision,
**Refresh agreement** loads current eligibility before a new attempt.

For a focused resilience demonstration, run the automated browser cases below: they
exercise a competing booking, delayed search, and deliberately lost committed responses
followed by exact-body/key retries. Do not manufacture a successful uncertain response
in the product or imply this is a production deployment.

## Reproduce the browser failure checks

With Python and Playwright Chromium installed, from `stage-4`:

```sh
python -m unittest discover -s tests -p test_browser.py -v
python -m unittest discover -s tests -p test_availability.py -v
```

The browser suite starts its own local service on an available port and installs an
arbitrary synthetic fixture. It exercises real HTTP behavior with browser routing used
only to delay or drop responses. Lost-response recovery submits the identical body and
idempotency key after export/import; a successful server response is required before
displaying confirmation. Exported credentials remain in memory and are not written to disk.

## Deployment limits

- Judge images enable unauthenticated `/_test/reset`, `/_test/export` and `/_test/import`
  by default. The command above binds localhost only. Never expose that configuration
  publicly. `-e TABLEKEEPER_TEST_CONTROLS=0` disables all test controls; disabling them
  alone does not make this hackathon image production-ready.
- Demo account details are public. Do not use the demo account to hold real personal data.
- Data is in memory and a container restart loses changes. There is no email delivery,
  password reset, payment, cross-tab synchronization or recovery of a pending booking
  after a page reload. Sessions are stored in this browser's local storage.
- A changed form is a new booking request. An unchanged form retries its existing key
  and body. If the response is uncertain, retry unchanged before making another booking.
- The UI does not expose ordinary individual or batch reservation amendments. Those
  required APIs remain available. Manager policies, guest history/terms, recurring
  adoption/list/detail and recurring time amendments have screens. A manager only sees
  restaurants assigned to that account. Closure planning supports the specified bounded
  problem, not an unlimited restaurant optimizer.
- All illustrations, styles and scripts are local; typography uses installed system
  Georgia and Arial fallbacks. There are no runtime font or asset downloads.

## Stage-2 development evidence retained

The first focused browser run completed in 3.837 seconds and exposed two mistakes in
the test driver: an unquoted CSS attribute value containing a colon and a positional
argument where Playwright requires `arg=`. That run reported two errors and one related
teardown failure. Both driver mistakes were corrected without weakening assertions.
The next run passed all five scenarios in 3.779 seconds. The expanded seven-scenario
suite passed in 4.789 seconds, adding changed-body identity and paired uncertain recovery.
Availability passed seven
tests in 0.004 seconds. These are local development results, not independent release
acceptance. The verifier's immutable revision and official isolated results govern release.

## Stage-3 development evidence

Crossed interface proposals initially left the server passing `policy=` while availability
expected an already-effective restaurant. The seats explicitly settled on the keyword
contract, and availability now uses the shared policy helpers. The integration also exposed
a missing cutoff field in the small availability unit-test fixture (seven errors in 0.001
seconds); adding the required fixture field restored all nine checks (0.004 seconds).
The first ten-scenario browser run passed nine and failed the final series-list navigation
check in 13.251 seconds: direct series detail worked, but the agreed optional list API was
not yet integrated. This failure was sent to the backend owner rather than hidden by
removing the list assertion.

The final list contract is an authenticated, owner-only `GET /api/series`; `/series`
remains the HTML screen and `/series/{id}` remains the specified private detail API.
After backend integration, all ten browser scenarios passed in 5.984 seconds (exit 0).
Engineer separately reported the complete 61-test local suite passing in 13.076 seconds.
Manager layouts were visually inspected at desktop and 375px; measured document width
at the mobile viewport was exactly 375px. Independent acceptance remains a separate gate.
