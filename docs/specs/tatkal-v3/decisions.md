# tatkal v3 — decisions ledger

Append-only. Chair: Patrick. Nothing binds without an entry; reversals
get new entries. Numbering restarts at D1 per this ledger's D1 (the v2
ledger is sealed at D19 in `../tatkal-v2/decisions.md`).

## D1 — v3 opened; v1/v2 conventions carried; starter ratified

**Date:** 2026-08-12 · **Decided by:** chair (ratification pass over
`../tatkal-v2/v3-starter.md` §5) · **Status:** final

v3 opens in this directory with its own ledger. Carried unchanged from
the v2 ledger's D1: the chair model, pre-registration discipline
(constants fixed before runs; misses reported, never adjusted; paired
per-seed stats; no CI-overlap API), the IRCTC safety boundary
verbatim, and honest framing (simulated mechanisms carry no policy
authority). Additionally carried as already-binding: the D18.2 amended
floor rule — post-event floors are max(burst drain, winner-redemption
drain).

The v3 starter is ratified as the seed document, as amended by D2–D5.
The v2 graded record (RESULTS.md, chair-approved) is v3's factual
baseline.

**Binds:** this directory's spec documents.

## D2 — v3 scope: M2 identity mitigation + costed bursts + M3 retry sensitivity

**Date:** 2026-08-12 · **Decided by:** chair (starter §5-Q1) ·
**Status:** final

In scope:

1. **M2 identity mitigation** — mechanisms that price identities and
   the question of which reclaims parity under abuse (arms per D5).
2. **Costed M1/M2 notification bursts** — the allocation arms across
   the existing D14.2 c_push grid, closing v2's coverage gap under the
   amended floor rule.
3. **M3 retry-model sensitivity** — sweep `p_retry_after_reject`:
   does paced drain recover inventory and fairness when rejected
   demand re-enters?

Out (deferred, not rejected): two-phase inventory / seat-hold;
adversarial co-evolution; distributed load; the standing v1/v2
deferrals including anything contacting IRCTC.

**Binds:** v3 requirements scope.

## D3 — population: v2's D13 carried verbatim

**Date:** 2026-08-12 · **Decided by:** chair (starter §5-Q3) ·
**Status:** final

The v2 registered population carries verbatim: cohorts and operating
scale, σ_T0, the 60/30/30/30 strategy mix with the degenerate-form
rule, m = 5, the abuse prevalence grid, the 20-seed universal floor,
and the center-cell rule. Additions only by decision entry; the bot
repertoire stays fixed (co-evolution deferred). Mitigations are
modelled mechanism-side, so v3 results remain directly comparable to
the v2 record.

**Binds:** every v3 workload.

## D4 — process rules: bar-cell coverage and floor completeness are binding

**Date:** 2026-08-12 · **Decided by:** chair (starter §5-Q4) ·
**Status:** final

1. **Bar-cell coverage check:** every registered bar must map to at
   least one planned cell in tasks.md before gate approval — a bar no
   cell evaluates cannot be registered. (Origin: v2's per-grid-point
   burst bars with only the zero cell run.)
