# Try Tablekeeper

Deployment status: pending live verification. These are the intended hosted test steps, not a claim that the reserved address is already serving the app.

The public demonstration uses made-up guests and an isolated data space for each browser session. You do not need an API key or a shared password. Do not enter real guest information. A demo expires after two hours; expired data is scheduled for hourly cleanup. The service retains at most 100 demo spaces, including expired spaces awaiting cleanup.

## The three-minute promise test

1. Open the live app, choose **Start a private demo**, then **Create synthetic demo**. You begin as the synthetic guest.
2. Open **Your bookings** and inspect **EVENING1**. It is for two guests at **Window nook**, on **14 June 2035 at 19:00**, in **Europe/London**. Note the arrival time and accepted terms.
3. Open **Demo controls**, then **Explore as manager**. In **For restaurants**, load the roster for **14 June 2035**.
4. In the closure form, choose **Window nook**, **14 June 2035 at 19:00** through **21:00**. Choose **Preview repair**. Expect one proposed move among three considered bookings, with zero unused seats after repair. A preview has not changed any booking.
5. Choose **Apply seating repair** and wait for confirmation. Return through **Demo controls** to **Explore as guest**.
6. Inspect **EVENING1** again. Its seating is now **Garden table**. Arrival time, party size and accepted terms are preserved. Its history records the reassignment.

Use a fresh demo for this exact seeded scenario. If you have already changed its bookings, **Reset this demo** and confirm **Reset my synthetic demo** first. Reset affects only your synthetic space.

## Explore everyday work

- **Book and edit:** use **Find a table**, choose a future date and party size, select an available time and table, then confirm. Find the result in **Your bookings**, load change options, review the proposed terms and save an amendment. Success requires a server confirmation.
- **Regular visits:** open a confirmed booking, choose a number of visits and the interval in weeks, then reserve them together. In **Regular evenings**, amend eligible visits and inspect the refreshed saved summary. Individually changed visits remain exceptions.
- **Manager view:** switch to the manager inside your demo, load the relevant date roster and inspect the service. Policy changes apply to future decisions while existing accepted terms remain visible.
- **Visitor isolation:** start another demo in a separate private/incognito browser context. A newly created booking from the first visitor must not appear in the second visitor's roster or lookup. Seeded references exist separately in each demo, so use a new booking for this check.
- **Sign out:** use **Sign out**. The previous server session is revoked. Begin a new synthetic demo to continue exploring; there is no shared demo password to reuse.

## Recovery and operating limits

If a response is uncertain, keep the saved request and choose **Recover original result**. An unchanged retry uses its original key and body. Discarding a pending request does not undo a server-side success. The automated browser evidence covers deliberately lost committed responses, page reloads, account switches and service restarts; a normal refresh alone does not reproduce that fault.

The planner supports six tables, four declared pairs and six overlapping confirmed bookings. The hosted companion uses Firestore and requires Google API access. The original graded stage folders are separate offline services. Cloud transaction failures can require a pause and an unchanged retry; the database may retain an abandoned transaction lock after a process stops.

For local setup, real account login, password changes, backup and restore, follow the [operator guide](../product/docs/operations.md) and [user guide](../product/docs/user-guide.md). Public demo roles and resets are confined to synthetic data. No payment, SMS or email delivery is configured.
