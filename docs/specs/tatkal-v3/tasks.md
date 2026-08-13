# tatkal-v3 — tasks

**Status:** draft (2026-08-13) — awaiting chair sign-off. No task
starts and no run is evaluated until this ladder is approved by
decision entry.

**Basis:** requirements.md (ratified, D7), design.md (approved, D8),
decisions.md D1–D8. The v2 population carries verbatim (D3), so v2's
archived cells are directly reusable as baselines and anchors.

Tasks are gated: a phase's exit criteria must hold before the next
phase starts. **Gate C is a chair decision, not a task** — it stands
between implementation and every evaluated run.

Sizes: S (≤ half day), M (~1 day), L (multi-day). Every task names its
requirement trace and its acceptance check.

**Phase IDs use the W prefix** (not V) so v3 artifacts never collide
with the v2 ladder's archived V-phases or its `tools/v5_*`–`v7_*`
modules.

---

## Cell registry

Every evaluated cell has an ID. The coverage table below maps bars to
these IDs; nothing may be run that is not registered here, and nothing
may be graded that no cell evaluates.

| ID pattern | family | parameter cells | × variants | runs |
|---|---|---|---|---|
| `MV-{c_verify}-{p}` | M2v verification-cost | c_verify {½,1,2} × p {0,.1,.2,.4} = 12 | 36 | 720 |
| `MR-{r_reg}-{p}` | M2r registration-bound | r_reg {.5,.8,.95} × p {0,.1,.2,.4} = 12 | 36 | 720 |
| `CB-{arm}-{c_push}` | costed bursts (center cells, D8.4: M1 at r_reg = 0.8, M2 at p = 0.2) | {M1, M2} × c_push {¼,½,1,2} = 8 | 24 | 480 |
| `RT-{p_retry}` | M3 retry sweep | p_retry {.3,.7,1.0} = 3 | 9 | 180 |
| **total** | | **35** | **105** | **2,100** |

**Archived cells** (v2 data, re-used not re-run — D3 carry, proven by
the W0 anchors). These are planned cells for D4.1 purposes; they are
satisfied by archive rather than by a new run, and every use is
labelled as archive-sourced in the report:

| ID | source | serves as |
|---|---|---|
| `A-M2-{p}`, p ∈ {0,.1,.2,.4} | v2 M2 cells | M2v/M2r c_verify=0 comparators; the p-matched mitigation baselines |
| `A-M1-{r_reg}`, r_reg ∈ {.5,.8,.95} | v2 M1 cells | costed-burst c_push = 0 anchors (M1 arm) |
| `A-M3` | v2 M3 cell | the p_retry = 0 anchor |
| `A-R2`, `A-R4` | v2 rung 2 / rung 4 | engineering context columns |

---

## W0 — anchors (R1)

| ID | Task | Size | Trace | Acceptance |
|---|---|---|---|---|
| W0.1 | v1 + v2 suites green on the v3 tree, untouched | S | R1 | all 147 existing tests pass unmodified |
| W0.2 | Re-register the reproduction tolerance for v3 by decision entry (chair); tolerance is `exact` per design §Anchors | S | R1, D8 | tolerance entry exists and is cited; no run precedes it |
| W0.3 | **v2-continuity anchor:** M2v at c_verify = 0 reproduces `A-M2-{p}` bit-identically at every p | M | R1, design §Anchors | 4 cells bit-identical to archive; any drift blocks W1 |
| W0.4 | **M3 anchor:** p_retry = 0 reproduces `A-M3` bit-identically | S | R4 | bit-identical; drift blocks W6 |

**Exit:** the D3 population carry is *proven*, not asserted — v2's
archives are legitimate v3 comparators. Without W0.3/W0.4 every
archive-sourced row in the coverage table is unfounded.

## W1 — mechanism code (the only new simulator code)

