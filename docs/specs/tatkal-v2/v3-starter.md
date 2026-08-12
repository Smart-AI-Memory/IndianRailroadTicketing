# tatkal v3 — starter

**Status:** RATIFIED (2026-08-12) — the §5 pass is complete; rulings
recorded as D1–D5 in
[`../tatkal-v3/decisions.md`](../tatkal-v3/decisions.md), which is the
binding record. All five rulings followed the draft recommendations:
scope = mitigation + costed bursts + M3 retry sensitivity (D2), fresh
ledger (D1), D13 population carried verbatim (D3), both new process
rules binding (D4), all three mitigation arms in (D5).

This file was drafted from the v2 graded record (RESULTS.md,
chair-approved; ledger sealed at D19) and served as the ratification
agenda.

---

## 1. What v2 established (carry-in facts, final per D19)

- **Allocation mechanisms deliver bot parity; engineering does not.**
  M1 (every uptake) and M2 (zero abuse) cut controller-level bot
  advantage from ~3.9× to ~1.0×; all D7 comparisons
  Holm-distinguishable against both engineering baselines.
- **P1 confirmed:** pooling collapses mimic bots and honest humans
  into one class by construction.
- **Unmitigated lotteries pay identity abusers ≈ m** at low
  prevalence (4.46 at p = 0.1 for m = 5), under the
  no-super-linear guard, self-diluting at scale — but honest-user
  fairness still degrades monotonically with prevalence. Mitigation,
  not prevalence, is the open lever.
- **The waiting room does not survive costing:** break-even ≤ 0.25× a
  status check; at free push not distinguishable from fast-fail under
  the v2 population.
- **M3 double negative (contingent):** fairness guard breached and
  inventory starved (125/200) — measured at p_retry = 0, where
  rejected demand leaves instead of re-entering. The negative's
  sensitivity to the retry model is unmeasured.
- **Un-run grid:** M1/M2 notification bursts were evaluated only at
  c_push = 0; the D14.2 shared grid contemplated costed bursts for
  them (RESULTS §7 limitation).
- **Process lesson (D18.2):** the c = 0 post-event floor omitted the
  winner-redemption drain — floors must enumerate every drain
  component, and the amended rule max(burst, winner-drain) is already
  binding prospectively.

## 2. Scope candidates (ranked; chair selects in §5-Q1)

1. **Identity mitigation for M2** — the mechanism-design core of v3.
   v2 proved the lottery works and quantified what abuse costs it; the
   open question is which mitigation reclaims parity: identity
   verification (a costed delay/work item per identity), an
   entry deposit (abuse becomes economically self-defeating), or
   registration-bound identities (M1×M2 hybrid: only pre-registered
   identities may enter the draw). Pure simulation on existing infra.
2. **Costed M1/M2 notification bursts** — complete v2's costing story
   by running the allocation arms across the D14.2 grid (the machinery
   already exists; the cells were simply not in V6's list). Closes the
   known coverage gap and exercises the amended floor rule.
3. **M3 retry-model sensitivity** — sweep p_retry_after_reject: does
   paced drain recover (inventory and fairness) when rejected demand
   re-enters? v2's honest negative deserves its sensitivity analysis
   before v3 writes M3 off.
4. **Two-phase inventory / seat-hold** (standing deferral) — would fix
   M2's ghost race and enable redemption windows; heavier modelling.
5. Standing v1/v2 deferrals: adversarial co-evolution, distributed
   load, payment/auth/CAPTCHA, anything touching IRCTC.

## 3. Pre-registration constraints (v2 carry-forwards + new lessons)

- **All v1/v2 conventions carry:** chair model, append-only ledger,
  floors before bars (with the D18.2 amended floor rule), per-mechanism
  fairness metrics before guards, paired per-seed stats, 20-seed
  universal floor, three-variant bracketing, two-clock reporting,
  multiplicity policy registered up front, misses reported never
  adjusted, IRCTC safety boundary verbatim.
- **NEW — bar-cell coverage check:** every registered bar must map to
  at least one planned cell in tasks.md before Gate approval. v2
  registered per-grid-point bars for M1/M2 bursts and then ran only
  the zero cell — the mismatch was caught at grading, not planning.
- **NEW — floor completeness rule:** a floor derivation must enumerate
  the drain components it includes and state why omitted ones are
  irrelevant (D18.2 origin).

## 4. Standing conventions

Chair model, pre-registration discipline, honest framing, and the
safety boundary carry verbatim from the v2 ledger's D1. Simulated
mechanisms carry no authority over real-system policy; v3's
mitigation results are evidence for study, not policy recommendations.

## 5. Open decisions for the ratification pass

- **Q1 — Scope:** which of §2's candidates are in v3? (Draft
  recommendation: 1 + 2 + 3 — all pure simulation on existing infra,
  each directly closes an edge v2 left open; two-phase inventory
  stays deferred.)
- **Q2 — Ledger:** new `docs/specs/tatkal-v3/` with numbering
  restarted at D1, D1 ratifying carried conventions (v2 precedent)?
- **Q3 — Population:** carry the v2 registered population (D13)
  verbatim — same cohorts, mix, m = 5, abuse grid, 20 seeds — with
  additions only by entry? (Mitigation is modelled mechanism-side;
  the bot repertoire stays fixed, keeping co-evolution deferred.)
- **Q4 — New process rules:** ratify the bar-cell coverage check and
  floor completeness rule (§3) as binding for v3's gates?
- **Q5 — Mitigation design space:** which M2 mitigations enter
  requirements — verification-cost, deposit, registration-bound — all
  three as arms, or a chair-picked subset? (Draft recommendation: all
  three; they occupy different corners — work-priced, money-priced,
  and enrollment-priced identity.)

---

*Drafted from: RESULTS.md (v2, chair-approved), decisions.md D1–D19,
v2 retro lessons D18.*
