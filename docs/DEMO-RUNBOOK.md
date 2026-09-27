# Tablekeeper local demo

This runbook currently covers the completed stage-2 experience. Manager policies,
recurring bookings and closure planning are later-stage work and are not demonstrated here.
All people, restaurant names and account details below are synthetic fixtures.

## Start a fresh local demo

From the repository root:

```sh
docker build -t tablekeeper-stage2 ./stage-2
docker run --rm --name tablekeeper-demo -p 127.0.0.1:8080:8080 -e PORT=8080 tablekeeper-stage2
```

Open `http://localhost:8080`. The initial startup loads `stage-2/tablekeeper/demo.py`:

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
4. **1:40–2:20 — Find and cancel.** Follow **View your reservation** to `/lookup`,
   or enter the reference on **Your reservation**. Show the confirmed status and both
   table names. Select **Cancel reservation**; status becomes `cancelled` and the
   cancellation button disappears. Returning to search makes both tables available again.
5. **2:20–3:00 — Show the experience and evidence.** Resize to 375 CSS pixels. The
   search controls, seating cards and booking form stack without horizontal page scroll.
   Explain that automated browser checks exercise a competing booking, delayed search,
   and a deliberately lost response followed by import and an unchanged retry. Do not
   simulate a successful uncertain response in the product or imply this is a production
   deployment.

## Reproduce the browser failure checks

With Python and Playwright Chromium installed, from `stage-2`:

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
- The stage-2 UI does not expose batch amendments. The required atomic batch API remains
  available. No manager policy, series or closure UI is claimed at this stage.
- All illustrations, styles and scripts are local; typography uses installed system
  Georgia and Arial fallbacks. There are no runtime font or asset downloads.

## Development evidence

The first focused browser run completed in 3.837 seconds and exposed two mistakes in
the test driver: an unquoted CSS attribute value containing a colon and a positional
argument where Playwright requires `arg=`. That run reported two errors and one related
teardown failure. Both driver mistakes were corrected without weakening assertions.
The next run passed all five scenarios in 3.779 seconds. The expanded seven-scenario
suite passed in 4.789 seconds, adding changed-body identity and paired uncertain recovery.
Availability passed seven
tests in 0.004 seconds. These are local development results, not independent release
acceptance. The verifier's immutable revision and official isolated results govern release.
