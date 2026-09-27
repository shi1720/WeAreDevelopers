# Tablekeeper local demo

This runbook covers the stage-3 experience. Closure planning and collective recurring
amendments are later-stage work and are not demonstrated here.
All people, restaurant names and account details below are synthetic fixtures.

## Start a fresh local demo

From the repository root:

```sh
docker build -t tablekeeper-stage3 ./stage-3
docker run --rm --name tablekeeper-demo -p 127.0.0.1:8080:8080 -e PORT=8080 tablekeeper-stage3
```

Open `http://localhost:8080`. The initial startup loads `stage-3/tablekeeper/demo.py`:

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
| Initial reservations | None |

The fixture is deterministic. Use 2035-06-14 for the walkthrough while that date is
in the future; after it passes, choose any future date. Booking past dates is allowed,
but cancellation still obeys the current-time cutoff. Restarting a fresh container
restores the initial fixture. A test reset/import replaces it; it is not silently reloaded.
`TABLEKEEPER_DEMO=0` starts empty instead.

## Three-minute walkthrough

1. **0:00–0:30 — Browse before signing in.** At `/`, choose The Orangery,
   2035-06-14 and 4 guests. Select **Find a table**. The small individual tables are
   visibly unavailable, while **Window nook + Garden table** offers a combined seating
   option. The restaurant's timezone is visible above the choices.
2. **0:30–1:00 — Sign in.** Open **Sign in** (`/login`) and use the synthetic account
   above. Alex appears in the header. New users can instead open `/signup`.
3. **1:00–1:40 — Keep a promise.** Repeat the search. Select the combined option at
   19:00, then **Confirm reservation**. The form stays visible and the confirmation
   names both tables, the restaurant, local time and unique reference. Click
   **Confirm reservation** again without editing: the server returns the same reference.
4. **1:40–2:20 — Make it a regular evening.** Follow **View your reservation** to
   `/lookup`. Show **The promise we kept** (policy 0, 90 minutes), then the immutable
   creation history. In **Make it a regular evening**, keep 4 visits and 1 week and
   select **Reserve regular visits**. Follow the agreement link. The original reference
   remains occurrence 1; all four visits have their own references. `/series` lists
   your agreements. Cancelling a visit from its lookup page cancels only that visit.
5. **2:20–3:00 — Show manager policy control.** Sign out and sign in as the demo
   manager. Open **For restaurants** (`/manager`), choose effective date 2035-06-14,
   change dining time to 120 minutes and publish. Policy version 1 appears. Explain that
   the guest's existing visits retain their accepted 90-minute terms. The manager cannot
   open another diner's private reservation history. Show the 375px layout if time permits.

For a focused resilience demonstration, run the automated browser cases below: they
exercise a competing booking, delayed search, and deliberately lost committed responses
followed by exact-body/key retries. Do not manufacture a successful uncertain response
in the product or imply this is a production deployment.

## Reproduce the browser failure checks

With Python and Playwright Chromium installed, from `stage-3`:

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
- The UI does not expose individual or batch amendments. The required amendment APIs
  remain available. Stage 3 adds policy publishing, accepted terms/history and recurring
  adoption/list/detail. Closure planning and collective recurring amendments are not yet
  available. A manager only sees restaurants assigned to that account.
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
