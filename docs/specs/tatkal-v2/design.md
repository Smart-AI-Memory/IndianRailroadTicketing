# tatkal-v2 — design

**Status:** APPROVED (2026-08-12, D14) — all five design choices ruled
as proposed; the constants marked **PROPOSED** below are now
**registered** by D14 (windows, shared c_push grid, rung-2 M3 base,
auto-redeem, two-clock reporting). Still owed before runs: fairness
guard values (D5) and success bars with floor statements (D3).
Population constants were registered earlier (D13).

**Inputs:** requirements.md (ratified, D11); population-derivation.md
(registered, D13); v1 design.md (the simulator being extended).

---

## Shape of the extension

v2 adds three allocation mechanisms and one costed re-run to the v1
simulator without touching v1 physics (R1):

- **The v1 `AdmissionStrategy` protocol stays.** M2 and M3 are
  implementable inside it: M2 is an admission strategy that pools
  instead of serving; M3 is an inventory-release schedule composed with
  an existing serving layer. M1 adds one pre-T0 phase (registration) to
  the workload plus an allocation event at T0.
- **New workload capability: identity structure** (D13.4). `Intent`
  gains an `identity_id` distinct from `user_id`; identity-split bots
  map `m = 5` identities to one controller. Humans: one identity each
  (v1 R3.10 carry).
- **New simulator concept: the allocation event.** M1's draw at T0 and
  M2's draw at T0+Q resolve many intents *at one instant*. Delivering
  those definitive answers is a **notification burst** — real work, not
  free. Burst delivery is costed with the same per-push cost parameter
  `c_push` as the R3 arm (one costing model across v2, see Measurement)
  — the D6 sweep therefore stresses M1/M2 too, not only the waiting
  room.
- v1 arms re-run unchanged under the v2 population per D12; rung 0 and
  rung 2 compile against the extended workload with identity fields
  ignored.

## Arm M1 — pre-registration window

Registration phase in [T0−W, T0): one-shot registration request per
registrant (D13.6), costed as server work on the shared pool.
Registration uptake `r_reg` swept {0.5, 0.8, 0.95} (D13.2).

- **W = 300 s — PROPOSED.** Realized ratio W/σ_T0 ≈ 857; registration
  load is trivially spread (~2,000 one-shots over 5 min at center
  uptake). Discrete-event time makes the long window computationally
  free.
- **Allocation rule — PROPOSED: uniform lottery over registered
  identities at T0** (the D8 default; FRFS remains available only via a
  justifying entry). Seats granted to `min(seats, registrants)` drawn
  winners.
- **Winner redemption — PROPOSED: auto-redeem.** Winners' booking
  requests are auto-submitted at T0 with standard human jitter; no
  redemption-window mechanic in v2 (a hold-expiry mechanic is two-phase
  inventory, which D2 defers). Losers get definitive answers in the T0
  notification burst.
- **Walk-ups** (the 1−r_reg share) contend for any seats left
  unallocated (normally zero) through the serving layer and receive
  fast definitive sold-out answers — M1's standby handling *is* the
  fast-fail path.
- Camp bots register in the first 5% of W (D13.3); registration
  timing is irrelevant under the lottery rule, so camping should buy
  nothing — a second implementation-leak diagnostic in the P1 family.

## Arm M2 — lottery over a qualification window

All booking arrivals in [T0, T0+Q] are pooled; the draw resolves at
T0+Q over **unique identities** in the pool.

- **Q = 5 s — PROPOSED.** Realized ratios: Q/σ_T0 ≈ 14, Q/bot_window =
  100. The contest outlasts the arrival spread by construction — the
  F5 statement is arithmetic, not argument.
- **Background overlap acknowledged:** background arrivals in
  [T0+2 s, T0+Q] land inside the pool (D13.6 fidelity ruling: the
  population does not move). Their pool share is reported.
- **Abuse sweep:** p ∈ {0, 0.1, 0.2, 0.4} per D13.4. Prediction P1
  (race/mimic advantage ≈ 1 at p = 0) is evaluated here.
- Draw winners' bookings execute immediately after the draw; losers
  are resolved in the T0+Q notification burst. Post-draw arrivals get
  fast-fail sold-out answers.

## Arm M3 — paced drain

