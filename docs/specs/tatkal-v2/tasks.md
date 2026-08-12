# tatkal-v2 — tasks

**Status:** draft (2026-08-12) — awaiting chair approval; ladder
activates on sign-off by decision entry.

**Basis:** requirements.md (ratified, D11), design.md (approved, D14),
population-derivation.md (registered, D13), decisions.md D1–D14.
Tasks are gated: a phase's exit criteria must hold before the next
phase starts. **Gate B is a chair decision, not a task** — it stands
between implementation and every evaluated run.

Sizes: S (≤ half day), M (~1 day), L (multi-day). Every task names its
requirement trace and its acceptance check.

---

## V0 — regression anchor (R1)

| ID | Task | Size | Trace | Acceptance |
|---|---|---|---|---|
| V0.1 | v1 test suite green on the v2 tree, untouched | S | R1 | all 118 v1 tests pass unmodified |
| V0.2 | Register the R1/R3′ reproduction tolerance by decision entry (chair), then re-run a designated v1 arm under the v1 population | S | R1 | v1 metrics reproduced within the registered tolerance; tolerance entry cited |

**Exit:** v2 development cannot silently alter v1 physics; the
tolerance constant is no longer UNSET.

## V1 — workload extensions (population per D13)

| ID | Task | Size | Trace | Acceptance |
|---|---|---|---|---|
| V1.1 | Identity structure: `identity_id` on `Intent`; identity-split bots map m = 5 identities to one controller; humans 1:1 | M | R2.2, D13.4 | controller-level accounting test: 30 abusers → 150 identities, win attribution rolls up to controllers |
| V1.2 | Registration-phase generation (M1): registrants uniform over [T0−W, T0), camp bots in first 5% of W, walk-ups at T0 jitter; r_reg ∈ {0.5, 0.8, 0.95} | M | R2.1, D13.2 | open-loop guarantee holds (intents from config+rng only); per-uptake counts match r_reg exactly |
| V1.3 | Bot strategies camp and identity-split + degenerate-form rule (camp→race, identity-split→mimic where inapplicable) | M | D13.3 | composition test: every arm sees exactly 60/30/30/30 with the correct effective strategies |
| V1.4 | Abuse-prevalence sweep wiring: p ∈ {0, 0.1, 0.2, 0.4} reassigns bot strategies in M2 cells only | S | D13.4 | p = 0.2 cell is bit-identical to the A3 base mix; p = 0 has zero identity-split bots |

**Exit:** v2 workload generates deterministically from (config,
fidelity, seed); all D13 constants are code, not prose.

## V2 — allocation events and costing

| ID | Task | Size | Trace | Acceptance |
|---|---|---|---|---|
| V2.1 | Allocation-event machinery: a draw resolves a set of pending intents at one instant; event log gains allocation-event id, tranche id | M | design §Shape | resolved intents carry the event id; no intent resolves before its event |
| V2.2 | Notification-burst costing: definitive answers from a draw are work items at `c_push` on the shared pool | M | D6, D14.2 | at c_push = 0 the burst is instantaneous (v1-continuity); at c_push > 0 burst drain time scales linearly (test) |
| V2.3 | Error-taxonomy streams: resets / timeouts / clean rejects / lottery-loss as distinct outcomes end-to-end | S | R4.1 | no report path sums them; planted-outcome test per stream |
| V2.4 | Two-clock fields: absolute TTDA and post-event resolution derived from the same log | S | R4.2, D14.5 | for a synthetic intent, both clocks compute to hand-checked values |

**Exit:** the two v2 simulator concepts (identity, allocation event)
are tested primitives; costing is one model with one parameter.

## V3 — arms

| ID | Task | Size | Trace | Acceptance |
|---|---|---|---|---|
| V3.1 | M1: registration + uniform lottery over registered identities at T0 + auto-redeem + walk-up fast-fail | L | R2.1, D14 | leak diagnostic: camp win-rate ≈ race win-rate among registrants (camping buys nothing under the lottery) |
| V3.2 | M2: pooling over [T0, T0+5 s], draw over unique identities, post-draw fast-fail | L | R2.2, D14.1 | leak diagnostic (P1): at p = 0, race/mimic draw-share advantage ≈ 1 |
| V3.3 | M3: 4 × 50-seat tranches over 8 s atop rung-2 serving layer, sold-out cache reset per tranche open | M | R2.3, D14.3 | inventory invariant holds across tranche boundaries; camp bots re-arrive within 50 ms of each open (log check) |
| V3.4 | R3′: rung 4 with push costed at c_push on the shared pool | M | R3, D6 | c_push = 0 cell reproduces v1 rung 4 within the V0.2 tolerance |

