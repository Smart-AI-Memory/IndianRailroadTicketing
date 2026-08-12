# tatkal-v2 — population derivation (R6)

**Status:** REGISTERED (2026-08-12, D13) — all five axes worked and
their constants registered; the bot repertoire is frozen (D9 executed)
and the abuse model set (D10 executed). Amendment at registration: M1
registration uptake `r_reg` is **swept** {0.5, 0.8, 0.95}, not fixed
(D13.2, against the draft's fixed-0.8 proposal). Per D1 discipline no
registered value may be adjusted after runs. This is the owner document
required by the requirements definition-of-done; D4, D9, D10, D12, and
D13 land here.

**Mandate.** Populations and seeds are re-derived for v2, not carried
(D4). The controlling constraint: cross-version comparisons with v1 are
made **knowingly or not at all** — every departure from the v1
population is recorded in §5 with its comparability consequence.

---

## 1. The v1 record (the baseline being broken from)

From `src/tatkal_sim/model/workload.py` (v1 close) and the v1 protocol:

| parameter | v1 value | meaning |
|---|---|---|
| cohorts | `pre_fire` / `t0_humans` / `bots` (+ `background`) | classified by first arrival |
| operating sizes | 30 / 2500 / 150 / 60 | `OPERATING_WORKLOAD`, D14 supercritical realization of C=256 |
| σ_T0 | 0.35 s | half-normal jitter after T0 — **the arrival spread of F5** |
| bot window | 0.05 s | bots uniform in [T0, T0+50 ms] (sniper family) |
| bot families | sniper / burst / mimic | train-on-one, evaluate-held-out (R7.1 guard) |
| bot advantage | `bot_speedup` cadence + arrival timing | a *racing* advantage |
| pre-fire window / poll | 20 s / 0.75 s | pre-T0 poll density for settling baseline |
| background | 60 users, T0+2 s → T0+32 s | post-spike trickle; settling-time measurability (v1 D14) |
| demand | 8 trains, Zipf s=1.1, AC only | hot-key concentration |
| seeds | 20-seed main sweeps | paired design; centers reuse main-sweep data |

The load-bearing fact: v1's contest lives inside **sub-second arrival
spread** (σ_T0 = 0.35 s, bots in 50 ms). That is exactly what F5 says
makes fairness intervention impossible — and exactly what the v2
mechanism windows are designed to dwarf.

## 2. What each v2 arm changes about what "arrival" means

- **M1 (pre-registration window, length W):** the meaningful arrival is
  the *registration* event inside [T0−W, T0), not the T0 race. The
  pre_fire cohort's camping behaviour becomes the *normal* behaviour;
  the interesting split is registrants vs. walk-ups (who arrive at T0
  unregistered).
- **M2 (lottery over [T0, T0+Q]):** arrival timing inside Q is
  irrelevant **by construction** — the bots' racing advantage
  (bot_window, bot_speedup-at-T0) is neutralized wholesale, and the
  exploit surface moves to identity multiplication (D10). Population
  must therefore model identities, not just users.
- **M3 (paced drain, k tranches over H):** the single contest becomes k
  smaller ones; re-arrival matters (rejected users of tranche i are
  arrivals of tranche i+1), and camping between tranches is the new bot
  play.

Consequence: v1's three-cohort structure keyed on first-arrival timing
does not survive contact with M1/M2 unchanged. The v2 population needs
**identity structure** (D10) and **per-arm behaviour repertoires** (D9)
as first-class axes, with timing demoted from "the whole game" to one
axis among several.

## 3. Derivation axes

Each axis ends in registered constants; per-axis status is tracked in
§6. All values below are **UNSET** unless marked *carried*.

### A1 — cohort structure and sizes — WORKED, pending registration

*Proposed for registration:*

- **Carry the operating scale unchanged:** pre_fire 30 / t0_humans
  2500 / bots 150 / background 60. Rationale: the v1 calibration's
  validity is load-scale-dependent (the D14 supercritical realization
  of C=256); changing scale would demand recalibration and would break
  R1's physics regression check for no mechanism-side reason.
- **M1 registered fraction `r_reg` SWEPT: {0.5, 0.8, 0.95}, center
  0.8** (D13.2, chair amendment of the fixed-0.8 proposal): the stated
  fraction of humans (t0_humans + pre_fire) registers during W; the
  rest arrive at T0 as walk-ups. M1's result is reported as a function
  of registration uptake — the walk-up share is what M1's standby
  handling acts on, and uptake is now a measured axis rather than an
  assumption. M1's cell count multiplies by 3.
- Background cohort carried unchanged (60 users, T0+2 s → T0+32 s);
  its M3 interaction is resolved in §7.

### A2 — arrival spread vs. mechanism windows — WORKED, pending registration

*Proposed for registration:*

- **σ_T0 = 0.35 s carried.** It is the empirically motivated human
  jitter; changing it breaks comparability for no reason (§5 row 1).
- **Honest registration timing (M1):** human registrants arrive
  uniformly over [T0−W, T0) — timing is irrelevant to a
  timing-independent allocation rule, so uniform is the
  honest-behaviour null. Walk-ups use the standard T0 jitter.
- **Realized-ratio reporting:** every mechanism-arm evaluation reports
  its window/σ_T0 ratio (Q/σ_T0, H/σ_T0) alongside results — the F5
  leverage claim made numeric. Registering W, Q, H stays the arms' job
  (R2).

### A3 — bot repertoire (D9) — WORKED, pending registration/freeze

One fixed strategy set spanning all arms, frozen by decision entry
before any evaluated run. *Proposed definitions:*

| strategy | definition | v1 ancestor |
|---|---|---|
| race | arrival uniform [T0, T0+50 ms]; cadence `bot_speedup`=0.5 (timeout/backoff halved) | sniper (carried values) |
| mimic | human-shaped arrival \|N(0, 0.35 s)\|; bot cadence 0.5 | mimic (carried) |
| camp | M1: registers in the first 5% of W (always registered); M3: re-arrives uniform within 50 ms of each tranche open | pre_fire behaviour, weaponized |
| identity-split | M2: controls `m` identities, each entered with mimic-shaped timing (indistinguishable by timing) | none — new per D10 |

- **Degenerate-form rule:** where a strategy's lever does not exist in
  an arm, it executes a stated fallback — camp → race on engineering
  arms; identity-split → mimic outside M2. Cohort composition is thereby
  constant across arms (the v2 analogue of v1's bot_cohort-off
  replacement convention).
- **Mix, fixed across arms:** race 60 / mimic 30 / camp 30 /
  identity-split 30 (= 150). Race keeps the plurality as the
  empirically dominant real-world strategy; the three others get equal
  weight. Per-strategy fairness is reported separately, so the mix
  cannot hide a strategy.
- Bots are probes with fixed strategies (D2/D9): no strategy switches
  on observed outcomes within or across runs.

### A4 — identity-abuse axis (D10) — WORKED, pending registration

*Proposed model:* abuse is a bot capability; humans hold one identity
(v1 R3.10 carry).

- **`m` = 5 identities per abuser, fixed.**
- **Swept: abuse prevalence `p` ∈ {0, 0.1, 0.2, 0.4}** — the fraction
  of the bot cohort running identity-split *in M2 cells*: 0 / 15 / 30 /
  60 bots. The A3 mix supplies the p = 0.2 center (its 30
  identity-split bots); zero-abuse anchors the sweep per D10; the
  non-abusing balance is timing-neutralized in M2 anyway, so
  composition among them is immaterial there.
- **Why these numbers bite:** at p = 0.4, abusers submit 60 × 5 = 300
  entries against ~2530 honest-human and 90 honest-bot entries —
  bot-controlled share of a uniform draw rises from the ~5.6%
  population share to ~13.4% (×2.4 advantage): measurable distortion
  without letting abuse dominate the pool.

### A5 — seeds — WORKED, pending registration

*Proposed for registration:* **20 seeds for every evaluated cell** —
the v1 main-sweep count carried as a floor, applied uniformly: no
evaluated cell below 20, centers reuse main-sweep data (D4 standing),
paired per-seed deltas per R7. The v1 lesson (10-seed center
contradicting the 20-seed sweep) is thereby structurally impossible in
v2.

## 4. Baseline population (RULED — D12)

D7 baselines (rung 2, rung 4) and the R2 mechanism arms must be
compared on **paired seeds over the same population** — otherwise the
paired design is void. **Ruled (D12):** engineering baselines are
re-run under the **v2 population** for all D7 comparisons; v1's
absolute rung numbers are not citable in v2 comparisons; the
v1-population re-run exists only as R1's physics regression check and
is never compared against mechanism arms.

## 5. Documented break from v1 (running table — §the D4 record)

| # | parameter | v1 | v2 | cross-version comparability |
|---|---|---|---|---|
| 1 | σ_T0 | 0.35 s | carried (D13) — **final** | preserved |
| 2 | cohort semantics | timing-only | + identity structure, per-arm repertoires, swept r_reg (D13) — **final** | v1 cohort metrics comparable only for engineering arms |
| 3 | bot repertoire | race + mimic (3 families) | 4-strategy set, frozen (D13.3) — **final** | race/mimic cells comparable; camp/identity-split have no v1 counterpart |
| 4 | identity model | 1 identity per user (implicit) | m=5, p ∈ {0, .1, .2, .4} (D13.4) — **final** | v1 ≙ v2 zero-abuse cell **only** |
| 5 | seeds | 20 main sweeps | 20 universal floor (D13.1) — **final** | paired stats never cross versions |
| 6 | baseline population | v1 workload | v2 re-runs (D12) — **final** | v1 absolute numbers not citable in v2 comparisons |

Rows are appended as derivation proceeds; a row is *final* only when
its constants are registered.

## 6. Axis status

| axis | status |
|---|---|
| A1 cohorts/sizes | **registered — D13** (r_reg swept, chair amendment) |
| A2 spread vs windows | **registered — D13** (per-arm W/Q/H ratios still owed by R2) |
| A3 bot repertoire | **frozen — D13.3** (D9 executed) |
| A4 identity abuse | **registered — D13.4** (D10 executed) |
| A5 seeds | **registered — D13.1** (20 universal floor) |
| §4 baseline population | **ruled — D12** |

## 7. Formerly open questions — resolutions proposed

- **Background vs. M3 pacing (resolved as fidelity):** the background
  cohort stays unchanged even when H extends past T0+2 s — arrivals
  landing inside a paced contest are what would really happen. The
  settling-time baseline is redefined per-arm as beginning after the
  **final allocation event** (last tranche drained, for M3), and any
  arm whose contest overlaps the background window reports the overlap.
  Fidelity kept; measurability preserved by moving the window, not the
  population.
- **M1 registration behaviour (resolved as one-shot):** registration is
  one request per registrant, uniform over W (camp bots front-load per
  A3); no pre-fire-style poll density on the registration surface.
  Costing that request is R2.1's job; this document fixes only the
  arrival behaviour.
- **M2 mimic collapse — registered prediction P1:** M2 collapses mimic
  bots and honest humans into one class *by design* — pooling
  neutralizes both arrival timing and cadence, the only two things
  mimic shares with race. **P1: at p = 0, per-strategy fairness for
  race and mimic under M2 ≈ 1 (no bot advantage).** A residual
  advantage at p = 0 is therefore a *diagnostic* of an implementation
  leak in the arm, not a finding. Stated before any run, per
  pre-registration discipline.
