# Stage 2 independent coverage

Governing contracts: complete stages 1 and 2 at official `803560d2a678ace1414465c098eb0ab5380ffade`. Accepted stage-1 folder at `3813508b5624b4ae89a346b68611a595f83cfde5` was copied unchanged in `21c841ea17505669e909566a9b7cdf2945c91d57`; both folder trees are `93744383122e819f760d2bf0a95dddf6fc791e13`. Stage 1 stays frozen.

This matrix and new tests are derived before stage-2 implementation review. Status is preparation, not service acceptance.

Prepared checks: unittest discovery reports **30 HTTP cases** (23 inherited plus 7 new combination cases). The separate Playwright program defines **7 browser scenarios**: responsive routes/grid/assets, single/pair lost responses, single/pair confirmed conflicts, stale search, and genuine stage-1 pending-retry migration into stage 2. Python compilation and discovery passed; no stage-2 runtime pass is claimed.

| Requirement | Independent check | Acceptance evidence still needed |
|---|---|---|
| All inherited stage-1 semantics | Copied 23 HTTP checks; official inherited suite | Frozen source review, inherited host/isolated execution |
| Declared pairs, sums and no transitivity | Nonlexical table/declaration order; singleton then pair ordering; undeclared end-pair rejection | Execute new combination tests |
| Selection/response forms | Both selectors rejected; empty/duplicate/3-member sets; wrong JSON type; canonical pair response, table_id iff singleton | Source review of missing/null/invalid identifiers |
| Occupancy on every member | Pair blocks both singles/overlapping pairs; cancellation frees members; 50 concurrent overlapping-pair requests | Execute HTTP contention test |
| PATCH and collective moves | Pair-to-single conversion; reversed pair no-op; failed pair expansion rollback; pair/single swap; intra-batch overlap | Frozen implementation review and official batch checks |
| Seeded and exported combinations | Cancelled pair consumes no occupancy; import preserves state/receipt | Structural import review and adversarial corruption |
| Required HTML routes, auth, identity, lookup | Browser login, all signed-in routes, confirmation, lookup/cancel, logout | Browser execution and manual visual inspection |
| Grid semantics and labels | Single availability data attributes; combination labels and declared-order cell ID | Check all slots, unavailable click, empty day |
| Late search A after B | Hold A response, complete B, select B, release A; grid/form/labels remain B | Execute browser race test |
| Confirmed conflict | Other client books after form opens; 409 refresh, inputs retained, error present, no confirmation | Execute for pair and single |
| Lost response after commit | Intercept write, commit server-side, abort delivery; unchanged retry has identical JSON/key and original receipt | Execute single and pair; no fabricated confirmation |
| Stage-1 live upgrade | UI signs in against stage 1; commit/lost response; export/import into stage 2 between requests; same page/form retry | No reload; old receipt may lack table_ids; lookup and session remain valid |
| Browser product quality | 375px and desktop screenshots; no horizontal scroll; visible labels, focus, feedback and human table names | Reviewer visual QA and offline asset requests |
| Offline/deployment/overshoot | Official suites 1+2, expected suite-3 rejection, final isolated run | New shared output directory, runtime/network inspection |

Reviewer owns only `stage-2/tests/independent_*.py`, this matrix and `evidence/stage-2/`. Raw exports and sessions remain private/in memory. Engineer/Experience own repairs. Complete acceptance requires a coordinator-frozen revision and independent runtime results; passing compilation/discovery is not service evidence.