| ID | Task | Size | Trace | Acceptance |
|---|---|---|---|---|
| W1.1 | `VerifyingLotteryPool` (M2v): one verification work item per identity at first pool entry, on the shared pool at `c_verify × status_cost_factor` | M | R2.1, D8.1 | one item per identity per run — a re-entering identity submits none (D8.1 rider test, exercised under p_retry > 0) |
| W1.2 | Verify-by-draw semantics: the draw runs over identities verified by the draw instant ∩ still active; later completions fall to post-draw fast-fail | M | R2.1, D6.3 | planted-timing test: verification completing at draw−ε enters, at draw+ε does not |
| W1.3 | Verification log stream `("verify_start"/"verify_done", t, identity)`, reported as its own load stream | S | R2.1, D6.3 | stream is separable from booking load in the report; saturation visible |
| W1.4 | `RegistrationBoundLotteryPool` (M2r): M1's registration machinery over W_b = 300 s atop M2's pool | M | R2.3, D6.4 | registration counts match r_reg exactly; abusers pre-register all m = 5 identities, costed |
| W1.5 | M2r reject-at-entry: unregistered entries get an edge MECH_REJECT | S | R2.3, D8.2 | walk-up receives a definitive reject in edge-latency, not at draw; no silent draw-time exclusion path exists |

**Exit:** both identity-pricing arms run as smoke tests (labelled
diagnostic, never cited). W0.3 still passes — the new code did not
disturb the c_verify = 0 path.

## W2 — deposit accounting module (no mechanism code)

| ID | Task | Size | Trace | Acceptance |
|---|---|---|---|---|
| W2.1 | Per-controller win distribution K tallied by deterministic re-run of the fitted M2 cells (V7 pattern; archives hold aggregates only) | M | R2.2, D8.3 | K distribution reproduces archived aggregate win counts exactly |
| W2.2 | d\*(p) solver: `E[net] = P(≥1 win)·(1 − price_effect) − E[max(0, K−1)]·d`, solved for zero | S | R2.2, D6.4 | hand-checked against a synthetic K; d\* per prevalence cell |
| W2.3 | Honest-framing statement: deposit friction named qualitatively; out-of-model exclusions (the unbanked) named, never quantified | S | R2.2, D6.2 | statement present; no number attached to an out-of-model exclusion |

**Exit:** the deposit arm is complete before any run — it consumes
archives and adds no cells. A large d\* is pre-registered (D8.3) as an
acceptable finding.

## W3 — metrics: honest-user cost per arm (D6.2)

| ID | Task | Size | Trace | Acceptance |
|---|---|---|---|---|
| W3.1 | M2v honest-user cost: added entry latency + draw-miss exclusion rate among honest identities | M | R2.1, D6.2 | hand-computed values on a synthetic log match |
| W3.2 | M2r honest-user cost: walk-up rejection count/rate per r_reg cell | S | R2.3, D6.2 | rate is a function of uptake, reported per cell |
| W3.3 | Fairness metric carried: controller-level draw-share advantage, unchanged from v2 | S | R2, D5 | v2 fairness values reproduce on `A-M2-{p}` |
| W3.4 | M3 retry metrics: seats sold, whole-run + per-tranche F, retry amplification per tranche, both clocks | M | R4 | per-tranche readouts present; congestion indicators computed |

**Exit:** every arm has BOTH a fairness metric and an honest-user cost
metric implemented — D6.2 makes this binding *before* guards, so a
missing cost metric blocks Gate C.

## W4 — floors, comparison inventory, coverage table

| ID | Task | Size | Trace | Acceptance |
|---|---|---|---|---|
| W4.1 | Floor derivation per the amended rule — max(burst drain, winner-redemption drain) — with the **D4.2 enumeration** for every arm | M | D1, D4.2 | each floor lists components INCLUDED and components OMITTED WITH CAUSE; an unenumerated floor fails review |
| W4.2 | **Late-verification drain: include or justify.** M2v's post-draw fast-fail path carries verification items that complete after the draw — a post-event drain component that no other arm has | S | D4.2, W1.2 | either the component is in the M2v floor, or the omission is justified in writing; silence is a D4.2 failure |
| W4.3 | Comparison inventory: enumerate every planned paired comparison across W5–W6, by family | S | R7 | the closed list Gate C needs, with counts per family |
| W4.4 | Coverage table below re-checked against implemented cells | S | D4.1 | every bar slot resolves to ≥ 1 cell ID that W6 actually plans to run |

**Exit:** everything Gate C must rule on exists — floors with
enumerations, the comparison inventory, and a coverage table with no
unmapped bar.

### W4.2 in full — why it has its own task

