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
- **OQ4 (from D10):** which second calibration anchor implements
  D8's intent — a second engine on the same machine (MySQL/MariaDB
  via the existing R2 harness; tests engine-independence), a second
  machine on the same engine (tests hardware transfer), or both?
  Requires a chair ruling on the infra install either way.
