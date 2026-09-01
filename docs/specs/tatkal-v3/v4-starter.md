# tatkal v4 — starter

**Status:** draft (2026-09-01) — seeded from the v3 graded record
(RESULTS.md, pending chair sign-off); ratification agenda for a v4
ledger's opening pass. Drafted the v2→v3 way: carry-in facts final
per the sealed record, scope candidates ranked, open questions listed.

## 1. What v3 established (carry-in facts)

- **Identity-pricing fails honestly at plausible prices.**
  Work-pricing starves on the shared pool (bottleneck moves at every
  c_verify; at deterrent strength it excludes 62% of honest users —
  more than the bots). Money-pricing is bit-inert until d ≈ 15× V
  (D20 confirmed exactly), then delivers parity with an unmodelled
  regressive cliff. Enrollment-pricing *helps* patient abusers
  (+0.5–0.7 advantage, Holm) by removing honest walk-ups.
- **The reversal: paced drain + re-entry recovers everything v2
  said it destroyed** — 125 → 188/200 seats (+50%, CI excludes 0)
  and the whole-run F guard passes. v2's M3 negative was a
  p_retry = 0 artifact. Adding chances beat charging for chances on
  every measured axis.
- **Costed bursts change loser experience, not allocation** (M2
  +0.23→+1.43 s across the grid; M1 immune; fairness untouched).
- **Latency guards are blind to exclusion harm** — B2 passed at
  exactly the cell where 62% of honest users were priced out; only
  the per-cohort `verify_missed` readout saw it.
- **Registration misses to inherit deliberately:** the B1 p = 0
  hard-median guard fails the record itself (sampling noise at ~180
  controllers); B3/B4's best-case arithmetic floors sit 6–90× under
  congested reality. v4 bars must be floor-aware AND
  congestion-aware (e.g. registered against a measured congested
  baseline, not pure work conservation).

## 2. Scope candidates (ranked)

1. **Pacing + re-entry as the primary mechanism family** — v3's one
   honest winner, currently measured only at v2's registered (k, H)
   and three retry points. Sweep tranche count/horizon × retry
   model; test whether camp-bot dilution survives adversarial
   re-arrival tuning; combine with the lottery (paced draws over a
   qualification window — "add chances over time" as a design axis).
2. **Two-phase inventory / seat-hold** (deferred since v1) — M3
   re-entry at 188/200 leaves a ghost-race remainder; holds with
   expiry would close it and make redemption real. The deposit arm's
   forfeiture rule becomes an actual mechanism instead of a utility
   stand-in.
3. **Adversarial adaptation** (deferred since v1) — every v3
   mechanism was measured against a frozen repertoire; A3's patient
   abuser and M3's camp dilution are exactly where adaptive bots
   would push back first.
4. **Honest-user price sensitivity for A2** — the d = 15 parity
   result is only as meaningful as the unmodelled regressive axis;
   a participation model over stake size would price the cliff.
5. Standing deferrals (distributed load, autoscaling, payments,
   CAPTCHA, IRCTC contact) remain deferred.

## 3. Pre-registration constraints (v3 lessons)

- All v1/v2/v3 conventions carry (chair model, append-only ledger,
  floors before bars, per-metric floors per D17.3, tail-inclusive
  light-work floors per D23, misses-reported-never-adjusted, paired
  per-seed stats, 20-seed floor, Holm within family).
- **NEW — congestion-aware bars:** a floor-relative bar over a
  best-case arithmetic floor MUST state the record cell's own
  measured value at registration; a bar the record itself fails
  cannot be registered (B1-p0/B3/B4 origin).
- **NEW — exclusion-aware guards:** any arm that can resolve users
  by exclusion registers a per-cohort exclusion guard alongside its
  latency guard (the B2/verify_missed origin).
- **Formulas-vs-semantics check stands:** four instances across
  v3 (DC2 objective, DC6-b, tail-free floors, B1-p0 guard) — every
  registered formula gets computed against its own record/semantics
  before the registering entry (cross-review or equivalent).

## 4. Open questions for the ratification pass

- Q1 scope: candidate 1 alone, or 1 + 2 (pacing with real holds)?
- Q2 population: carry D13 verbatim again, or re-derive for
  re-entry-heavy dynamics (retry churn changes what arrival means)?
- Q3 baselines: v3's M3-pr1.0 as the new strong baseline?
- Q4 the B1-class guard: re-register as CI-based (v2 P1 style)
  rather than hard median?