Inventory released in `k` tranches over horizon H, composed atop the
rung-2 serving layer (fast-fail with its sold-out cache reset at each
tranche open) — **composition base PROPOSED** for chair confirmation.

- **k = 4 equal tranches (50 seats), H = 8 s — PROPOSED.** Tranche
  spacing 2 s ≈ 5.7×σ_T0: each tranche re-forms a contest, and the
  overall contest spans H/σ_T0 ≈ 23. Equal tranches keep the design
  one-parameter-simple; uneven schedules are a labelled variant only.
- Camp bots re-arrive within 50 ms of each tranche open (D13.3) —
  M3 is where camp genuinely bites, and per-tranche per-strategy
  fairness is the readout.
- Re-arrival fidelity: rejected users of tranche i re-enter per the v1
  retry model (`p_retry_after_reject` sensitivity knob carries); M3
  cells report retry amplification per tranche.
- Settling time measured from final-tranche drain (D13.6).

## Arm R3′ — costed push re-run (waiting room)

v1 rung 4 re-run with push delivery costed per D6:

- Push work on the shared worker pool, service time = `c_push`.
- **Sweep grid — PROPOSED: c_push ∈ {0, ¼, ½, 1, 2} ×
  `status_service_time`** (v1 default `app_time`/5). Anchored at zero
  (the v1 model, R3 acceptance's continuity cell); topping at 2× a
  status check — if a push costs more than the poll it replaces, the
  room's economics have inverted, so the grid brackets the plausible
  break-even by construction.
- Comparator: rung 2 under the v2 population (D12), paired seeds.
  Break-even = the c_push at which the rung-4 vs rung-2 paired delta's
  95% CI on the primary metric includes zero.

## Measurement changes (R4, R7)

- **Event log gains:** `identity_id`, allocation-event id, tranche id,
  per-strategy bot labels. Metrics stay derived-not-inline (v1 rule).
- **Two-clock reporting for allocation arms.** Absolute TTDA (from
  arrival; includes the deliberate wait W or Q — honest user
  experience) AND post-event resolution latency (from the allocation
  event; the mechanism's operational quality). Bars will be registered
  per-clock under D3 — the deliberate wait is a *designed* floor
  (losers cannot resolve before the draw), so floor-aware bars are
  mandatory here, not optional hygiene. This generalizes v1's
  horizon-censoring lesson (R4.2).
- **Error taxonomy first-class (R4.1):** resets / timeouts / clean
  rejects / lottery-loss are distinct outcome streams in the log and
  every report.
- **Three-variant tables by default (R4.3):** the report generator
  emits plateau/fitted/cliff for every headline metric; M1/M2 draw
  bursts and M3 tranche opens are exactly the kind of load spike the
  cliff variant exists to stress.
- **Per-mechanism fairness (D5) — PROPOSED definitions** (registered
  with their guards later, per D5's no-metric-no-guard-no-run):
  - M1/M2: **draw-share advantage** = bot-controlled win share ÷
    bot population share (per strategy; identity-split measured at the
    controller level, not the identity level).
  - M3: per-tranche F-ratio (v1 definition per tranche), plus
    whole-run aggregate.
  - R3′: v1 F-ratio unchanged (latency-shaped contest).
- **Paired-seed harness carries** (20-seed floor per D13.1, bootstrap
  B=10,000 on the seeded stats stream, no CI-overlap API).

## Floors (D3 groundwork — derivations owed before bars)

To be computed and stated with each bar's registration:

- engineering arms / R3′: inventory-drain arithmetic floor (v1 method).
- M1/M2 losers: post-event resolution floor = notification-burst drain
  time at the swept c_push (a *moving* floor — bars must state distance
  at each grid point or bind at the registered worst case).
- M3: per-tranche drain floor; whole-run floor = H + last-tranche
  drain.

## Out of scope

Two-phase inventory (auto-redeem is the M1 design consequence),
adaptive bots, distributed load, per-train forecasting — all per D2.
No new ML (R8): the v1 classifier is not run inside mechanism arms.

## Design choices — RULED (D14)

All five choices were ruled as proposed at the DC1–DC5 pass
(2026-08-12): windows (W = 300 s, Q = 5 s, k = 4 / H = 8 s), the shared
c_push grid, the rung-2 M3 base, M1 auto-redeem, and two-clock
reporting are registered by D14. tasks.md follows.
