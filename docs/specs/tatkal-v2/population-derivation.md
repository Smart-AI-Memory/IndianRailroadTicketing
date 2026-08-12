# tatkal-v2 — population derivation (R6)

**Status:** working draft (2026-08-12) — derivation OPEN. Nothing here
is frozen: proposals are marked *proposed*, and every constant is
**UNSET** until registered by decision entry. This is the owner
document required by the requirements definition-of-done; D4 (re-derive
fresh, document the break), D9 (bot repertoire re-derived then frozen),
and D10 (identity-abuse axis) all land here.

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

### A1 — cohort structure and sizes

*Proposed:* keep the human-side structure (pre_fire / t0_humans /
background) and the operating scale (~2500 t0_humans) so server-side
load physics stays in the calibrated regime; add a registrant/walk-up
split for M1 as a *behaviour* of existing cohorts, not new cohorts.
Sizes: **UNSET** pending A2.

### A2 — arrival spread vs. mechanism windows

The F5 leverage claim of each arm is a *ratio*: mechanism window vs.
population arrival spread. The derivation must state, per arm, the
ratio the population realizes (e.g. Q / σ_T0). Registering W, Q, H is
the arms' job (R2), but the population fixes σ_T0 and the camping/
walk-up mix those windows act on. σ_T0: *proposed carry* at 0.35 s —
it is the empirically motivated human jitter and changing it would
break comparability for no mechanism-side reason (§5 entry 1).

### A3 — bot repertoire (D9: re-derive, then freeze)

*Proposed repertoire,* one fixed strategy set spanning all arms —
frozen by decision entry before any evaluated run:

| strategy | plays against | v1 ancestor |
|---|---|---|
| race | engineering arms, M3 tranches | sniper/burst (carried) |
| mimic | all arms | mimic (carried) |
| camp | M1 registration, M3 inter-tranche | pre_fire behaviour, weaponized |
| identity-split | M2 (and M1 if lottery rule chosen) | none — new per D10 |

Bots are probes with fixed strategies (D2/D9): no strategy switches on
observed outcomes within or across runs. Per-strategy cohort sizes:
**UNSET**.

### A4 — identity-abuse axis (D10)

The abuse model must answer: who multiplies identities (bots only, or a
human tail too), and what does an identity cost? *Proposed:* abuse is a
bot capability — each identity-split bot controls `m` identities, with
`m` NOT swept (fixed per registration) and the **swept parameter being
abuse prevalence**: the fraction of the bot cohort running
identity-split. Zero-abuse cell anchors the sweep (D10). Abuse model,
`m`, prevalence grid: **UNSET**.

### A5 — seeds

Seed count is constrained by R7's paired-CI decision rule and by the
v1 lesson that 10-seed cells contradict 20-seed sweeps. *Proposed
floor:* no evaluated cell below the main-sweep seed count, whatever it
is registered to be; centers reuse main-sweep data (D4, standing).
Count: **UNSET**.

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
| 1 | σ_T0 | 0.35 s | *proposed carry* | preserved if carried |
| 2 | cohort semantics | timing-only | + identity structure, per-arm repertoires | v1 cohort metrics comparable only for engineering arms |
| 3 | bot repertoire | race + mimic (3 families) | 4-strategy set (A3), frozen | race/mimic cells comparable; camp/identity-split have no v1 counterpart |
| 4 | identity model | 1 identity per user (implicit) | abuse axis per D10 | v1 ≙ v2 zero-abuse cell **only** |
| 5 | seeds | 20 main sweeps | UNSET | paired stats never cross versions |
| 6 | baseline population | v1 workload | v2 re-runs (D12) | v1 absolute numbers not citable in v2 comparisons — **final** |

Rows are appended as derivation proceeds; a row is *final* only when
its constants are registered.

## 6. Axis status

| axis | status |
|---|---|
| A1 cohorts/sizes | open — proposal drafted |
| A2 spread vs windows | open — σ_T0 carry proposed |
| A3 bot repertoire | open — 4-strategy set proposed (D9 freeze pending) |
| A4 identity abuse | open — prevalence-sweep model proposed (D10) |
| A5 seeds | open |
| §4 baseline population | **ruled — D12** |

## 7. Open questions

- Does the background cohort (settling-time trickle) interact with M3's
  pacing horizon H? If H extends past T0+2 s, background arrivals land
  *inside* the contest — decide whether that is fidelity (it is what
  would really happen) or contamination (settling baseline lost).
- Does M1 registration traffic need its own pre-fire-style poll
  density, or is registration a one-shot request per user? (Costing is
  R2.1's job; the *population behaviour* is this document's.)
- mimic-family bots under M2: with timing neutralized, is mimic
  distinct from an honest human at all — or does M2 collapse mimic and
  human into one class by design? (If so, that is a *finding to
  predict*, worth stating before runs.)
