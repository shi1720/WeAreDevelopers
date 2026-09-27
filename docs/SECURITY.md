# Security and deployment boundaries

Tablekeeper is a hackathon service under a precise test contract. It is not certified or represented as internet-production-safe.

The judge image must enable unauthenticated `/_test/reset`, `/_test/export` and `/_test/import` by default. These controls can replace all application state or disclose credentials and sessions. Keep judge containers on loopback or the harness's isolated network. Any public demo must explicitly disable all test controls using the hardened mode documented in the relevant stage's RUN.md; public exposure is not part of this production dispatch.

Exports are private artifacts. They include password hashes and can include active bearer tokens; never commit them, paste them into the room or include them in public test logs. Tests should report assertions and counts without printing tokens. A reset/import invalidates destination credentials by replacing state as required; an accepted import preserves source sessions and original retry receipts.

Passwords must use an appropriate password-hashing function. Reservation lookup and mutations remain owner-scoped. Manager permissions apply only to the expressly authorized restaurant operations, and do not confer access to another diner's private records. Browser assets are local, and runtime operation must not require internet services.

The contract allows nonexpiring tokens and ephemeral disk state. Email verification, password resets, refresh tokens, production abuse prevention, audited backups, disaster recovery and certification are outside the required service. Persistence, if provided by an implementation, does not itself establish these properties. Consult each stage's RUN.md and the final verification report for implemented controls and measured limitations.

Synthetic demonstration accounts are intentionally public local-demo fixtures. They must never reuse a real person's email/password or provider credentials.