D18.2 amended v2's floor rule because a drain component (winner
redemption) had been omitted silently. D4.2 exists so that cannot
recur. M2v introduces the first genuinely new post-event drain
component since: verification work items whose completion lands after
the draw instant. Verify-by-draw (D6.3) means those identities are
*excluded* from the draw, but their work items still occupy the shared
pool during the post-event window, alongside the notification burst.

Whether that component belongs in the M2v floor is a derivation
question, not a foregone conclusion — it may be dominated by burst
drain at every grid point, in which case the max() rule absorbs it.
The task is to **state which**, with the arithmetic. An M2v floor that
does not mention late verification is exactly the v2 miss repeated in
a new arm.

---

## COVERAGE TABLE (D4.1) — every bar maps to a cell

Bar *values* are UNSET here; they are registered at Gate C. This table
registers the bar **slots** and their evaluating cells. **D4.1 check:
Gate C may register a bar only if it appears in this table.** A bar
with no cell fails gate approval mechanically — the check is a lookup,
not a judgment.

### Latency / floor-relative bars

| # | bar slot | clock | evaluating cells | new or archive |
|---|---|---|---|---|
| B1 | M2v post-event resolution p99 vs floor, per c_verify point | post-event | `MV-½-*`, `MV-1-*`, `MV-2-*` (3 slots) | new |
| B2 | M2v loser absolute TTDA vs deliberate wait + floor | absolute | same as B1 | new |
| B3 | M2v c_verify = 0 continuity | both | `A-M2-{p}` | archive (W0.3) |
| B4 | M2r post-event resolution p99 vs floor, per r_reg point | post-event | `MR-.5-*`, `MR-.8-*`, `MR-.95-*` (3 slots) | new |
| B5 | M2r walk-up reject latency (edge-fast, per D8.2) | absolute | `MR-*-*` | new |
| B6 | costed-burst post-event p99 vs max(burst, redemption) floor, **per c_push grid point per arm** | post-event | `CB-M1-{¼,½,1,2}`, `CB-M2-{¼,½,1,2}` (8 slots) | new |
| B7 | costed-burst c_push = 0 anchors | post-event | `A-M1-{r_reg}`, `A-M2-.2` (2 slots) | archive |
| B8 | M3 whole-run vs H + last-tranche drain floor, per p_retry | whole-run | `RT-.3`, `RT-.7`, `RT-1.0` (3 slots) | new |
| B9 | M3 p_retry = 0 anchor | whole-run | `A-M3` | archive (W0.4) |

**B6 is the v2 miss, closed.** v2 registered per-grid-point burst bars
and ran only the zero cell. Here all 8 non-zero grid points have
cells, and the 2 zero points resolve to archive. D4.1 came from this
exact failure.

### Fairness guards

| # | guard slot | evaluating cells |
|---|---|---|
| B10 | zero-abuse advantage ≤ 1.05 (P1-consistent), per mitigation arm | `MV-*-0`, `MR-*-0` |
| B11 | identity-split controller advantage ≤ m (= 5) at p > 0, per arm | `MV-*-{.1,.2,.4}`, `MR-*-{.1,.2,.4}` |
| B12 | costing does not change who wins (registered prediction: fairness is costing-independent) | `CB-*-*` vs `A-M1-*` / `A-M2-.2` |
| B13 | M3 fairness regression vs the p_retry = 0 comparator | `RT-*` vs `A-M3` |

### Honest-user cost guards (D6.2 — binding, values UNSET)

| # | guard slot | evaluating cells |
|---|---|---|
| B14 | M2v honest draw-miss exclusion rate, per c_verify point | `MV-*-*` |
| B15 | M2v added entry latency, per c_verify point | `MV-*-*` |
| B16 | M2r walk-up exclusion rate, per r_reg point | `MR-*-*` |

### Report-only (findings, never pass/fail)

| # | item | evaluating cells |
|---|---|---|
| B17 | M2v verification load stream + its saturation point | `MV-*-*` |
| B18 | deposit d\*(p) per prevalence | archives via W2 (no cells) |
| B19 | M3 seats sold / inventory recovery | `RT-*` |
| B20 | M2 ghost_sales (v2-carried mechanism finding) | all M2-derived cells |

**Unmapped-bar check:** B1–B20 all resolve to at least one cell ID.

**Unused-cell check:** all 35 parameter cells in the registry appear
in at least one row above (B1 covers the 12 `MV-*`, B4 the 12 `MR-*`,
B6 the 8 `CB-*`, B8 the 3 `RT-*`) — so no cell is run that no bar or
finding consumes.

