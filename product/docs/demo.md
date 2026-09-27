# Synthetic demonstration

The public demo is an explicit operator opt-in through `TABLEKEEPER_PUBLIC_DEMO=1`. Missing production data never enables it. Follow the operator start instructions with this setting, open `/demo`, and select **Create synthetic demo**. No cloud resources need to be created to run the local SQLite demonstration.

Each visitor receives a cryptographically random isolated namespace, bound to a server session. The demo uses made-up `.test` accounts. Never enter real guest data. The demo is labelled on every page and expires after two hours. Do not use it for a real venue's service book.

## Walkthrough

1. Start a private demo. Search The Orangery for **14 June 2035** to explore the seeded evening. Choose a free table and confirm a booking.
2. Open **Your bookings**, select a booking and inspect accepted terms and history. Search for a changed arrival or party size, review its proposed terms, then save.
3. Adopt a confirmed booking into regular visits. Open **Regular evenings**, amend eligible visit times and check the automatically refreshed summary.
4. Open **Demo controls** and choose **Explore as manager**. Load the date roster for **14 June 2035**. Preview a table closure over that evening, review the complete plan and apply only after the server confirms a feasible plan.
5. Open a separate incognito browser context and create another demo. Its bookings, roster, history and plans are separate. Copying a reference or plan does not grant access to another visitor's namespace.
6. Choose **Reset this demo**, read the warning, then **Reset my synthetic demo**. Only this visitor's synthetic namespace is reset. Role switching remains inside this visitor's demo.

## Recovery demonstration

Automated browser evidence deliberately lets the server commit a material request, drops the response, reloads the page and restarts the service against the same durable store. The restored recovery panel retries the original request body and key, recovering the original receipt instead of creating another booking. This is a test-only response interception, not a production fault endpoint.

To explain recovery interactively, point out the recovery panel and its explicit discard warning. Do not claim a successful booking until a real response has confirmed it. Switching users hides the original user's pending request; signing back in restores it.

## Boundaries

The venue limit is 1 to 6 tables and at most 4 declared pairs. Closure planning considers at most 6 overlapping confirmed bookings. Demo lifetime and storage are bounded; expiry can require a fresh demo. This pilot has no payments, SMS or email delivery. The demonstration is not evidence of unlimited scale, an SLA or security certification.

The operator provisions and deploys the Google Cloud project after acceptance. Firebase Hosting plus Cloud Run requires billing and is not a promise of zero cost. Deployed Firestore acceptance remains a separate operator gate. This room does not publish a site or use provider credentials.