**Exit:** all four arms run as smoke tests (labelled diagnostic, never
cited as results); both P1-family leak diagnostics pass.

## V4 — metrics, fairness, floors

| ID | Task | Size | Trace | Acceptance |
|---|---|---|---|---|
| V4.1 | Two-clock metrics + per-mechanism fairness: draw-share advantage (M1/M2, controller-level), per-tranche F-ratio (M3), v1 F-ratio (R3′) | M | D5, D14.5 | hand-computed values on a synthetic log match |
| V4.2 | Three-variant report generator: plateau/fitted/cliff table emitted by default for every headline metric | M | R4.3 | a report missing a variant fails generation |
| V4.3 | Floor computations: inventory-drain floors (engineering/R3′), burst-drain floors at each c_push grid point (M1/M2 post-event clock), per-tranche and whole-run floors (M3) | M | D3, design §Floors | floor document with one number per (arm, clock, variant, grid point), derivation shown |
| V4.4 | Multiplicity inventory: enumerate every planned paired comparison across V5–V6 | S | R7 | the count Gate B needs, listed by family |

**Exit:** everything Gate B needs to rule on exists: floor document,
fairness metric implementations, comparison inventory.

## GATE B — chair decision (blocks all evaluated runs)

Register by decision entry, informed by V4's outputs:

- **every success bar** with its floor distance stated per clock and
  variant (D3 — a bar without a floor statement cannot be registered);
- **fairness guard values** per mechanism over the D5-defined metrics;
- **multiplicity policy**: the V4.4 comparison count and the correction
  procedure, or the explicit decision not to correct;
- confirmation that reproduction tolerance (V0.2) and any report-only
  metrics are as intended.

No evaluated run starts before this entry exists. Smoke/diagnostic
runs (V3) are never promoted to results.

## V5 — baselines under the v2 population (D12)

| ID | Task | Size | Trace | Acceptance |
|---|---|---|---|---|
| V5.1 | Rungs 0, 2, 4 at 20 seeds × 3 variants under the v2 population | M | R5, D12 | paired-seed logs archived; v1 numbers cited nowhere |

**Exit:** every comparator the arms need exists as v2 data.

## V6 — mechanism and sweep runs

| ID | Task | Size | Trace | Acceptance |
|---|---|---|---|---|
| V6.1 | M1 × r_reg {0.5, 0.8, 0.95} × 3 variants × 20 seeds | M | R2.1 | all cells at full seed count; realized W/σ_T0 reported |
| V6.2 | M2 × p {0, 0.1, 0.2, 0.4} × 3 variants × 20 seeds; P1 evaluated at p = 0 | M | R2.2, D13.5 | P1 verdict recorded (pass, or leak investigation opened) |
| V6.3 | M3 × 3 variants × 20 seeds; per-tranche readouts | M | R2.3 | retry amplification per tranche in the report |
| V6.4 | R3′ × c_push {0, ¼, ½, 1, 2} × 3 variants × 20 seeds; break-even located or bounded | M | R3, D6 | break-even stated with paired CI, or reported not-found-within-range |

**Exit:** every registered cell run at full seed count; no cell below
20 seeds exists anywhere (D13.1).

## V7 — pre-registered evaluation and write-up

| ID | Task | Size | Trace | Acceptance |
|---|---|---|---|---|
| V7.1 | Grade every Gate-B bar (both clocks); misses reported, never adjusted; sensitivity per registered protocol, centers reusing main-sweep data | L | R7, D4 | RESULTS.md v2 with per-clause grading of the expected-result hypothesis |
| V7.2 | Honest-framing section: who each mechanism advantages/disadvantages, not only aggregate scores; policy-authority disclaimer | S | Honest framing | present and specific per arm |

**Exit:** v2 concluded by decision entry; v3 candidates listed.

---

## Standing rules (apply to every phase)

- Determinism and inventory-invariant tests run in CI on every commit.
- No D13/D14 registered constant is touched outside a decision entry.
- Every report lists enabled fidelity toggles and both clocks.
- v1 absolute numbers appear in no v2 comparison (D12).
- Smoke/diagnostic runs are labelled and never cited as results.
- Drift from this ladder gets named in-session before it happens, not
  discovered after.