2. **Floor completeness rule:** a floor derivation must enumerate the
   drain components it includes and state why omitted components are
   irrelevant. (Origin: D18.2's omitted winner-redemption drain.)

**Binds:** v3's gate approvals and floor document.

## D5 — mitigation arms: verification-cost, deposit, registration-bound

**Date:** 2026-08-12 · **Decided by:** chair (starter §5-Q5) ·
**Status:** final

All three mitigation arms enter requirements, each pricing identity in
a different currency:

- **Verification-cost** (work-priced): each identity entering the draw
  costs a verification work item on the shared pool.
- **Deposit** (money-priced): entry stakes a deposit refunded to
  losers; abuse at scale becomes economically self-defeating. Modelled
  abstractly — no payment processing (the deferral stands); the
  deposit is a utility parameter, not a payment flow.
- **Registration-bound** (enrollment-priced, the M1×M2 hybrid): only
  identities registered in a pre-window may enter the draw.

The comparison across the three is the finding.

**Binds:** v3 requirements R-scope for M2 mitigation.

## D6 — v1–v2 synthesis precedes v3 requirements authoring

**Date:** 2026-09-01 · **Decided by:** chair (promotion from round
table thread `q-project-critical-review-001`, msgs 2, 4, 6, 8;
3/3 seats convergent in one round, no absences) · **Status:** final

Before v3's requirements.md is authored, the project ships a
**time-boxed v1–v2 synthesis**: one standalone, paper-style document
with an explicit threats-to-validity section, ending in a
claim → evidence → v3-gap table, plus a repo-hygiene pass folded
into the same PR (tag the v2 conclusion, prune the stale session
worktree, resolve the uncommitted `requirements.txt` edit, ignore
`.DS_Store`). Rationale (unanimous across seats): the repo went
public 2026-09-01 with no readable front door; writing the validity
section forces confrontation with structural weaknesses —
single-calibration-anchor, cost-model sensitivity,
parity-near-true-by-construction — while v3 design can still respond
to them; v3 loses nothing since D1–D5 are ledgered. Guard against
the seats' own named risk: **one document, one PR** — the synthesis
is not an open-ended documentation project.

Full transcript: `~/.attune/reports/roundtable/q-project-critical-review-001.md`
(machine-local, untracked).

**Binds:** v3 sequencing — the requirements gate does not open until
the synthesis PR lands.

## D7 — synthesis audience: transferring practitioners first

**Date:** 2026-09-01 · **Decided by:** chair (ruling on OQ1) ·
**Status:** final

The D6 synthesis optimizes first for **practitioners judging whether
the conclusions transfer beyond the simulator**, not for students
reproducing the experiment. Consequences for the document: claims and
their transfer limits lead; the threats-to-validity section is a
first-class citizen, not an appendix; reproduction instructions
(seeds, sweep commands, grading pipeline) are included but demoted to
an appendix. The claim → evidence → v3-gap table is written in
practitioner terms: what would have to be true of a real system for
each claim to carry.

**Binds:** the D6 synthesis document's structure.

## D8 — second calibration anchor: the owed Postgres run lands in v3

**Date:** 2026-09-01 · **Decided by:** chair (ruling on OQ3) ·
**Status:** final

v3 does **not** inherit the single SQLite hot-key measurement as the
project's only anchor to reality. A second, independent calibration
anchor is ruled in: the **Postgres run owed since v1's R2** ("these
constants are provisional until it lands"). Postgres locks per row
where SQLite serialises the whole database, so it is the anchor that
directly tests the two things the lone SQLite run cannot:

1. **Does the transferable finding survive?** v1's headline shape —
   flat median, ~1000× p99 explosion past the knee — is claimed as
   the transferable result. If Postgres reproduces the shape (at
   whatever absolute constants), the finding is engine-independent
   and the simulator's server model rests on two legs. If it does
   not, the simulator is misspecified for exactly the sharded case
   (R4 rung 3) where SQLite is known to *overstate* contention — a
   falsification, to be reported as such, per the pre-registration
   discipline.
2. **The sharded-case constants stop being provisional.** v2/v3
   comparisons involving per-train sharding currently ride on an
   engine whose lock scope is wrong for that case by construction.

The run reuses the v1 calibration protocol
(`tools/calibrate_lock_contention.py`, same concurrency ladder, ≥ 3
reps) against a local Postgres. Its result — confirming or breaking
the shape — is **explained in the D6 synthesis's threats-to-validity
section** either way; a confirming result upgrades the section, a
breaking one becomes the synthesis's most important paragraph.
Practical note: this requires a local Postgres, a deliberate
infrastructure addition to be recorded in the repo README when it
lands (the project's no-ad-hoc-installs discipline applies).

**Binds:** v3 calibration scope; the D6 synthesis content.

## D9 — gateway modelling: the costed-pool middle path

**Date:** 2026-09-01 · **Decided by:** chair (ruling on OQ2, after
moderated deliberation; recommendation adopted) · **Status:** final

Neither pole. Full active-bottleneck modelling invents calibration
constants the project does not have (rigor-theater risk, per the
`q-project-critical-review-001` review); pure utility penalties are
blind to bottleneck-moving — the exact failure v2's costed push
notifications exposed in the waiting room. Instead, the v2 `c_push`
pattern applies: **swept, capacity-bounded costs — never invented
latency distributions.** Per arm:

1. **Verification-cost:** the D5 shared pool is a *bounded-capacity
   queue* (existing simulator machinery), service capacity swept over
   a pre-registered grid. Registration arrivals follow a
   **deadline-spike profile** reusing the T0 arrival machinery — the
   arm is explicitly tested for whether it merely moves the stampede
   to the registration-window close (the R8 question, new subsystem).
2. **Deposit:** stays a pure utility parameter — D5 ruled it and
   money is not a queueing resource in this model; payment-processing
   failure modes remain deferred.
3. **Registration-bound:** no bottleneck modelling (the pre-window is
   long), but it shares arm 1's deadline-arrival profile so the two
   arms differ by mechanism, not modelling generosity.

The asymmetry is by design: each arm's price is charged against the
model most faithful to that price's currency (work queues; money does
not). The verification pool enters every relevant floor derivation as
an enumerated drain component (D4 rule 2).

**Binds:** v3 requirements and design for the D5 arms; v3 workload
definitions (deadline-spike registration arrivals).

## D10 — correction to D8: the Postgres anchor already landed in v1

**Date:** 2026-09-01 · **Decided by:** moderator finding, recorded
append-only; supersedes D8's premise, not its intent · **Status:**
final (factual correction); successor question logged as OQ4

D8 was ruled on a stale premise. The round-table brief (and D8's
text) described the project as resting on the lone SQLite hot-key
measurement, with "the Postgres run owed since v1's R2." In fact the
v1 record shows:

- The **Postgres/HTTP calibration landed 2026-08-11**
  (`tatkal-spike-prototype/calibration/2026-08-11-postgres-http.csv`,
  fit record `fit-2026-08-11.json`, harness `tools/r2_server.py` +
  `tools/calibrate_r2.py`) and is the measurement the simulator's
  server model was fitted to (v1 RESULTS §1).
- The **SQLite run is withdrawn provenance** (v1 RESULTS §10) — it is
  not an anchor at all.

So the true state is *one valid anchor* (Postgres/HTTP, one machine),
not the SQLite-only picture D8 corrected against. D8's substance —
the project should not rest on a single calibration anchor — stands
unchanged; its prescribed mechanism ("the owed Postgres run") is
already satisfied and cannot be the second anchor. What a second
anchor now means is a genuinely independent lineage: a **different
engine** (e.g. MySQL/MariaDB behind the same R2 HTTP harness — tests
engine-independence of the flat-median/exploding-tail shape) or
**different hardware** (same harness elsewhere — tests machine
transfer). Engine choice and any infrastructure install are the
chair's (OQ4). The D6 synthesis describes the calibration lineage as
it actually is: Postgres-anchored, SQLite withdrawn, single machine.

**Binds:** D8's implementation; the D6 synthesis's
threats-to-validity content.

## Open questions (no decision yet)

Logged 2026-09-01 from round table `q-project-critical-review-001`
(member-originated, R9; chair-promoted):

- ~~OQ1 (Codex, msg 3)~~ — resolved by **D7**.
- ~~OQ2 (Antigravity, msg 5)~~ — resolved by **D9**.
- ~~OQ3 (Claude, msg 7)~~ — resolved by **D8**, as corrected by
  **D10**.
- ~~OQ4 (from D10)~~ — resolved by **D11**.

## D11 — second anchor: MariaDB/MySQL behind the existing R2 harness

**Date:** 2026-09-01 · **Decided by:** chair (ruling on OQ4;
moderator recommendation adopted) · **Status:** final

The D8/D10 second calibration anchor is a **second engine on the same
machine**: MariaDB (or MySQL) behind the existing R2 HTTP harness
(`tools/r2_server.py` / `tools/calibrate_r2.py`), same concurrency
ladder, ≥ 3 reps. Rationale: it directly tests engine-independence of
the flat-median / exploding-tail shape — the claim v3 leans on —
with one local install and no new hardware; the synthesis already
disclaims absolute constants, so hardware transfer is the weaker
marginal question. Shape-comparison criteria are pre-registered in
v3 requirements (R9) before the run; the result is reported either
way and lands as an addendum to `docs/v1-v2-synthesis.md` per D8.
The MariaDB install is recorded in the README when it happens
(no-ad-hoc-installs discipline).

**Binds:** v3 requirements R9; the anchor task in v3 tasks.md.

## D12 — requirements ratified

**Date:** 2026-09-01 · **Decided by:** chair · **Status:** final

`requirements.md` R1–R10 are ratified as authored. The abuse-pricing
statement obligation (R2), the bar-cell coverage and floor
completeness bindings (R8/D4), the R9 anchor criteria procedure, and
the first-class honest-cost readout (Honest framing) all bind.
UNSET constants remain traceable to the entries that must fix them
(Gate B for bars/guards; D13 below for the design constants).

**Binds:** the v3 experiment's scope and procedure.

## D13 — design approved; DC1–DC6 registered as proposed

**Date:** 2026-09-01 · **Decided by:** chair · **Status:** final

`design.md` is approved. DC1–DC6 are registered as proposed, none
amended: c_verify ∈ {¼, 1, 4} × app time (DC1); the deterministic
expected-value deposit entry rule (DC2); d ∈ {0.1, 0.5, 2} × V
(DC3); the deadline-spike registration profile — 40% uniform + 60%
final-10%, σ_reg = σ_T0, uniform as labelled variant (DC4);
p_retry ∈ {0, 0.25, 0.5, 1.0} (DC5); anchor shape criteria — knee
exists, p50 ≤ 2× and p99 ≥ 10× at 8× knee (DC6). The §Cell-budget
table (59 cells / 1,180 runs) is the planning envelope; the binding
cell list is tasks.md as gated at Gate B.

**Binds:** every v3 mechanism constant named above.

## D14 — task ladder approved; ladder active

**Date:** 2026-09-01 · **Decided by:** chair · **Status:** final

`tasks.md` W0–W6 is approved and the ladder is active. Gate B
remains a chair decision standing between W3 and every evaluated
run; the W3.4 bar-cell coverage table is a gate blocker (D4.1). W4
(anchor run) is authorized to run ahead of W1–W3, its MariaDB
install to be recorded in the README when it happens (D11).

**Binds:** v3 execution order and gates.

## D15 — W4 anchor graded: engine-independence FALSIFIED; DC6-b criterion miss recorded

**Date:** 2026-09-01 · **Decided by:** moderator grading under the
registered protocol; chair notified · **Status:** final (result
entry; misses reported, never adjusted)

The D11 MariaDB anchor ran same-day (12.3.3, full ladder, 20
reps/level, zero errors; raw CSV in
`../tatkal-spike-prototype/calibration/2026-09-01-mariadb-http.csv`;
graded report `reports/w4-anchor-2026-09-01.md`). DC6 verdict as
registered: (a) pass, **(b) FAIL** (p50 ratio 8.45 vs ≤ 2),
**(c) FAIL** (p99 ratio 5.64 vs ≥ 10) — **the fitted server shape is
not engine-independent.** MariaDB queues fairly (p50/p99 grow
together, throughput holds at 96% of peak at C = 256); Postgres
degrades tail-first (p99 ×50, throughput to 32% of peak).

Recorded miss: DC6-b as registered is failed by the Postgres anchor
itself (ratio 3.46) — the criterion encoded the synthesis slogan,
not statistics computed from the anchor CSV. Graded as registered;
the falsification does not hinge on it (report §criterion-miss).

Consequences (bindings, not adjustments): fitted-variant results are
scoped to Postgres-like engines; the plateau variant has a measured
real instance; R4.3 three-variant reporting is load-bearing for
every v3 headline. Synthesis threat #1 updated by addendum per D8's
either-way obligation.

**Binds:** interpretation scope of fitted-variant claims in v3
reporting; the W4 exit criterion is met (two anchor lineages — with
a recorded falsification, the mandatory acceptable outcome).

## D16 — cross-model review of the spec documents before Gate B

**Date:** 2026-09-01 · **Decided by:** chair (2026-09-01 retro, item
5 — adopting the moderator's pushback against his own same-session
D12–D14 batch ratification) · **Status:** final

Before the Gate B entry is drafted, the ratified v3 spec documents
(requirements.md, design.md, tasks.md) receive a **cross-model
second-opinion review** (`/cross-review` — a different model than
the authoring one; advisory, board-recorded). Rationale: author,
recommender, and ratifier were one mind on one afternoon — the
closed-review-loop weakness the `q-project-critical-review-001`
round table named. The review is advisory; findings are triaged by
the chair and any resulting amendments get their own entries. D12–
D14 stand — this hedges them rather than reopening them.

**Binds:** Gate B sequencing — no Gate B entry before the
cross-review's findings are triaged.

## D17 — cross-review executed; all six findings ruled REAL; amendments applied

**Date:** 2026-09-01 · **Decided by:** chair (triage of the D16
cross-review; seat: Codex; board thread
`review-tmp-cross-review-v3-spec-20260901-1723`; receipts row in
`../cross-review/receipts.md`, disposition `real`) · **Status:**
final

All three spec documents were sent in full (33,238 chars, nothing
omitted). Six findings, all ruled real; amendments applied in this
entry's commit:

1. **DC2 objective corrected** (design): a controller redeems at
   most one seat, so k* maximizes `P(≥1 win|k)·V − E[(wins−1)⁺|k]·d`
   — the original form valued every win at V and biased k* upward.
2. **W1.3 ledger invariant completed** (tasks): stakes in = loser
   refunds + excess-win forfeits + redeemed-winner stakes, with the
   redeemed stake returned at redemption (the deposit is a bond).
3. **Verification floors named per metric** (design, W3.2):
   aggregate-drain arithmetic bounds total drain only; per-identity
   wait bars take queueing-derived floors at Gate B.
4. **DC6 ladder-cap rule registered** (design): if 8× knee exceeds
   the ladder cap, grade at the highest available multiple and
   record the shortfall — binds future anchor runs, not the D15
   grading (knee = 2, unaffected).
5. **Knee detection registered** (design): argmax of median
   steady-state throughput — the harness's computed rule, now on
   paper.
6. **W5.5 acceptance aligned with R4** (tasks): whole-run inventory,
   fairness, and retry amplification at every grid point.

The D16 hedge is discharged: findings triaged, amendments entered.
Meta-note for the record: the reviewing seat independently surfaced
the same failure class the same-day retro named (registered formulas
not computed against their own semantics) — the hedge earned its
place on its first use.

**Binds:** DC2/DC6 as amended; W1.3/W3.2/W5.5 acceptance as amended.
The Gate B path is now open.

## D18 — W0 regression anchor complete

**Date:** 2026-09-01 · **Decided by:** moderator execution under the
approved ladder; result entry · **Status:** final

W0.1: the full v1+v2 suite passes on the v3 tree, untouched — 147
tests, including the v2 golden-snapshot anchor. W0.2: the designated
v2 arm (M2, p = 0.1, fitted, 20 seeds) reproduces **bit-identically**
against the archived v2 record under the exact tolerance (v2 D16,
carried by R1). Graded report: `reports/w0-regression-2026-09-01.md`.
Environment drift found and repaired exactly (venv missing the
pinned pytest; reinstalled 9.1.1) — the starter-queued CI workflow
is the mechanical fix for this class.

**Binds:** W0 exit — W1 (priced-entry machinery) may begin.

## D19 — W1 priced-entry machinery complete

**Date:** 2026-09-01 · **Decided by:** moderator execution under the
approved ladder; result entry · **Status:** final

W1.1–W1.4 landed as `strategies/mitigation.py` (three policies over
`PricedLotteryPool`), the `a3` workload branch (DC4 deadline profile
+ uniform variant), and `runner_v3.py`. Acceptance held: policy=None
is **bit-identical** to the v2 M2 arm (log, metrics, intents — W1.1);
verification overload degrades to clean `verify-missed` with zero
lost intents and derivable per-identity wait (W1.2); the
D17-corrected k* rule is monotone with the d = 0 cell refused in
favour of pass-through, and the forfeiture ledger balances —
including refunds to identities whose client went inactive before
the draw: the bond follows the stake, not the session (W1.3); the
deadline profile concentrates ≥ 55% of registrations in the final
decile where the uniform variant shows ~10%, generation is
deterministic, and the `ineligible` stream works end-to-end (W1.4).
Full suite: 155 tests green; existing v1/v2 physics untouched.

Two implementation constants flagged for chair ratification at the
W2 gate (D1 discipline — recorded, not silently adopted):
1. a3 patient-abuser registration timing = uniform over W;
2. the deposit refund-at-draw rule for inactive-client stakes
   (adopted above as the D17-consistent reading).

**Binds:** W1 exit — W2 (arm assembly + abuse-pricing statements)
may begin.

## D20 — W2 gate: statements ratified; DC3 gains the d = 15 bracket point

**Date:** 2026-09-01 · **Decided by:** chair (after moderated
discussion; recommendation adopted) · **Status:** final

1. **Abuse-pricing statements ratified** as drafted in design.md
   §A1–A3 — on record per R2 before any evaluated run.
2. **a3 abuser registration timing ratified**: uniform over W. The
   draw is timing-blind, so the constant shapes registration-surface
   load only; the deadline stress is carried by the DC4 human cohort.
3. **Inactive-client stake refunds ratified**: the bond follows the
   stake, not the session (D17-consistent; the alternative punishes
   patience limits — regressive per Honest framing).
4. **DC3 amended: d grid = {0.1, 0.5, 2, 15}.** Computing the
   D17-corrected DC2 rule against the operating odds
   (p_win ≈ 200/2800 ≈ 0.071) shows forfeiture-only pricing cannot
   deter at the original grid: the marginal 5th identity pays for
   itself until d ≈ 3×V and the marginal 2nd until d ≈ 13×V, so
   k* = m across {0.1, 0.5, 2} — a foregone negative under R7's
   equal-effort clause if left unstated. **Pre-registered
   accordingly:** on {0.1, 0.5, 2} the deposit arm is EXPECTED to
   show zero abuse deterrence ("forfeiture-only deposits cannot
   deter at low win probability" is the hypothesis, and confirming
   it is a finding); d = 15 brackets the computed threshold and is
   expected to collapse k* to 1. A2 cells grow 12 → 16 (~80 more
   runs; budget note updated).

**Binds:** DC3 as amended; the A2 grading frame; W2 may proceed.

## D21 — W2 arms assembled; ladder advances to W3

**Date:** 2026-09-01 · **Decided by:** moderator execution under the
approved ladder; result entry · **Status:** final

All three mitigation arms run as labelled smoke diagnostics per
variant (never cited as results). Acceptance held: A1 streams present
across fitted/plateau/cliff (W2.1); the d-grid is monotone with the
D20 pre-registration confirmed mechanically — k* = m at d = 0.1 and
k* = 1 at the d = 15 bracket, and in-run stake counts match k* per
controller exactly (W2.2); the a3 camping-buys-nothing leak
diagnostic passes over 12 aggregated seeds (camp win rate within
[0.5, 1.6]× the registered field's — the draw is timing-blind, W2.3).
Bonus guard: the DC2 public-constants pool expectation matches the
generated identity count exactly, so the abuser's odds cannot
silently drift from the population. Full suite: 161 green.

**Binds:** W2 exit — W3 (honest-cost metrics, floor document,
multiplicity inventory, bar-cell coverage table) may begin; Gate B
follows W3.

## D22 — W3 complete: the Gate B packet exists

**Date:** 2026-09-01 · **Decided by:** moderator execution under the
approved ladder; result entry · **Status:** final

W3.1: honest-cost readout implemented (`measure/metrics_v3.py`) —
both clocks plus each arm's actual price (verification wait,
verify-missed, stake exposure, registration burden, ineligible),
per cohort, never only aggregate; hand-computed synthetic-log test
green. W3.2: floor document generated from model constants
(`tools/v3_floors.py` → `floors.md`) with the D4.2 enumeration per
family, per-metric naming per D17.3, and the amended
max(burst, winner-drain) rule applied — winner drain (14.195 ms)
dominates the burst floor at c_push ≤ 0.5, exactly the regime the
D18.2 amendment exists for. W3.3: multiplicity inventory — **47
primary-metric comparisons** across six families; Holm within family
proposed. W3.4: bar-cell coverage table — six proposed bars
(B1–B6), zero uncovered, mapped to the 63-cell plan. Full suite:
162 green.

**Binds:** W3 exit. Everything Gate B needs exists; Gate B (a chair
decision, not a task) is next: guard values, bar constants, and the
multiplicity policy register by chair entry over exactly this
packet.
