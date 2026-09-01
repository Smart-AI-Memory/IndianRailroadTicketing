# tatkal-v3 — tasks

**Status:** approved — ladder active (chair sign-off 2026-09-01,
decisions.md D14).

**Basis:** requirements.md (draft), design.md (draft, DC1–DC6),
decisions.md D1–D11, v2 population (D13, carried by D3). Phases are
gated: a phase's exit criteria hold before the next starts. **Gate B
is a chair decision, not a task.** Sizes: S (≤ half day), M (~1 day),
L (multi-day). Every task names its trace and acceptance.

---

## W0 — regression anchor (R1)

| ID | Task | Size | Trace | Acceptance |
|---|---|---|---|---|
| W0.1 | v1+v2 test suite green on the v3 tree, untouched | S | R1 | all tests pass unmodified |
| W0.2 | Re-run a designated v2 arm (M2 p = 0.1, fitted) under the v3 tree | S | R1 | v2 metrics reproduced within the registered tolerance; entry cited |

**Exit:** v3 development cannot silently alter v1/v2 physics.

## W1 — priced-entry machinery and the deadline surface

| ID | Task | Size | Trace | Acceptance |
|---|---|---|---|---|
| W1.1 | Priced-entry pipeline: entry filters/costs compose onto the M2 draw path without touching the draw | M | design §Shape | with all pricing disabled, M2 output is bit-identical to v2 M2 |
| W1.2 | Verification work items on the shared pool at `c_verify`; `verify-missed` outcome stream | M | R2.1, DC1 | verification demand > window capacity produces clean `verify-missed`, never lost intents; pool-wait logged per identity |
| W1.3 | Deposit entry rule (DC2 as amended by D17) + forfeiture accounting; `forfeit` stream | M | R2.2, DC2/DC3, D17 | at d = 0, k = m reproduces the v2 unmitigated cell; forfeiture ledger balances: stakes in = loser refunds + excess-win forfeits + redeemed-winner stakes (returned at redemption — the deposit is a bond, not a price; D17 finding 2) |
| W1.4 | Deadline-spike registration profile (DC4) + `ineligible` stream; uniform profile as labelled variant | M | R2.3, R5.1 | per-profile arrival histograms match registered constants; open-loop guarantee holds |

**Exit:** the one new simulator concept (priced entry) is a tested
primitive; all three new outcome streams exist end-to-end.

## W2 — arms

| ID | Task | Size | Trace | Acceptance |
|---|---|---|---|---|
| W2.1 | A1 verification-cost arm assembled | M | R2.1 | abuse-pricing statement on record; smoke run per variant |
| W2.2 | A2 deposit arm assembled | M | R2.2 | abuse-pricing statement on record; d-grid smoke monotonicity (higher d → lower k*) |
| W2.3 | A3 registration-bound arm assembled | M | R2.3 | abuse-pricing statement on record; camping-buys-nothing leak diagnostic (v2 M1 carry) passes |

**Exit:** three arms run as labelled smoke tests; every abuse-pricing
statement is a recorded entry. Smoke runs are never cited as results.

## W3 — metrics, floors, coverage

| ID | Task | Size | Trace | Acceptance |
|---|---|---|---|---|
| W3.1 | Honest-cost readout per arm (both clocks + arm-specific price), per cohort | M | R2, Honest framing | hand-computed synthetic-log values match |
| W3.2 | Floor document: verification-pool floors per DC1 point (named per metric — aggregate drain vs wait-distribution, D17 finding 3); burst/winner-drain floors per c_push point; M3 floors per p_retry point — every derivation enumerating drain components | M | R8, D4.2, D17 | one number per (arm, clock, variant, grid point, metric); enumeration present for each |
| W3.3 | Multiplicity inventory: every planned paired comparison across W5–W6, listed by family | S | R8 | the count Gate B needs |
| W3.4 | **Bar-cell coverage table:** every bar the Gate-B draft registers ↔ its planned cell below | S | R8, D4.1 | zero uncovered bars; the table is in the Gate-B packet |

**Exit:** everything Gate B needs exists. W3.4 failing blocks the
gate — that is its purpose.

## GATE B — chair decision (blocks all evaluated runs)

Register by decision entry, informed by W3: every success bar with
floor distance stated per clock/variant/grid point; fairness guard
values over the carried D5 metric; honest-cost guard values;
multiplicity policy over the W3.3 count; reproduction tolerance
confirmation; the W3.4 coverage table attached. No evaluated run
before this entry.

## W4 — anchor run (R9 — independent of W1–W3, may run first)

| ID | Task | Size | Trace | Acceptance |
|---|---|---|---|---|
| W4.1 | Engine flag on r2_server; MariaDB install recorded in README | S | R9, D11 | same ladder runs against both engines |
| W4.2 | MariaDB calibration: ladder 1…256, ≥ 3 reps; CSV committed | S | R9 | raw CSV under tatkal-spike-prototype/calibration/ |
| W4.3 | Grade DC6 shape criteria; synthesis addendum updating threat #1 either way | S | R9, D8 | addendum merged; verdict stated as confirmed / falsified |

**Exit:** the project has two anchor lineages, or a recorded
falsification — both acceptable, one mandatory.

## W5 — sweeps (the design §Cell-budget list, as registered at Gate B)

| ID | Task | Size | Trace | Acceptance |
|---|---|---|---|---|
| W5.1 | A1 grid: c_verify × p, fitted + center bracketing | M | R2.1 | all cells 20 seeds; pool-wait stream in every report |
| W5.2 | A2 grid: d × p, fitted + center bracketing | M | R2.2 | forfeiture ledger balances in every cell |
| W5.3 | A3 grid: profile × p, fitted + center bracketing | M | R2.3 | deadline-vs-uniform delta reported |
| W5.4 | R3 bursts: 2 arms × c_push grid + bracketing | M | R3 | floors per grid point from W3.2 cited |
| W5.5 | M3 × p_retry × 3 variants | M | R4, D17 | per-tranche readouts; censoring companion present; whole-run inventory, fairness, and retry amplification reported at every grid point (D17 finding 6) |

**Exit:** every registered cell at full seed count; no cell below 20
seeds exists anywhere; v2 reuse cells cited, not re-run.

## W6 — pre-registered evaluation and write-up

| ID | Task | Size | Trace | Acceptance |
|---|---|---|---|---|
| W6.1 | Grade every Gate-B bar; misses reported, never adjusted; cross-arm comparison table (the D5 finding) | L | R8 | RESULTS.md v3 with per-clause grading of the expected result |
| W6.2 | Honest-framing section: who each mitigation prices out, per cohort; unmodelled-harm axes named (honest price-sensitivity) | S | Honest framing | present and specific per arm |
| W6.3 | v4 starter drafted from the graded record | S | v2 precedent | starter seeded from RESULTS, not from memory |

**Exit:** v3 concluded by decision entry; ledger sealed; v4
candidates listed.

---

## Standing rules (every phase)

- Determinism and inventory-invariant tests on every commit.
- No registered constant is touched outside a decision entry.
- Every report lists fidelity toggles, both clocks, and enabled
  outcome streams.
- Smoke/diagnostic runs labelled, never cited.
- v2 record cells are reused only where the population is verbatim
  (D3); any drift discovered voids the reuse and is named in-session.
- Drift from this ladder gets named before it happens.
