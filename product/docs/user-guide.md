# Tablekeeper pilot user guide

Tablekeeper keeps a small venue's bookings, accepted terms and seating changes together. This companion supports one venue per namespace, 1 to 6 tables and at most 4 declared pairs. It is intended for a small pilot, not unlimited scale or a service-level guarantee.

## First setup

The operator starts the configured service and supplies a high-entropy setup secret through a separate private channel. Open `/setup`. Enter that secret, the owner's name, email and password, then the venue name, IANA timezone, opening hours, start interval, dining duration and change deadline. Passwords need at least 12 characters.

Name each table and set its capacity. Select only the table pairs the venue can actually join. Check every value before creating the venue. Setup creates the owner and venue together and is consumed once. It cannot be reopened after restart. The secret is sent in the request body and is never stored by the browser application. Do not place it in a URL or screenshot.

Inventory and timezone are fixed after setup. Managers can publish effective-dated policies for later hours, capacities, intervals, duration and change deadlines. Existing bookings retain their accepted terms.

## Sign in and account care

Sign in with the account used to book. Browser authentication uses an HttpOnly cookie, not a browser-readable bearer token. Sign out using the header button. Pending recovery information remains isolated to its original account, so another signed-in account does not see or replay it.

Use **Account** to change your password. There is no email verification, automated password recovery or email delivery. Tablekeeper never pretends that it has sent a recovery email. If you lose access, contact the venue operator; this pilot does not provide a self-service owner password-reset screen. The operator must use a documented, identity-checked operational procedure rather than sharing another guest's account or editing live database records casually.

Sessions have a 12-hour absolute lifetime and a 2-hour inactivity timeout. Demo sessions also end when their 2-hour namespace expires. An expired session requires signing in again. These limits are server enforced; leaving a page open does not extend them through polling.

## Find and change a booking

1. Choose a restaurant, date and party size, then select an available table and time. Only declared pairs are offered as combinations.
2. Confirm the reservation. A booking is confirmed only after the server returns its reference.
3. Open **Your bookings** to find upcoming or past reservations without remembering a reference. Results are limited to 25 per page. **Find a reference** remains available.
4. Open a booking to see its accepted terms, revision and append-only history. To edit, choose a date and party size, load change options, and select an available table and arrival time.
5. Review the proposed policy before accepting and saving the change. The original booking's accepted change deadline controls eligibility. The save checks the current booking revision and seating together.

If someone changes the booking first, reload the current booking and review again. A failed save does not authorize presenting the proposed change as confirmed. Cancellation remains available on a confirmed booking, subject to its accepted deadline.

Times are interpreted in the venue's IANA timezone. Availability excludes nonexistent local times during daylight-saving gaps. The inherited convention uses the first occurrence of a repeated local time.

## An uncertain response

Before a material request is sent, the application saves its exact body and idempotency key in this browser's local storage, scoped to the signed-in account and namespace. It stores no password, setup secret or session credential there. This applies to booking, cancellation, individual editing, policy publication, recurring adoption/amendment and closure preview/apply.

If a response disappears, the server might still have committed it. Reloading restores the recovery panel. **Recover original result** submits the same body and key, including after a service restart. A different material change is blocked until recovery is settled. After recovery, follow the booking or agreement link to see current details; an exact historical receipt can predate later edits.

**Review discard options** is an explicit escape hatch. Discarding a retry does not undo a saved operation. Check your bookings, agreement or manager roster first. Then acknowledge the warning before discarding. A new request could otherwise duplicate an already-saved booking. Do not clear browser storage while an outcome is uncertain. If storage cannot be written, Tablekeeper refuses to send the change.

## Regular evenings

Open a confirmed booking and choose the number of visits and weeks between them. All visits are checked and reserved together. Each has its own reference and accepted terms. An individual edit or cancellation creates a permanent exception for that visit.

In **Regular evenings**, choose the starting visit and a new local arrival time. Review eligible and skipped visits. Amendment saves all eligible changes together or none. After success, the page reloads the agreement so the displayed visits reflect current saved times. A competing revision requires a refresh and another review.

## Run a service

Managers open **For restaurants**. The date roster shows operational booking information for their venue: arrival, guest name, party size, seating, status and reference. It does not provide other diners' account details or private histories. Choose a service date and load the roster again when needed; there is no aggressive polling.

To publish a policy, choose an effective date and enter the complete policy. Existing accepted terms stay unchanged. For new decisions, the latest applicable effective date wins, then the newest version on that date.

To close a table, enter the closure interval and preview a seating repair. Preview does not close the table or move bookings. Review the considered bookings, moves and preserved terms, then apply. The server commits the closure and seating changes together. A stale preview must be regenerated.

A closure plan considers at most **six overlapping confirmed bookings**, including bookings that do not move. The planner also supports at most six tables and four pairs. If a closure exceeds the bound, nothing is applied. Choose a genuinely smaller operational closure or handle the situation outside this pilot. Splitting a larger closure into separate plans does not establish globally correct combined seating.

## Scope and credits

No payments, SMS, external model calls or real email delivery are included. Hosted durable storage uses Firestore; local SQLite is a separate offline adapter. Deployment, backups, restore permissions and remaining hosted acceptance gates are documented in the operator documentation.

Shivam Gupta leads product direction and factory configuration. The Proofline Pilot coding seats implement and independently verify the companion. All demonstration data is synthetic.