**One deliberate exception:** `A-R2` and `A-R4` (v2 rungs 2 and 4)
appear in no bar row. They are **report-context columns only**,
carrying v2's RESULTS format so mitigation numbers can be read against
the engineering baselines. They evaluate nothing and are graded
against nothing. Stated here rather than left as a silent gap in the
check — an archive column nobody registered is how a table like this
starts drifting from what the runs actually do.

---

## GATE C — chair decision (blocks all evaluated runs)

Register by decision entry, informed by W4's outputs:

- **every bar value** for B1–B16, with its floor distance stated per
  clock and variant (D3 — a bar without a floor statement cannot be
  registered), drawn **only** from the coverage table above (D4.1);
- **honest-user cost guard values** (B14–B16) — currently UNSET, and
  D6.2 makes them non-optional for every mitigation arm;
- **multiplicity policy**: the W4.3 comparison count and the
  correction procedure (v2 precedent: Holm within family — carried as
  the default candidate, confirmed or amended here);
- **confirmation of the W4.2 late-verification ruling** — in the M2v
  floor, or omitted with stated cause;
- confirmation that the W0.2 reproduction tolerance and the
  report-only set (B17–B20) are as intended.

No evaluated run starts before this entry exists. W1's smoke runs are
never promoted to results.

## W5 — archive verification (no new baselines needed)

| ID | Task | Size | Trace | Acceptance |
|---|---|---|---|---|
| W5.1 | Confirm every archive-sourced cell in the coverage table loads, at 20 seeds × 3 variants, paired by seed with the new cells | S | R5, D3 | seed pairing verified cell-by-cell; any gap converts that row to a new run and re-enters Gate C |

**Exit:** v3 needs no baseline re-run — v2's D3-carried population
makes `A-*` cells directly comparable, and W0.3/W0.4 proved it.

## W6 — evaluated runs

| ID | Task | Size | Trace | Acceptance |
|---|---|---|---|---|
| W6.1 | M2v: 12 parameter cells × 3 variants × 20 seeds (720 runs) | L | R2.1 | all cells at full seed count; verification load stream archived per cell |
| W6.2 | M2r: 12 × 3 × 20 (720 runs) — **full abuse grid per D8.5** | L | R2.3, D8.5 | all 4 prevalence points present; a 2-point M2r grid is a D8.5 violation |
| W6.3 | Costed bursts: 8 × 3 × 20 (480 runs) | M | R3 | every c_push grid point has its cell (closes B6) |
| W6.4 | M3 retry: 3 × 3 × 20 (180 runs) | M | R4 | per-tranche readouts; congestion regime named if entered |

**Exit:** 105 cells / 2,100 runs at full seed count; no cell below 20
seeds exists anywhere (D3's universal floor).

## W7 — grading and write-up

| ID | Task | Size | Trace | Acceptance |
|---|---|---|---|---|
| W7.1 | Grade every Gate-C bar on both clocks; misses reported, never adjusted | L | R7 | RESULTS.md with per-clause grading of the expected-result hypothesis |
| W7.2 | The cross-arm comparison — M2v vs M2r at all four prevalence points (the D5 finding) | M | D5, D8.5 | comparison stated at every p; this is why D8.5 restored the grid |
| W7.3 | Honest framing: who each mechanism advantages and disadvantages; out-of-model exclusions named, never quantified; the D8.2 registration-oracle note; policy-authority disclaimer | S | Honest framing, D8.2 | present and specific per arm |
| W7.4 | v4 candidates listed; v3 concluded by decision entry; ledger sealed | S | — | conclusion entry exists |

**Exit:** v3 concluded.

---

## Standing rules (apply to every phase)

- Determinism and inventory-invariant tests run in CI on every commit.
- No D3/D6/D8 registered constant is touched outside a decision entry.
- Every report lists enabled fidelity toggles and both clocks.
- v1 absolute numbers appear in no v3 comparison (v2 D12 carries).
- Archive-sourced cells are labelled as such wherever they appear.
- Smoke/diagnostic runs are labelled and never cited as results.
- Bars come from the coverage table or they do not exist (D4.1).
- Floors enumerate inclusions and justified omissions (D4.2).
- Drift from this ladder gets named in-session before it happens, not
  discovered after.
