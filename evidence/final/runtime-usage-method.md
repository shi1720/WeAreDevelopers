# Runtime usage accounting

Fixed snapshot sampled **2026-09-27T18:02:01.565269+00:00**, after coordinator acceptance. [Sanitized counters](runtime-usage-sanitized.json) retain the exact eight provider-session IDs, per-epoch event timestamps and selected counters. No raw messages, tool payloads, credentials or private filesystem paths are published.

| Seat | Input | Output | Total |
|---|---:|---:|---:|
| Coordinator | 33,364,251 | 50,284 | 33,414,535 |
| Engineer | 28,544,052 | 92,747 | 28,636,799 |
| Experience | 20,571,640 | 75,941 | 20,647,581 |
| Verifier | 36,627,586 | 116,658 | 36,744,244 |
| **Total** | **119,107,529** | **335,630** | **119,443,159** |

Cached input **116,797,184** is included within input. Reasoning output **30,359** is included within output. Do not add these subsets again. The original four epochs contribute 102,030,309 tokens; four replacement epochs contribute 17,412,850. Every epoch reports model `gpt-6-astra`, effort `low`. These are runtime-reported metadata and counters, not independent serving-model attestation or provider billing.

The private measurement read only metadata and token counters from these explicitly identified production rollouts. Each epoch's first cumulative counter equalled its first request increment, establishing an observed zero baseline. Cumulative components were monotonic; each changed cumulative counter matched the accompanying request increment. Duplicate unchanged notifications were ignored. No copied timestamp-plus-counter signatures or overlapping predecessor/successor counter intervals were found. Current room bindings were checked before and after sampling. The total is the sum of the last cumulative counter of each epoch, never the sum of all cumulative events. Unknown replacements fail closed pending lineage review.

The snapshot is sequential, not an atomic provider report. Per-epoch timestamps show freshness; later usage is outside its scope. Operator, rehearsal, presentation and companion sessions are excluded. Input includes repeated context supplied to successive requests; it is not a count of unique words produced.

**Provider-billed dollar spend is unknown.** The preserved [BAND catalog snapshot](usage-snapshot.json) reported 102,262,893 tokens and $131.32365 for four sessions at 17:56:26 UTC. It does not cover the verified eight-epoch lineage, and its cache/pricing semantics were not validated. It is historical telemetry, not the final usage total or a defensible cash-cost estimate. No new dollar estimate is derived from these counters.
