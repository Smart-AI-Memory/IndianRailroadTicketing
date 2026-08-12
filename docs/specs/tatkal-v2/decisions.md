# tatkal v2 — decisions ledger

Append-only. Chair: Patrick. Nothing binds without an entry; reversals
get new entries. Numbering restarts at D1 per this ledger's D1 (the v1
ledger is sealed at D17 in `../tatkal-spike-prototype/decisions.md`).

## D1 — v2 opened; v1 conventions carried; starter ratified

**Date:** 2026-08-12 · **Decided by:** chair (ratification pass over
`../tatkal-spike-prototype/v2-starter.md` §5) · **Status:** final

v2 of the tatkal experiment is opened in this directory with its own
ledger, numbering restarted at D1. The following v1 conventions carry
forward unchanged:

- **Chair model:** Patrick rules; append-only decision entries; nothing
  binds without an entry; reversals get new entries.
- **Pre-registration discipline:** constants/thresholds fixed before
  runs; misses reported, never adjusted; paired per-seed stats only (no
  CI-overlap API, by design).
- **Safety boundary (verbatim):** simulation/calibration only; MUST NOT
  send load or automated booking requests to IRCTC; synthetic workloads
  and locally controlled calibration service/database only; no claim of
  having solved production IRCTC without independent evidence.
- **Honest framing:** scarcity-allocation problem, not only a throughput
  problem; simulated mechanisms carry no authority over real policy.

The v2 starter is ratified as the seed document, as amended by D2–D6.

**Binds:** this directory's spec documents; the starter's §1 carry-in
facts are the factual baseline for v2 requirements.

## D2 — v2 scope: mechanism-design simulations + costed push delivery

**Date:** 2026-08-12 · **Decided by:** chair (starter §5-Q1) ·
**Status:** final

In scope for v2:

1. **Mechanism-design simulations** — pre-registration windows, lottery
   over a qualification window, deliberately paced drains (RESULTS §9's
   "first v2 candidates"; each attacks F5 by making the contest outlast
   the arrival spread).
2. **Costed push delivery** — re-test of the rung-4 waiting room with
   push notification realistically costed (v1 modelled it cost-free
   while fully costing polling; Antigravity seat's open question).

Explicitly out of v2 scope (deferred, not rejected): two-phase
inventory / seat-hold expiry; adversarial bot co-evolution (bounded by
F5 — premature before a mechanism lengthens the contest); real
distributed load / autoscaling; and the standing v1 deferrals (payment,
multi-region, production auth, CAPTCHA, traffic replay, anything
contacting IRCTC).

**Binds:** v2 requirements scope section.

## D3 — floor-aware success-bar derivation is binding

**Date:** 2026-08-12 · **Decided by:** chair (starter §5-Q3) ·
**Status:** final

Floor derivation is a mandatory pre-registration step: every success bar
must state its distance from the relevant physics floor (inventory-drain
arithmetic, or the analogous floor for the metric) **before** the bar is
registered. A bar without a stated floor distance cannot be registered.

Origin: v1's winners bar sat ~4% above the inventory-drain floor by
accident (retro pushback item).

**Binds:** every pre-registered bar in v2.

## D4 — populations and seeds re-derived for v2

**Date:** 2026-08-12 · **Decided by:** chair (starter §5-Q4, against the
starter's draft recommendation to carry v1's) · **Status:** final

v2 populations and seed counts are **re-derived fresh** rather than
carried from v1's D11/20-seed protocol: mechanism-design arms (lotteries,
paced drains) may need different population structure. The derivation
must **document the break from v1** — where and why v2's populations
differ — so cross-version comparisons are made knowingly or not at all.

The center-cell rule stands regardless: sensitivity-sweep center cells
reuse main-sweep data; never re-run the center at lower seed count
(v1's 10-seed center contradicted its 20-seed main sweep in P9).

**Binds:** v2 population/seed derivation document; every sensitivity
sweep.

## D5 — fairness metric defined per mechanism, before guards

**Date:** 2026-08-12 · **Decided by:** chair (starter §5-Q5) ·
**Status:** final

v1's F-ratio measured bot advantage in a latency contest; a lottery or
paced drain changes what "advantage" means. Each mechanism arm must
therefore define its fairness metric — what bot advantage means under
that mechanism — **before** its guard value is registered. No metric,
no guard, no run.

**Binds:** every mechanism arm's fairness guard in v2.

## D6 — push costing: shared worker pool, swept per-push cost

**Date:** 2026-08-12 · **Decided by:** chair (starter §5-Q6) ·
**Status:** final

"Realistically costed" push delivery means: push work is costed on the
**same shared worker pool** that costed v1's status polling (symmetric
costing), with the per-push cost as a **swept parameter**. The sweep's
purpose is to locate the break-even — the push cost at which the waiting
room's advantage disappears — rather than to bet on a single cost value.
Sweep range and grid are pre-registered per D3 discipline before any
run.

**Binds:** the costed-push arm's design and its pre-registered sweep.

## Open questions (no decision yet)

*(new questions get logged here)*
