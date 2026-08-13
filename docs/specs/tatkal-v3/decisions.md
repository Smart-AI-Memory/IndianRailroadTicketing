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

## D6 — requirements judgment calls ruled; grids registered

**Date:** 2026-08-12 · **Decided by:** chair (requirements
ratification pass RQ1–RQ4) · **Status:** final

1. **Deposit arm is accounting-only (RQ1).** Under the D3 fixed
   repertoire it reports abuser expected net utility and the d*
   threshold per prevalence, computed analytically from the registered
   utility model — seat value normalized to 1, losers refunded. The
   behavioural budget variant is ruled out for v3 (no D3 amendment).
2. **Honest-user cost metrics are binding (RQ2).** Every mitigation
   arm registers a fairness metric AND an honest-user cost metric
   before its guards; out-of-model exclusions are named as
   unmeasurable, never quantified.
3. **Verify-by-draw (RQ3).** Only identities whose verification
   completes by the draw enter it; later verifications fall to
   post-draw fast-fail; verification is measured as its own load
   stream; honest draw-misses count in the exclusion metric.
4. **Constants registered (RQ4):** c_verify ∈ {0, ½, 1, 2} × status
   check (zero cell = unmitigated M2 continuity anchor); W_b = 300 s
   (carrying v2's W); p_retry ∈ {0, 0.3, 0.7, 1.0} (zero cell = v2 M3
   anchor); deposit utility model as in (1). Per D1 discipline none
   may be adjusted after runs; misses are reported.

**Binds:** requirements.md R2/R4; every dependent cell.

## D7 — v3 requirements ratified in full

**Date:** 2026-08-12 · **Decided by:** chair · **Status:** final

requirements.md, as drafted from D1–D5 and amended by the D6 rulings,
is **ratified in full**. R1–R8, the deferral list, the safety boundary,
honest framing, and the expected-result hypothesis are binding. The
design phase opens; the design document owes the chair: the M2r entry
semantics, the deposit forfeiture accounting, the verification work
model, and the costed-burst cell list checked against D4.1.

**Binds:** requirements.md (status: ratified); design-phase sequencing.

## D8 — the five open design choices ruled; M2r abuse grid restored to full

**Date:** 2026-08-13 · **Decided by:** chair (design review pass over
`design.md` §"Design choices open for chair review") · **Status:** final

All five PROPOSED design choices are ruled. Four are approved as
drafted, two of them with riders; the fifth is rejected in favour of
the ratified requirement.

1. **M2v verification work model — approved.** One verification work
   item per identity at its first pool entry, not per poll; per-poll
   re-verification models a stateless verifier and is not what real
   verification does. **Rider:** verification is cached *per identity*,
   not per entry — an identity re-entering the pool under the R4 retry
   sweep does NOT re-verify. This is stated because v3 sweeps
   `p_retry` and the interaction would otherwise be undefined.
2. **M2r entry semantics — approved.** Unregistered entries get an
   edge MECH_REJECT (v1 reject semantics) rather than silent
   exclusion at the draw; walk-ups learn their fate in milliseconds
   instead of waiting Q for a draw they were never in. **Rider:**
   reject-at-entry is also a fast oracle for registration state. Under
   the D3 fixed repertoire no simulated abuser exploits it, so there
   is no in-model effect — this is recorded as an out-of-model
   honest-framing item, not quantified.
3. **Deposit forfeiture accounting — approved.** Given D6.4's
   losers-refunded model the deposit prices multi-win forfeiture, and
   d\* is computed from per-controller win distributions by
   deterministic re-run (V7 pattern). A large d\* is pre-registered as
   an acceptable and likely finding: the refund-losers design is weak
   against low-multiplicity abuse, and reporting that is the point.
4. **Costed-burst cell list — approved, confirmatory.** Center cells
   only (M1 at r_reg = 0.8, M2 at p = 0.2 × the c_push grid). Noted:
   this does not amend anything — ratified R3 already reads "M1
   (center uptake) and M2 (center abuse)". The ruling confirms the
   design matches the requirement.
5. **M2r abuse grid — REJECTED as drafted; the full grid stands.**
   M2r runs p ∈ {0, 0.1, 0.2, 0.4}, not {0, 0.2}. Ratified R2 binds
   all three arms to the same abuse grid; narrowing one arm is an
   amendment to a ratified requirement, not a design choice, and no
   amendment is made. Substantively: the deposit arm never runs, so
   M2v vs M2r is the live head-to-head, and D5 makes the comparison
   across arms the finding — two common prevalence points is too thin
   a basis for it. Cost accepted: M2r goes 6 → 12 parameter cells
   (18 → 36 counted cells), 360 → 720 runs; family totals 87 → 105
   cells and 1,740 → 2,100 evaluated runs.

**Binds:** design.md (status: approved); the cell budget; tasks.md's
D4.1 coverage table.

## Open questions (no decision yet)

*(new questions get logged here)*
